#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import psycopg2
import json
from datetime import datetime, timedelta
import os, stat
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
app.secret_key = os.urandom(24) # Секретный ключ для сессий

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB', 'developer_control'),
        user=os.getenv('POSTGRES_USER', 'control_admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'secure_password_here')
    )

# Декоратор для проверки аутентификации
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__ # Сохраняем имя функции для Flask
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM dev_control.users WHERE username = %s AND is_active = TRUE", (username,))
            user_data = cur.fetchone()
            
            if user_data and pbkdf2_sha256.verify(password, user_data[0]):
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard(): # Removed @login_required for testing
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get general statistics
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM dev_control.developers WHERE status = 'active') as active_developers,
                    (SELECT COUNT(*) FROM dev_control.file_events WHERE DATE(detected_at) = CURRENT_DATE) as events_today,
                    (SELECT COUNT(*) FROM dev_control.violations WHERE DATE(created_at) = CURRENT_DATE) as violations_today,
                    (SELECT COUNT(*) FROM dev_control.blocked_files WHERE unblocked_at IS NULL) as blocked_files
            """)
            
            stats_data = cur.fetchone()
            
            stats = {
                'active_developers': stats_data[0] if stats_data[0] else 0,
                'events_today': stats_data[1] if stats_data[1] else 0,
                'violations_found': stats_data[2] if stats_data[2] else 0,
                'blocked_files': stats_data[3] if stats_data[3] else 0
            }
            
            conn.close()
            return render_template('dashboard.html', stats=stats, recent_events=[])
    except Exception as e:
        # If database is not available, return default values
        stats = {
            'active_developers': 0,
            'events_today': 0,
            'violations_found': 0,
            'blocked_files': 0
        }
        return render_template('dashboard.html', stats=stats, recent_events=[])

@app.route('/api/stats')
def get_stats(): 
    """Получить общую статистику"""
    conn = get_db_connection()
    
    with conn.cursor() as cur:
        # Общая статистика
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM dev_control.developers WHERE status = 'active') as active_developers,
                (SELECT COUNT(*) FROM dev_control.file_events WHERE DATE(detected_at) = CURRENT_DATE) as today_events,
                (SELECT COUNT(*) FROM dev_control.violations WHERE DATE(created_at) = CURRENT_DATE) as today_violations,
                (SELECT COUNT(*) FROM dev_control.blocked_files WHERE unblocked_at IS NULL) as currently_blocked
        """)
        
        stats = cur.fetchone()
        
        return jsonify({
            'active_developers': stats[0],
            'today_events': stats[1],
            'today_violations': stats[2],
            'currently_blocked': stats[3]
        })

@app.route('/api/recent_events')
@login_required
def get_recent_events():
    """Получить последние события"""
    conn = get_db_connection()
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                fe.file_path,
                fe.event_type,
                fe.detected_at,
                d.username,
                aa.tz_compliance_score,
                aa.security_score,
                aa.is_blocked
            FROM dev_control.file_events fe
            JOIN dev_control.developers d ON fe.developer_id = d.id
            LEFT JOIN dev_control.ai_analysis aa ON fe.id = aa.file_event_id
            ORDER BY fe.detected_at DESC
            LIMIT 20
        """)
        
        events = []
        for row in cur.fetchall():
            events.append({
                'file_path': row[0],
                'event_type': row[1],
                'detected_at': row[2].isoformat(),
                'username': row[3],
                'tz_score': float(row[4]) if row[4] else None,
                'security_score': float(row[5]) if row[5] else None,
                'is_blocked': row[6] if row[6] else False
            })
        
        return jsonify(events)

@app.route('/api/violations')
@login_required
def get_violations():
    """Получить нарушения"""
    severity = request.args.get('severity', 'all')
    
    conn = get_db_connection()
    
    with conn.cursor() as cur:
        query = """
            SELECT 
                v.violation_type,
                v.severity,
                v.description,
                v.created_at,
                fe.file_path,
                d.username
            FROM dev_control.violations v
            JOIN dev_control.file_events fe ON v.file_event_id = fe.id
            JOIN dev_control.developers d ON fe.developer_id = d.id
            WHERE v.created_at >= %s
        """
        
        params = [datetime.now() - timedelta(days=7)]
        
        if severity != 'all':
            query += " AND v.severity = %s"
            params.append(severity)
            
        query += " ORDER BY v.created_at DESC LIMIT 50"
        
        violations = []
        for row in cur.fetchall():
            violations.append({
                'type': row[0],
                'severity': row[1],
                'description': row[2],
                'created_at': row[3].isoformat(),
                'file_path': row[4],
                'username': row[5]
            })
        
        return jsonify(violations)

@app.route('/api/unblock_file', methods=['POST'])
@login_required
def unblock_file():
    """Разблокировать файл"""
    data = request.get_json()
    file_path = data.get('file_path')
    
    if not file_path:
        return jsonify({'error': 'file_path required'}), 400
    
    conn = get_db_connection()
    
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE dev_control.blocked_files 
            SET unblocked_at = NOW() 
            WHERE file_path = %s AND unblocked_at IS NULL
            RETURNING id
        """, (file_path,))
        
        result = cur.fetchone()
        
        if result:
            conn.commit()
            # Восстанавливаем права на файл
            try:
                # Ensure the path is absolute for os.chmod
                abs_file_path = os.path.abspath(file_path)
                os.chmod(abs_file_path, stat.S_IREAD | stat.S_IWRITE)
            except Exception as e:
                # Log the error but don't block the unblock operation
                print(f"Error changing file permissions: {e}")
                
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'File not found or already unblocked'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
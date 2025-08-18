-- Примеры SQL-запросов для Grafana Dashboard
-- Используйте эти запросы в Grafana, подключив PostgreSQL как источник данных.

-- 1. Общее количество файловых событий по дням
SELECT
    DATE_TRUNC('day', detected_at) AS day,
    COUNT(*) AS event_count
FROM
    dev_control.file_events
GROUP BY
    1
ORDER BY
    1;

-- 2. Количество нарушений по типам за последние 7 дней
SELECT
    violation_type,
    COUNT(*) AS violation_count
FROM
    dev_control.violations
WHERE
    created_at >= NOW() - INTERVAL '7 days'
GROUP BY
    violation_type
ORDER BY
    violation_count DESC;

-- 3. Количество критичных нарушений по дням
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS critical_violation_count
FROM
    dev_control.violations
WHERE
    severity = 'critical'
GROUP BY
    1
ORDER BY
    1;

-- 4. Средний балл безопасности по дням
SELECT
    DATE_TRUNC('day', analyzed_at) AS day,
    AVG(security_score) AS avg_security_score
FROM
    dev_control.ai_analysis
GROUP BY
    1
ORDER BY
    1;

-- 5. Средний балл соответствия ТЗ по дням
SELECT
    DATE_TRUNC('day', analyzed_at) AS day,
    AVG(tz_compliance_score) AS avg_tz_compliance_score
FROM
    dev_control.ai_analysis
GROUP BY
    1
ORDER BY
    1;

-- 6. Топ-10 файлов с наибольшим количеством нарушений
SELECT
    fe.file_path,
    COUNT(v.id) AS total_violations
FROM
    dev_control.file_events fe
JOIN
    dev_control.violations v ON fe.id = v.file_event_id
GROUP BY
    fe.file_path
ORDER BY
    total_violations DESC
LIMIT 10;

-- 7. Количество заблокированных файлов по дням
SELECT
    DATE_TRUNC('day', blocked_at) AS day,
    COUNT(*) AS blocked_file_count
FROM
    dev_control.blocked_files
GROUP BY
    1
ORDER BY
    1;

-- 8. Количество нарушений по разработчикам за все время
SELECT
    d.username,
    COUNT(v.id) AS total_violations
FROM
    dev_control.developers d
JOIN
    dev_control.file_events fe ON d.id = fe.developer_id
JOIN
    dev_control.violations v ON fe.id = v.file_event_id
GROUP BY
    d.username
ORDER BY
    total_violations DESC;

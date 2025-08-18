#!/usr/bin/env python3

"""
LAZARUS HOOK - Перехватчик для создания trigger при нужных условиях
Мониторит активность и создаёт .lazarus_trigger когда нужен pulse
"""

import os
import time
import sys
from pathlib import Path

MEMORY_DIR = Path("/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/MEMORY")
TRIGGER_FILE = MEMORY_DIR / ".lazarus_trigger"
HEARTBEAT_FILE = MEMORY_DIR / ".lazarus_heartbeat"

def create_trigger():
    """Создаёт trigger файл для активации pulse"""
    TRIGGER_FILE.touch()
    print(f"⚡ Trigger created at {time.strftime('%H:%M:%S')}")

def check_heartbeat():
    """Проверяет жив ли pulse"""
    if HEARTBEAT_FILE.exists():
        with open(HEARTBEAT_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                last_beat = int(lines[-1].strip())
                if time.time() - last_beat > 30:
                    return False
        return True
    return False

if __name__ == "__main__":
    print("🔷 LAZARUS HOOK ACTIVE")
    
    # Создаём начальный trigger
    create_trigger()
    
    # Мониторим и создаём trigger каждые 60 секунд
    while True:
        time.sleep(60)
        if not check_heartbeat():
            print("❌ Pulse dead, creating emergency trigger")
            create_trigger()
        else:
            print("✅ Pulse alive")
            # Периодический trigger для поддержания
            if time.time() % 300 < 60:  # каждые 5 минут
                create_trigger()
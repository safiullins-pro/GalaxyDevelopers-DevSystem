
import os
import pandas as pd
from datetime import datetime

def get_file_stats(file_path):
    try:
        stats = os.stat(file_path)
        size_kb = stats.st_size / 1024
        creation_time = datetime.fromtimestamp(stats.st_ctime)
        return size_kb, creation_time
    except FileNotFoundError:
        return None, None

def get_category(file_path):
    if "01_AGENTS" in file_path:
        return "Агенты"
    elif "02_DATA" in file_path:
        return "Данные"
    elif "03_TEMPLATES" in file_path:
        return "Шаблоны"
    elif "04_STANDARDS" in file_path:
        return "Стандарты"
    elif "05_ROLES" in file_path:
        return "Роли"
    elif "06_PROCESSES" in file_path:
        return "Процессы"
    elif "07_DELIVERABLES" in file_path:
        return "Deliverables"
    elif "08_LOGS" in file_path:
        return "Логи"
    elif "09_JOURNALS" in file_path:
        return "Журналы"
    elif "10_REPORTS" in file_path:
        return "Отчеты"
    else:
        return "Прочее"

def analyze_quality(file_path):
    # This is a placeholder for a more sophisticated analysis
    return 5, 5, 5, 5, 5

def create_inventory_catalog():
    with open("all_files.txt", "r") as f:
        files = [line.strip() for line in f.readlines()]

    data = []
    for file in files:
        size_kb, creation_time = get_file_stats(file)
        if size_kb is not None:
            file_name = os.path.basename(file)
            extension = os.path.splitext(file_name)[1]
            category = get_category(file)
            quality = analyze_quality(file)
            data.append([file, file_name, extension, size_kb, creation_time, category] + list(quality))

    df = pd.DataFrame(data, columns=["Путь к файлу", "Имя файла", "Расширение", "Размер в КБ", "Дата создания", "Категория", "Полнота информации", "Актуальность", "Структурированность", "Соответствие формату", "Практическая применимость"])
    df.to_excel("ToDo/Phase1/P1.1/inventory_catalog.xlsx", index=False)

if __name__ == "__main__":
    create_inventory_catalog()

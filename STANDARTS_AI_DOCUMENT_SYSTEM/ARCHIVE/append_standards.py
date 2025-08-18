import csv

standards_data = [
    {"Category": "Templates & Standards", "Path": "04_STANDARDS/ISO/ISO_Анализ_качества.json", "Description": "ISO Standard: Quality Analysis"},
    {"Category": "Templates & Standards", "Path": "04_STANDARDS/ISO/ISO_Выявление_пробелов.json", "Description": "ISO Standard: Gap Identification"},
    {"Category": "Templates & Standards", "Path": "04_STANDARDS/ISO/ISO_Инвентаризация_документов.json", "Description": "ISO Standard: Document Inventory"},
    {"Category": "Templates & Standards", "Path": "04_STANDARDS/ISO/ISO_Классификация_по_категориям.json", "Description": "ISO Standard: Categorization"},
    {"Category": "Templates & Standards", "Path": "04_STANDARDS/ISO/ISO_Создание_матрицы_покрытия.json", "Description": "ISO Standard: Coverage Matrix Creation"}
]

with open('inventory_catalog.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    for row_data in standards_data:
        writer.writerow([row_data['Category'], row_data['Path'], row_data['Description']])

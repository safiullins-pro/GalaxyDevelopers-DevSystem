import os

search_paths = [
    '/Volumes/Z7S/development/GalaxyDevelopers',
    '/Volumes/Z7S/development/ALBERT_TOOLS_PLACE'
]

error_files = []
forge_files = []

for path in search_paths:
    for root, dirs, files in os.walk(path):
        for filename in files:
            try:
                # Поиск файлов, начинающихся с "Error" и с расширением .md
                if filename.startswith("Error") and filename.endswith(".md"):
                    error_files.append(os.path.join(root, filename))

                # Поиск файлов, содержащих "FORGE" (без учета регистра)
                if "forge" in filename.lower():
                    forge_files.append(os.path.join(root, filename))
            except Exception:
                continue

print("Файлы, начинающиеся с 'Error' и типом .md:")
if error_files:
    for file_path in error_files:
        print(file_path)
else:
    print("-> Файлы не найдены.")

print("\n" + "="*30 + "\n")

print("Файлы, содержащие 'FORGE' в названии:")
if forge_files:
    for file_path in forge_files:
        print(file_path)
else:
    print("-> Файлы не найдены.")

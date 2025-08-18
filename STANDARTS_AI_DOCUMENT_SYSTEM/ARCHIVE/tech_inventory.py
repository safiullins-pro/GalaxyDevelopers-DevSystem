
import os
import json

def create_tech_inventory():
    inventory = {
        "python_agents": [],
        "config_files": [],
        "automation_scripts": [],
        "docker_files": [],
        "ci_cd_configs": []
    }

    for root, dirs, files in os.walk("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem"):
        for file in files:
            file_path = os.path.join(root, file)
            if "01_AGENTS" in file_path and file.endswith(".py"):
                inventory["python_agents"].append(file_path)
            elif file.endswith(('.json', '.yaml', '.env')):
                inventory["config_files"].append(file_path)
            elif file.endswith(('.sh', '.py')) and "11_SCRIPTS" in file_path:
                inventory["automation_scripts"].append(file_path)
            elif file == "Dockerfile" or file == "docker-compose.yml":
                inventory["docker_files"].append(file_path)
            elif ".github/workflows" in file_path:
                inventory["ci_cd_configs"].append(file_path)

    with open("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/ToDo/Phase1/P1.2/tech_inventory.json", "w") as f:
        json.dump(inventory, f, indent=4)

if __name__ == "__main__":
    create_tech_inventory()

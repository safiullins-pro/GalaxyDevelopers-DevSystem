import csv
import re

def generate_process_documentation():
    # Read the process catalog
    process_catalog = {}
    with open('process_catalog.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            process_catalog[row[1]] = row[0]

    # Read the phase READMEs
    phase_processes = {}
    for i in range(1, 8):
        phase = f'P{i}'
        with open(f'06_PROCESSES/{phase}/README.md', 'r') as f:
            content = f.read()
            processes = re.findall(r'- \*\*(P\d\.\d+)\*\*: (.*)', content)
            phase_processes[phase] = processes

    # Generate the inventory catalog
    with open('inventory_catalog.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'Path', 'Description'])
        writer.writerow(['System Architecture & Documentation', '00_DOCUMENTATION', 'High-level design documents, READMEs, and architecture diagrams.'])
        writer.writerow(['Project Management & Processes', '00_PROJECT_MANAGEMENT', 'Execution plans, role definitions, process catalogs, and RACI matrices.'])
        writer.writerow(['Core Application Logic', '01_AGENTS', 'AI agents for the GALAXYDEVELOPMENT system.'])
        writer.writerow(['Data & Databases', '02_DATA', 'Raw data, processed data, database schemas (.sql), and caches.'])
        writer.writerow(['Templates & Standards', '03_TEMPLATES', 'Reusable code templates and documentation templates.'])
        writer.writerow(['Templates & Standards', '04_STANDARDS', 'Industry standards (ISO, NIST, etc.).'])
        writer.writerow(['Project Management & Processes', '05_ROLES', 'Detailed role profiles for the 38 roles in the system.'])
        for i in range(1, 39):
            writer.writerow(['Project Management & Processes', f'05_ROLES/ROLE_{i}', f'Role Profile: ROLE_{i}'])
        writer.writerow(['Project Management & Processes', '06_PROCESSES', 'Definitions and workflows for the 47 core micro-processes.'])
        for phase, processes in phase_processes.items():
            for process_code, process_name in processes:
                process_id = process_catalog.get(process_name.strip())
                writer.writerow(['Project Management & Processes', f'06_PROCESSES/{phase}/{process_code}_{process_name.strip().replace(" ", "_")}', f'Process Definition for {process_name.strip()} (ID: {process_id})'])
        writer.writerow(['Deliverables', '07_DELIVERABLES', 'Generated artifacts and deliverables from the processes.'])
        writer.writerow(['Logs, Reports & Journals', '08_LOGS', 'Application logs from agent and system execution.'])
        writer.writerow(['Logs, Reports & Journals', '09_JOURNALS', 'System journals and operational records.'])
        writer.writerow(['Logs, Reports & Journals', '10_REPORTS', 'Generated reports from system execution.'])
        writer.writerow(['Configuration & Environment', '11_SCRIPTS', 'Supporting scripts for automation and system management.'])
        writer.writerow(['Configuration & Environment', '12_CONFIGS', 'Configuration files for the system and its components.'])
        writer.writerow(['Archive', '13_ARCHIVE', 'Archived files and previous versions.'])

    # Generate the coverage matrix
    with open('coverage_matrix.md', 'w') as f:
        f.write('# Documentation Coverage Matrix\n\n')
        f.write('This matrix tracks the documentation coverage for the 47 core processes in the GALAXYDEVELOPMENT system.\n\n')
        f.write('| Process ID | Process Name | Phase | Process Definition | Methodology & Standards | Role Assignments | Inventory Catalog | Coverage Matrix | Gaps Analysis | Process Workflow | Execution Guide |\n')
        f.write('| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n')
        for phase, processes in phase_processes.items():
            for process_code, process_name in processes:
                process_id = process_catalog.get(process_name.strip())
                f.write(f'| {process_id} | {process_name.strip()} | {phase} | | | | | | | | |\n')

if __name__ == '__main__':
    generate_process_documentation()

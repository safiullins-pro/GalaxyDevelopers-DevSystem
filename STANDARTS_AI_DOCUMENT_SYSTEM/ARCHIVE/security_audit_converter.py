
import pandas as pd

def create_security_audit_excel():
    with open("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/ToDo/Phase1/P1.2/security_audit.txt", "r") as f:
        lines = [line.strip() for line in f.readlines()]

    df = pd.DataFrame(lines, columns=["Найденные секреты"])
    df.to_excel("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/ToDo/Phase1/P1.2/security_audit.xlsx", index=False)

if __name__ == "__main__":
    create_security_audit_excel()

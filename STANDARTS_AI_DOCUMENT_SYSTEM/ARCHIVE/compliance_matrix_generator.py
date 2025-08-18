
import pandas as pd

def create_compliance_matrix():
    standards = ["ITIL 4", "ISO 27001", "COBIT"]
    processes = [f"P{i}.{j}" for i in range(1, 8) for j in range(1, 4)]

    compliance_matrix = pd.DataFrame(index=processes, columns=standards)
    compliance_matrix.to_excel("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/ToDo/Phase1/P1.4/compliance_matrix.xlsx")

if __name__ == "__main__":
    create_compliance_matrix()

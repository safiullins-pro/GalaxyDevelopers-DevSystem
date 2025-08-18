
import pandas as pd

def create_raci_matrix():
    processes = [f"P{i}.{j}" for i in range(1, 8) for j in range(1, 4)]
    roles = [f"Role_{i}" for i in range(1, 36)]

    raci_matrix = pd.DataFrame(index=processes, columns=roles)
    raci_matrix.to_excel("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/ToDo/Phase1/P1.3/raci_matrix.xlsx")

if __name__ == "__main__":
    create_raci_matrix()

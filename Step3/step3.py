import pandas as pd 
import numpy as np
import os
from io import StringIO

def read_avzn(path):
    columns = ["Actv", "Zone", "Quantity", "Category1", "Category2", "Category3", "Category4"]

    with open(os.path.join(path, "avzn31ft.txt"), "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_idx = next(i for i, line in enumerate(lines) if "Actv Zone Quantity" in line)

    data_start = None
    for i in range(header_idx + 1, len(lines)):
        if lines[i].strip().startswith("-----"):
            data_start = i + 1
            break

    data_lines = []
    for line in lines[data_start:]:
        parts = line.split()
        if len(parts) == 7:
            data_lines.append(line)
        elif data_lines:
            break

    data = "".join(data_lines)

    df = pd.read_csv(StringIO(data), sep=r"\s+", header=None, names=columns, engine="python")

    print(df)
    return df



if __name__ == "__main__":
    read_avzn("C://Users//hmackenzie//OneDrive - SystraGroup//LEIM_Python//New_Tool//Step3//Inputs")
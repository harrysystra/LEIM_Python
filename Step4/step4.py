import pandas as pd 
import os
from io import StringIO

#CONFIGURATION
max_iterations = 10
tolerance = 0.1

input_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step4\\Inputs'
output_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step4\\Outputs'

step2_output_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step2\\Outputs'

test_scenarios = ['Low', 'Behavioural', 'High']

year = "2031"

def read_step2_outputs(path,
                        test_scenario):
    test_scenario_co_df = pd.read_csv(os.path.join(path, f'{test_scenario}_co.csv'))
    core_scenario_co_df = pd.read_csv(os.path.join(path, 'Core_co.csv'))

    test_scenario_co_df = test_scenario_co_df.drop(columns=[col for col in test_scenario_co_df.columns if '20' in col and year not in col])
    core_scenario_co_df = core_scenario_co_df.drop(columns=[col for col in core_scenario_co_df.columns if '20' in col and year not in col])

    return test_scenario_co_df, core_scenario_co_df

def read_cozn(path):
    columns = ["Actv", "Zone", "COLevel1", "COLevel2", "COLevel3", "COLevel4"]

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    dash_lines = [i for i, line in enumerate(lines) if line.strip().startswith("-----")]

    if len(dash_lines) < 2:
        raise ValueError("COZN file not in expected format - missing dashed lines. \n Correct file provided?")

    data_start = dash_lines[1] + 1

    data = "".join(lines[data_start:])

    df = pd.read_csv(StringIO(data), sep=r"\s+", header=None, names=columns, engine="python")

    print(df)
    return df
"""
def read_avzn(path):
    columns = ["Actv", "Zone", "Quantity", "Category1", "Category2", "Category3", "Category4"]

    dash_count = 0
    data_lines = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("-----"):
                dash_count += 1
                continue
            elif line.strip().startswith("00000000"):
                break        
            if dash_count == 2:
                if line.strip(): 
                    data_lines.append(line)

    if not data_lines:
        raise ValueError(f"No data rows found in {path}")

    df = pd.read_csv(
        StringIO("".join(data_lines)),
        sep=r"\s+",
        header=None,
        names=columns,
        dtype={
            "Actv": "int32",
            "Zone": "int32",
            "Quantity": "float64",
            "Category1": "float64",
            "Category2": "float64",
            "Category3": "float64",
            "Category4": "float64",
        },
        engine="python"
    )
    print(df)
    return df
"""

def read_avzn_temp(path):
    df = pd.read_csv(os.path.join(path, 'avzn31ft.csv'))
    
    print(df)
    return df

def multiply_avzn_and_cozn(avzn_df, cozn_df):

    pass

def ntem_targets_and_scaling_factors():
    pass

def adjustment_one():
    pass

def adjustment_two():
    pass

def calculate_new_cozn():
    pass

def iterate_procedure_until_target():
    pass

if __name__ == "__main__":
    read_step2_outputs(step2_output_dir, 'High')
    cozn_df = read_cozn(os.path.join(input_dir, 'cozn31ft.dat'))
    avzn_df = read_avzn_temp(os.path.join(input_dir))

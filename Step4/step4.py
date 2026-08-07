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

    data_lines = []
    for line in lines[data_start:]:
        parts = line.split()
        if len(parts) != 6:
            break
        data_lines.append(line)

    data = "".join(data_lines)

    df = pd.read_csv(StringIO(data), sep=r"\s+", header=None, names=columns, engine="python")

    print(df)
    return df

def read_geodef(path):
    columns = ["Zone", "D30_Districts ID"]

    geo_df = pd.read_csv(os.path.join(path, 'geodef_GISCorrect.csv'))
    return geo_df

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

def multiply_avzn_and_cozn(avzn_df: pd.DataFrame, 
                           cozn_df: pd.DataFrame):
    """
    Merge cozn proportions with avzn quantities on Actv and Zone,
    then multiply each CO level by quantity 
    Extra avzn-only Actv rows are exclued"""

    avzn_subset = avzn_df[['Actv', 'Zone', 'Quantity']].copy()

    df = cozn_df.merge(avzn_subset, on=['Actv', 'Zone'], how='left', validate='one_to_one')

    if df['Quantity'].isna().any():
        missing = df.loc[df['Quantity'].isna(), ['Actv', 'Zone']]
        raise ValueError(f"Missing Quantity for Actv-Zone pairs: {missing}")

    for col in ['COLevel1', 'COLevel2', 'COLevel3', 'COLevel4']:
        df[col] = df[col] * df['Quantity']

    print(df)
    return df

def aggregate_to_district_level(multiplied_df: pd.DataFrame,
                                geodef_df: pd.DataFrame):
    """Aggregate zone-level multiplied CO output to district level using thr geodef file
        removing activity from this step"""

    df = multiplied_df.copy()
    geo = geodef_df[['Zone', 'D30_Districts ID']].copy()

    df["Zone"] = pd.to_numeric(df["Zone"], errors='coerce')
    geo["Zone"] = pd.to_numeric(geo["Zone"], errors='coerce')
    geo["D30_Districts ID"] =pd.to_numeric(geo["D30_Districts ID"], errors='coerce')

    df = df.dropna(subset=['Zone'])
    geo = geo.dropna(subset=['Zone', 'D30_Districts ID'])

    df["Zone"] = df["Zone"].astype(int)
    geo["Zone"] = geo["Zone"].astype(int)
    geo["D30_Districts ID"] = geo["D30_Districts ID"].astype(int)

    if geo["Zone"].duplicated().any():
        raise ValueError("Duplicate Zone entries found in geodef_df.")

    merged = df.merge(geo, on="Zone", how="left", validate="many_to_one")

    value_cols = ["COLevel1", "COLevel2", "COLevel3", "COLevel4"]

    district_df = (
        merged.groupby("D30_Districts ID", as_index=False)[value_cols]
        .sum()
        .rename(columns={"D30_District ID": "District"})
    )
    print(district_df)
    return district_df

def format_scenario_co_data(path):

    df = pd.read_csv(path)
    df = df[df["District"] != 30]

    print(df)

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
    multiplied_df = multiply_avzn_and_cozn(avzn_df, cozn_df)
    geodef_df = read_geodef(os.path.join(input_dir))
    result = aggregate_to_district_level(multiplied_df, geodef_df)
    format_scenario_co_data("Step4\\Inputs\\Core_co.csv")

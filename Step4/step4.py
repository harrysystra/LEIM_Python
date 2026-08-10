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
        .rename(columns={"D30_Districts ID": "District"})
    )
    colevel_cols = ["COLevel1", "COLevel2", "COLevel3", "COLevel4"]
    district_df["Total"] = district_df[colevel_cols].sum(axis=1)
    print(district_df)
    return district_df

import pandas as pd

def format_scenario_co_data(path, target_year=2031):
    df = pd.read_csv(path)

    year_col = str(target_year)

    if year_col not in df.columns:
        if target_year in df.columns:
            year_col = target_year
        else:
            raise ValueError(f"Target year column '{target_year}' not found in file.")

    df = df[["District", "CarOwnership", year_col]].copy()

    df["District"] = pd.to_numeric(df["District"], errors="coerce")
    df = df.loc[df["District"] != 30, :]

    co_map = {
        "no_car": "COLevel1",
        "1_car": "COLevel2",
        "2_cars": "COLevel3",
        "3+_cars": "COLevel4"
    }

    df["CarOwnership"] = df["CarOwnership"].map(co_map)

    if df["CarOwnership"].isna().any():
        bad = df.loc[df["CarOwnership"].isna(), :]
        raise ValueError(f"Unmapped CarOwnership values found:\n{bad}")

    df_wide = (
        df.pivot(index="District", columns="CarOwnership", values=year_col)
          .reset_index()
    )

    df_wide.columns.name = None

    colevel_cols = ["COLevel1", "COLevel2", "COLevel3", "COLevel4"]
    df_wide = df_wide[["District"] + colevel_cols]

    df_wide["Total"] = df_wide[colevel_cols].sum(axis=1)


    print(df_wide)
    return df_wide

def scale_totals_to_avzn_total(avzn_cozn_df, scenario_df):


    colevel_cols = ["COLevel1", "COLevel2", "COLevel3", "COLevel4"]

    avzn_df = avzn_cozn_df.copy()
    scen_df = scenario_df.copy()

    avzn_df = avzn_df[["District"] + colevel_cols + ["Total"]]
    scen_df = scen_df[["District"] + colevel_cols + ["Total"]]

    avzn_df = avzn_df.rename(columns={"Total": "avzn_total"})
    scen_df = scen_df.rename(columns={"Total": "scenario_total"})

    merged = avzn_df.merge(
        scen_df,
        on="District",
        how="inner",
        suffixes=("_avzn", "_scenario")
    )

    missing_in_scenario = set(avzn_df["District"]) - set(scen_df["District"])
    missing_in_avzn = set(scen_df["District"]) - set(avzn_df["District"])

    if missing_in_scenario:
        print(f"Warning: districts in avzn*cozn but not scenario_df: {sorted(missing_in_scenario)}")
    if missing_in_avzn:
        print(f"Warning: districts in scenario_df but not avzn*cozn: {sorted(missing_in_avzn)}")

    if (merged["scenario_total"] == 0).any():
        bad = merged.loc[merged["scenario_total"] == 0, ["District", "scenario_total"]]
        raise ValueError(f"Scenario total is zero for some districts:\n{bad}")

    result = pd.DataFrame()
    result["District"] = merged["District"]

    for col in colevel_cols:
        result[col] = (
            merged[f"{col}_scenario"] * merged["avzn_total"] / merged["scenario_total"]
        )

    result["Total"] = result[colevel_cols].sum(axis=1)

    print(result)

    return result

import pandas as pd
import numpy as np

def calculate_scaling_factors(scaled_avzn_total_df, avzn_cozn_df):

    colevel_cols = ["COLevel1", "COLevel2", "COLevel3", "COLevel4"]

    scaled_df = scaled_avzn_total_df.copy()
    avzn_df = avzn_cozn_df.copy()

    scaled_df = scaled_df[["District"] + colevel_cols]
    avzn_df = avzn_df[["District"] + colevel_cols]

    merged = scaled_df.merge(
        avzn_df,
        on="District",
        how="inner",
        suffixes=("_scaled", "_avzn")
    )

    missing_in_scaled = set(avzn_df["District"]) - set(scaled_df["District"])
    missing_in_avzn = set(scaled_df["District"]) - set(avzn_df["District"])

    if missing_in_scaled:
        print(f"Warning: districts in avzn_cozn_df but not scaled_avzn_total_df: {sorted(missing_in_scaled)}")
    if missing_in_avzn:
        print(f"Warning: districts in scaled_avzn_total_df but not avzn_cozn_df: {sorted(missing_in_avzn)}")

    result = pd.DataFrame()
    result["District"] = merged["District"]

    for col in colevel_cols:
        denom = merged[f"{col}_avzn"]

        result[col] = np.where(
            denom != 0,
            merged[f"{col}_scaled"] / denom,
            np.nan
        )

    print(result)
    return result

import pandas as pd
import numpy as np

import pandas as pd
import numpy as np

def first_adjustment(avzn_cozn_df, scaling_factors_df, avzn_df, geodef_df):
    colevel_cols = ["COLevel1", "COLevel2", "COLevel3", "COLevel4"]

    ac = avzn_cozn_df.copy()
    sf = scaling_factors_df.copy()
    av = avzn_df.copy()
    geo = geodef_df.copy()

    if "Zone" not in ac.columns:
        raise ValueError(
            f"first_adjustment expected a zone-level dataframe with a 'Zone' column, "
            f"but got columns: {ac.columns.tolist()}"
        )

    if "District" not in geo.columns:
        if "D30_Districts ID" in geo.columns:
            geo = geo.rename(columns={"D30_Districts ID": "District"})
        else:
            raise ValueError("geodef_df must contain either 'District' or 'D30_Districts ID'.")

    geo = geo[["Zone", "District"]].copy()

    for df in [ac, av, geo]:
        if "Zone" in df.columns:
            df["Zone"] = pd.to_numeric(df["Zone"], errors="coerce")

    sf["District"] = pd.to_numeric(sf["District"], errors="coerce")
    geo["District"] = pd.to_numeric(geo["District"], errors="coerce")

    ac = ac.dropna(subset=["Zone"])
    av = av.dropna(subset=["Zone"])
    geo = geo.dropna(subset=["Zone", "District"])
    sf = sf.dropna(subset=["District"])

    ac["Zone"] = ac["Zone"].astype(int)
    av["Zone"] = av["Zone"].astype(int)
    geo["Zone"] = geo["Zone"].astype(int)
    geo["District"] = geo["District"].astype(int)
    sf["District"] = sf["District"].astype(int)

    ac = ac.merge(geo, on="Zone", how="left", validate="many_to_one")

    if ac["District"].isna().any():
        bad = ac.loc[ac["District"].isna(), ["Zone"]].drop_duplicates()
        raise ValueError(f"Some zones in avzn_cozn_df could not be mapped to a District:\n{bad}")

    # Rename before merge so the name is guaranteed to survive
    av_for_merge = av.rename(columns={"Quantity": "TotalHHAVZN"})

    if "Actv" in av_for_merge.columns and "Actv" in ac.columns:
        ac = ac.merge(
            av_for_merge[["Actv", "Zone", "TotalHHAVZN"]],
            on=["Actv", "Zone"],
            how="left",
            validate="one_to_one"
        )
    else:
        ac = ac.merge(
            av_for_merge[["Zone", "TotalHHAVZN"]],
            on="Zone",
            how="left",
            validate="many_to_one"
        )

    if ac["TotalHHAVZN"].isna().any():
        bad = ac.loc[ac["TotalHHAVZN"].isna(), ["Zone"]].drop_duplicates()
        raise ValueError(f"Some rows could not find Quantity from avzn_df:\n{bad}")

    ac = ac.merge(
        sf[["District"] + colevel_cols],
        on="District",
        how="left",
        suffixes=("", "_factor"),
        validate="many_to_one"
    )

    factor_cols = [f"{c}_factor" for c in colevel_cols]
    missing_factor = ac[factor_cols].isna().any(axis=1)
    if missing_factor.any():
        bad = ac.loc[missing_factor, ["Zone", "District"]].drop_duplicates()
        raise ValueError(f"Some rows could not find district scaling factors:\n{bad}")

    for col in colevel_cols:
        ac[col] = ac[col] * ac[f"{col}_factor"]

    ac["TotalHH"] = ac[colevel_cols].sum(axis=1)

    ac["ScalingFactor"] = np.where(
        ac["TotalHH"] != 0,
        ac["TotalHHAVZN"] / ac["TotalHH"],
        np.nan
    )

    output_cols = []
    if "Actv" in ac.columns:
        output_cols.append("Actv")
    output_cols += ["Zone", "District"] + colevel_cols + ["TotalHH", "TotalHHAVZN", "ScalingFactor"]

    print(ac[output_cols].copy())
    return ac[output_cols].copy()


def second_adjustment(adjustment_1_df, avzn_df):
    """
    Apply the row-level ScalingFactor from adjustment_1 to each CO level.

    Parameters
    ----------
    adjustment_1_df : pd.DataFrame
        Output from first_adjustment with columns including:
        ['Zone', 'COLevel1', 'COLevel2', 'COLevel3', 'COLevel4',
         'TotalHH', 'TotalHHAVZN', 'ScalingFactor']
        and optionally 'Actv', 'District'

    avzn_df : pd.DataFrame
        Original AVZN dataframe with at least:
        ['Zone', 'Quantity']
        and optionally 'Actv'

    Returns
    -------
    pd.DataFrame
        Columns:
        ['COLevel1', 'COLevel2', 'COLevel3', 'COLevel4', 'TotalHH', 'TotalHHAVZN']
        plus key columns such as 'Actv', 'Zone', and 'District' if present.
    """

    colevel_cols = ["COLevel1", "COLevel2", "COLevel3", "COLevel4"]

    adj = adjustment_1_df.copy()
    av = avzn_df.copy()

    required_adj_cols = colevel_cols + ["ScalingFactor"]
    missing_adj = [c for c in required_adj_cols if c not in adj.columns]
    if missing_adj:
        raise ValueError(f"adjustment_1_df is missing required columns: {missing_adj}")

    # Standardise key columns
    for df in [adj, av]:
        if "Zone" in df.columns:
            df["Zone"] = pd.to_numeric(df["Zone"], errors="coerce")
        if "Actv" in df.columns:
            df["Actv"] = pd.to_numeric(df["Actv"], errors="coerce")

    if "Zone" not in adj.columns:
        raise ValueError("adjustment_1_df must contain 'Zone'.")

    if "Quantity" not in av.columns:
        raise ValueError("avzn_df must contain 'Quantity'.")

    adj = adj.dropna(subset=["Zone"])
    av = av.dropna(subset=["Zone"])

    adj["Zone"] = adj["Zone"].astype(int)
    av["Zone"] = av["Zone"].astype(int)

    if "Actv" in adj.columns and "Actv" in av.columns:
        adj["Actv"] = adj["Actv"].astype(int)
        av["Actv"] = av["Actv"].astype(int)
        av_merge = av[["Actv", "Zone", "Quantity"]].rename(columns={"Quantity": "TotalHHAVZN"})
        merged = adj.merge(
            av_merge,
            on=["Actv", "Zone"],
            how="left",
            validate="one_to_one",
            suffixes=("", "_avzn")
        )
    else:
        av_merge = av[["Zone", "Quantity"]].rename(columns={"Quantity": "TotalHHAVZN"})
        merged = adj.merge(
            av_merge,
            on="Zone",
            how="left",
            validate="many_to_one",
            suffixes=("", "_avzn")
        )

    if merged["TotalHHAVZN"].isna().any():
        key_cols = ["Zone"] + (["Actv"] if "Actv" in merged.columns else [])
        bad = merged.loc[merged["TotalHHAVZN"].isna(), key_cols].drop_duplicates()
        raise ValueError(f"Some rows could not find Quantity from avzn_df:\n{bad}")

    result = merged.copy()

    for col in colevel_cols:
        result[col] = result[col] * result["ScalingFactor"]

    result["TotalHH"] = result[colevel_cols].sum(axis=1)

    # Exact check requested
    mismatch = ~np.isclose(result["TotalHH"], result["TotalHHAVZN"], rtol=0, atol=1e-9)
    if mismatch.any():
        key_cols = [c for c in ["Actv", "Zone", "District"] if c in result.columns]
        debug_cols = key_cols + colevel_cols + ["TotalHH", "TotalHHAVZN", "ScalingFactor"]
        bad = result.loc[mismatch, debug_cols]
        raise ValueError(
            "TotalHH does not exactly match TotalHHAVZN for some rows.\n"
            f"{bad.head(20)}"
        )

    output_cols = [c for c in ["Actv", "Zone", "District"] if c in result.columns]
    output_cols += colevel_cols + ["TotalHH", "TotalHHAVZN"]
    print(result[output_cols].copy())
    return result[output_cols].copy()

import pandas as pd
import numpy as np

def calculate_new_cozn(adjustment_2_df):

    colevel_cols = ["COLevel1", "COLevel2", "COLevel3", "COLevel4"]

    df = adjustment_2_df.copy()

    required_cols = colevel_cols + ["TotalHH"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"adjustment_2_df is missing required columns: {missing}")

    result = pd.DataFrame(index=df.index)

    for col in colevel_cols:
        result[col] = np.where(
            df["TotalHH"] != 0,
            df[col] / df["TotalHH"],
            np.nan
        )
    print(result)
    return result


if __name__ == "__main__":
    read_step2_outputs(step2_output_dir, 'High')
    cozn_df = read_cozn(os.path.join(input_dir, 'cozn31ft.dat'))
    avzn_df = read_avzn_temp(os.path.join(input_dir))
    multiplied_df = multiply_avzn_and_cozn(avzn_df, cozn_df)
    geodef_df = read_geodef(os.path.join(input_dir))
    avzn_cozn = aggregate_to_district_level(multiplied_df, geodef_df)
    test_scenario_co = format_scenario_co_data("Step4\\Inputs\\High_co.csv", 2031)
    scaled_avzn_total = scale_totals_to_avzn_total(avzn_cozn, test_scenario_co)
    scaling_factors = calculate_scaling_factors(scaled_avzn_total, avzn_cozn)
    adjustment_1 = first_adjustment(multiplied_df, scaling_factors, avzn_df, geodef_df)
    adjustment_2 = second_adjustment(adjustment_1, avzn_df)
    calculate_new_cozn(adjustment_2)

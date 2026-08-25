import pandas as pd 
import numpy as np
import os
from io import StringIO


def read_geodef(path):
        
        geodef_df = pd.read_csv(os.path.join(path, 'geodef_GISCorrect.csv'))

        return geodef_df

def read_avzn(path):
    """Reads AVZN from standard format and returns DataFrame with district added (district info from Geodef file)"""

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

    df["Sum"] = df.iloc[:, -4:-1].sum(axis=1)
    df["Adults"] = df.iloc[:, -4:-2].sum(axis=1)

    geodef_df = read_geodef(path="C://Users//hmackenzie//OneDrive - SystraGroup//LEIM_Python//New_Tool//Step2//Inputs")
    df["District"] = df["Zone"].map(geodef_df.set_index("Zone")["D30_Districts ID"])

    print(geodef_df)

    print(df)
    return df



def append_ntem_target_column(avzn_df,
                              planning_hhs_difference_df,
                              planning_jobs_difference_df,
                              year,
                              output_col=None):
    lookup_col = f"Sum of {year}"
    if output_col is None:
        output_col = f"NTEM_Target_{year}"

    df = avzn_df.copy()

    hhs = planning_hhs_difference_df[["District", lookup_col]].rename(columns={lookup_col: "_hhs"})
    jobs = planning_jobs_difference_df[["District", lookup_col]].rename(columns={lookup_col: "_jobs"})

    df = df.merge(hhs, on="District", how="left")
    df = df.merge(jobs, on="District", how="left")

    df[output_col] = df["_jobs"]
    df.loc[df["Actv"] < 40, output_col] = df.loc[df["Actv"] < 40, "_hhs"]

    df = df.drop(columns=["_hhs", "_jobs"])

    return df



def calculate_additional_hhs_and_emp(df,
                                     year):
    result_df = df.copy()

    result_df['hh/emp'] = np.where(result_df["Actv"] < 34, "hh", "Emp")
    group_totals = result_df.groupby(["District", 'hh/emp'])["Quantity"].transform("sum")
    result_df['Proportion'] = result_df["Quantity"] / group_totals

    result_df['ExtraHH/jobs'] = result_df[f'NTEM_Target_{year}'] * result_df['Proportion']

    print(result_df)
    return result_df



def add_extra_people_by_pt_on_hh(df):
    df = df.copy()

    activity_classifications_df = pd.read_csv('Step3//Inputs//activity_classifications.csv')
    lookup = activity_classifications_df.set_index("Actv")["Classification1"]
    df["Classification1"] = df["Actv"].map(lookup)

    df["1_Quantity"] = df["Quantity"] + df["ExtraHH/jobs"]

    for i in range(1, 5):
        df[f"1_Category{i}"] = df[f"Category{i}"] + (df[f"Category{i}"] * df["ExtraHH/jobs"]) / df["Quantity"]

    print(df)
    return df



def check_children_at_district_level_ntem(df, high_planning_under16_difference_df, year):

    out = pd.DataFrame({"District": range(1, 30)})

    after = (
        df.loc[df["Actv"] < 40]
        .groupby("District")["1_Category1"]
        .sum()
        .rename("ChildrenAfter")
    )

    before = (
        df.loc[df["Actv"] < 40]
        .groupby("District")["Category1"]
        .sum()
        .rename("ChildrenBefore")
    )

    out = out.merge(after, on="District", how="left")
    out = out.merge(before, on="District", how="left")

    out[["ChildrenAfter", "ChildrenBefore"]] = out[["ChildrenAfter", "ChildrenBefore"]].fillna(0)
    out["Difference"] = out["ChildrenAfter"] - out["ChildrenBefore"]

    lookup_col = f"Sum of {year}"
    ntem_lookup = high_planning_under16_difference_df.set_index("District")[lookup_col]
    out["NTEM Target"] = out["District"].map(ntem_lookup)

    out["Remaining"] = out["NTEM Target"] - out["Difference"]

    print(out)

    return out







if __name__ == "__main__":
    avzn_df = read_avzn(path="C://Users//hmackenzie//OneDrive - SystraGroup//LEIM_Python//New_Tool//Step3//Inputs")
    planning_hh_difference_df = pd.read_csv('Outputs//2_Extended_NTEM_Targets//High_planning_HHs_difference.csv')
    planning_jobs_difference_df = pd.read_csv('Outputs//2_Extended_NTEM_Targets//High_planning_jobs_difference.csv')
    additional_hh_emp_df = append_ntem_target_column(avzn_df=avzn_df,
                                                     planning_hhs_difference_df=planning_hh_difference_df,
                                                     planning_jobs_difference_df=planning_jobs_difference_df,
                                                     year=2046)
    extra_hhs_emp = calculate_additional_hhs_and_emp(df=additional_hh_emp_df,
                                                     year=2046)
    extra_ppl_df = add_extra_people_by_pt_on_hh(extra_hhs_emp)
    high_under16_df = pd.read_csv('Outputs//2_Extended_NTEM_Targets//High_planning_under16_difference.csv')
    district_df = check_children_at_district_level_ntem(df=extra_ppl_df,
                                                        high_planning_under16_difference_df=high_under16_df,
                                                        year=2046)

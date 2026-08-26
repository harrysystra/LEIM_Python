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

    df["Sum"] = df["Category1"] + df["Category2"] + df["Category3"] + df["Category4"]
    df["Adults"] = df["Category2"] + df["Category3"] + df["Category4"]

    geodef_df = read_geodef(path="C://Users//hmackenzie//OneDrive - SystraGroup//LEIM_Python//New_Tool//Step2//Inputs")
    df["District"] = df["Zone"].map(geodef_df.set_index("Zone")["D30_Districts ID"])

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
    df.loc[df["Actv"] < 33, output_col] = df.loc[df["Actv"] < 33, "_hhs"]

    df = df.drop(columns=["_hhs", "_jobs"])

    return df



def calculate_additional_hhs_and_emp(df,
                                     year):
    result_df = df.copy()

    result_df['hh/emp'] = np.where(result_df["Actv"] < 33, "hh", "Emp")
    group_totals = result_df.groupby(["District", 'hh/emp'])["Quantity"].transform("sum")
    result_df['Proportion'] = result_df["Quantity"] / group_totals

    result_df['ExtraHH/jobs'] = result_df[f'NTEM_Target_{year}'] * result_df['Proportion']

    return result_df



def add_extra_people_by_pt_on_hh(df):
    df = df.copy()

    activity_classifications_df = pd.read_csv('Step3//Inputs//activity_classifications.csv')
    lookup = activity_classifications_df.set_index("Actv")["Classification1"]
    df["Classification1"] = df["Actv"].map(lookup)

    df["1_Quantity"] = df["Quantity"] + df["ExtraHH/jobs"]

    for i in range(1, 5):
        df[f"1_Category{i}"] = df[f"Category{i}"] + (df[f"Category{i}"] * df["ExtraHH/jobs"]) / df["Quantity"]

    return df



def check_children_at_district_level_ntem(df, high_planning_under16_difference_df, year):

    out = pd.DataFrame({"District": range(1, 30)})

    after = (
        df.loc[df["Actv"] < 33]
        .groupby("District")["1_Category1"]
        .sum()
        .rename("ChildrenAfter")
    )

    before = (
        df.loc[df["Actv"] < 33]
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

    return out


def distribute_remaining_children_to_hh_with_child(
    df,
    activity_classifications_df,
    district_children_df
):
    out = df.copy()

    classification_cols = ["Classification1", "Classification2", "Classification3", "Classification4"]
    lookup_df = activity_classifications_df.set_index("Actv")

    for col in classification_cols:
        out[col] = out["Actv"].map(lookup_df[col])

    children_totals = (
        out.loc[out["Classification2"] == "Children"]
        .groupby("District")["1_Category1"]
        .sum()
    )

    out["_children_district_total"] = out["District"].map(children_totals)

    out["Prop Child by 30 Sect"] = 0.0

    mask_prop = (
        (out["Classification2"] == "Children") &
        (out["_children_district_total"].notna()) &
        (out["_children_district_total"] != 0)
    )

    out.loc[mask_prop, "Prop Child by 30 Sect"] = (
        out.loc[mask_prop, "1_Category1"] / out.loc[mask_prop, "_children_district_total"]
    )

    remaining_lookup = district_children_df.set_index("District")["Remaining"]
    out["Remaining Children to Allocate"] = 0.0

    mask_remaining = out["Classification2"] == "Children"
    out.loc[mask_remaining, "Remaining Children to Allocate"] = (
        out.loc[mask_remaining, "District"].map(remaining_lookup).fillna(0)
    )

    out = out.drop(columns=["_children_district_total"])

    out["Extra Children by Zone"] = out["Prop Child by 30 Sect"] * out["Remaining Children to Allocate"]
    out["New Children + Jobs1"] = out["Extra Children by Zone"] + out["1_Category1"]

    return out



def create_updated_avzn(df):
    out = df.copy()

    classification_cols = [col for col in out.columns if "Classification" in col]

    keep_cols = (
        ["Actv", "Zone", "District"] +
        classification_cols +
        ["1_Quantity", "New Children + Jobs1", "1_Category2", "1_Category3", "1_Category4"]
    )

    out = out[keep_cols].copy()

    out = out.rename(columns={
        "1_Quantity": "Quantity",
        "New Children + Jobs1": "Category1",
        "1_Category2": "Category2",
        "1_Category3": "Category3",
        "1_Category4": "Category4"
    })

    out["Total population"] = (
        out["Category1"] +
        out["Category2"] +
        out["Category3"] +
        out["Category4"]
    )

    out["Total adults"] = (
        out["Category2"] +
        out["Category3"] +
        out["Category4"]
    )

    return out



def sum_population_tables(csv_path_1, csv_path_2, csv_path_3):
    df1 = pd.read_csv(csv_path_1)
    df2 = pd.read_csv(csv_path_2)
    df3 = pd.read_csv(csv_path_3)

    if list(df1.columns) != list(df2.columns) or list(df1.columns) != list(df3.columns):
        raise ValueError("Input CSVs do not have matching columns")

    out = df1.copy()
    cols_to_sum = [col for col in out.columns if col != "District"]
    out[cols_to_sum] = df1[cols_to_sum] + df2[cols_to_sum] + df3[cols_to_sum]

    return out



def check_population_at_district_level_ntem_vs_step3(
    new_avzn_df,
    old_avzn_df,
    population_target_df,
    under16_target_df,
    year,
    resident_actv_max=32
):

    new_residents = new_avzn_df.loc[new_avzn_df["Actv"] <= resident_actv_max].copy()
    old_residents = old_avzn_df.loc[old_avzn_df["Actv"] <= resident_actv_max].copy()

    out = pd.DataFrame({"District": sorted(new_residents["District"].dropna().unique())})

    after = (
        new_residents.groupby("District")["Total adults"]
        .sum()
        .rename("Adults After")
    )

    if "Adults" in old_residents.columns:
        before = (
            old_residents.groupby("District")["Adults"]
            .sum()
            .rename("Adults Before")
        )
    else:
        tmp = old_residents.copy()
        tmp["Adults"] = tmp["Category2"] + tmp["Category3"] + tmp["Category4"]
        before = (
            tmp.groupby("District")["Adults"]
            .sum()
            .rename("Adults Before")
        )

    out = out.merge(after, on="District", how="left")
    out = out.merge(before, on="District", how="left")

    out[["Adults After", "Adults Before"]] = out[["Adults After", "Adults Before"]].fillna(0)
    out["Difference"] = out["Adults After"] - out["Adults Before"]

    lookup_col = f"Sum of {year}"

    if lookup_col not in population_target_df.columns:
        raise ValueError(f"Column '{lookup_col}' not found in population_target_df")

    if lookup_col not in under16_target_df.columns:
        raise ValueError(f"Column '{lookup_col}' not found in under16_target_df")

    population_lookup = population_target_df.set_index("District")[lookup_col]
    under16_lookup = under16_target_df.set_index("District")[lookup_col]

    out["NTEM Population"] = out["District"].map(population_lookup)
    out["NTEM Children"] = out["District"].map(under16_lookup)

    out[["NTEM Population", "NTEM Children"]] = out[["NTEM Population", "NTEM Children"]].fillna(0)

    out["NTEM Adults"] = out["NTEM Population"] - out["NTEM Children"]
    out["Remaining Adults"] = out["NTEM Adults"] - out["Difference"]

    return out


def redistribute_adults_to_multi_adult_households(
    df,
    population_check_df
):
    out = df.copy()

    remaining_adults_lookup = population_check_df.set_index("District")["Remaining Adults"]
    out["Remaining Adults"] = out["District"].map(remaining_adults_lookup)

    mask = out["Actv"].gt(16) & out["Actv"].lt(33)

    eligible_adults = out["Total adults"].where(mask, 0)
    district_multiadult_totals = eligible_adults.groupby(out["District"]).transform("sum")

    out["Scaling Factor"] = np.where(
        mask,
        out["Total adults"] / district_multiadult_totals,
        0.0
    )

    out["Extra Adults"] = np.where(
        mask,
        out["Remaining Adults"] * out["Scaling Factor"],
        0.0
    )

    for i in range(1, 5):
        out[f"2_Category{i}"] = np.where(
            mask,
            out["Extra Adults"] * out[f"Category{i}"] / out["Total adults"],
            0.0
        )

    out["Total Adult Diff"] = out["2_Category2"] + out["2_Category3"] + out["2_Category4"]

    return out



def create_final_avzn(redistributed_adults_df,
                      updated_avzn):
    out = updated_avzn.copy()

    for i in range(2, 5):
        out[f"Category{i}"] += redistributed_adults_df[f"2_Category{i}"]

    for i in range(1, 5):
        out.drop(labels=f"Classification{i}", axis=1, inplace=True)

    print(out)
    return out



def export_df_as_csv(csv_name: str, table: pd.DataFrame, output_folder: str):
    """
    Exports df as a csv file and saves to output folder. 
    Args:
        - csv_name: desired filename for output
        - table: pandas DataFrame to convert to csv
        - output_folder: full path to desired output location
    """
    output_path = os.path.join(output_folder, csv_name)
    table.to_csv(output_path, index=None, header=True)



if __name__ == "__main__":
    avzn_df = read_avzn(path="C://Users//hmackenzie//OneDrive - SystraGroup//LEIM_Python//New_Tool//Step3//Inputs")
    planning_hh_difference_df = pd.read_csv('Outputs//2_Extended_NTEM_Targets//High_planning_HHs_difference.csv')
    planning_jobs_difference_df = pd.read_csv('Outputs//2_Extended_NTEM_Targets//High_planning_jobs_difference.csv')
    additional_hh_emp_df = append_ntem_target_column(avzn_df=avzn_df,
                                                     planning_hhs_difference_df=planning_hh_difference_df,
                                                     planning_jobs_difference_df=planning_jobs_difference_df,
                                                     year=2031)
    extra_hhs_emp = calculate_additional_hhs_and_emp(df=additional_hh_emp_df,
                                                     year=2031)
    extra_ppl_df = add_extra_people_by_pt_on_hh(extra_hhs_emp)
    high_under16_df = pd.read_csv('Outputs//2_Extended_NTEM_Targets//High_planning_under16_difference.csv')
    district_df = check_children_at_district_level_ntem(df=extra_ppl_df,
                                                        high_planning_under16_difference_df=high_under16_df,
                                                        year=2031)
    activity_class_df = pd.read_csv("Step3//Inputs//activity_classifications.csv")
    distributed_children = distribute_remaining_children_to_hh_with_child(df=extra_ppl_df,
                                                                          activity_classifications_df=activity_class_df,
                                                                          district_children_df=district_df)
    updated_avzn = create_updated_avzn(df=distributed_children)
    population_table = sum_population_tables("Outputs//2_Extended_NTEM_Targets//High_planning_under16_difference.csv",
                                             "Outputs//2_Extended_NTEM_Targets//High_planning_75plus_difference.csv",
                                             "Outputs//2_Extended_NTEM_Targets//High_planning_16-74_difference.csv"
                                             )
    under16_table = pd.read_csv("Outputs//2_Extended_NTEM_Targets//High_planning_under16_difference.csv")
    population_checker_df = check_population_at_district_level_ntem_vs_step3(new_avzn_df=updated_avzn,
                                                                             old_avzn_df=avzn_df,
                                                                             population_target_df=population_table,
                                                                             under16_target_df=under16_table,
                                                                             year=2031)
    redistributed_adults = redistribute_adults_to_multi_adult_households(df=updated_avzn,
                                                                         population_check_df=population_checker_df)
    final_avzn = create_final_avzn(redistributed_adults_df=redistributed_adults,
                                   updated_avzn=updated_avzn)
    export_df_as_csv(csv_name="avzn_updated",
                     table=final_avzn,
                     output_folder="Outputs//3_Scale_AVZN")
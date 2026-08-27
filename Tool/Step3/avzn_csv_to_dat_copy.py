import pandas as pd
from datetime import date
import os


# Function to output to .dat file in AVZN format
def output_to_dat(
    df, path, output_file_name
):
    df["Category1"] = df["Category1"].map("{:.5e}".format)
    df["Category2"] = df["Category2"].map("{:.5e}".format)
    df["Category3"] = df["Category3"].map("{:.5e}".format)
    df["Category4"] = df["Category4"].map("{:.5e}".format)
    df["Quantity"] = df["Quantity"].map("{:.5e}".format)

    df = df.sort_values(by=["Actv", "Zone"])

    cur_date = date.today()
    with open(os.path.join(path, f"{output_file_name}.dat"), "w") as file:
        file.write(
            f" ========================================================================\n"
        )
        file.write(f" DELTA Model: \n\n")
        file.write(f" {cur_date} \n\n")
        file.write(
            f" ========================================================================\n"
        )
        file.write(
            f" ------------------------------------------------------------------------\n"
        )
        file.write(f" AVZN01: Output activity data by zone\n")
        file.write(
            f" .... .... Total...... ...Category ...Category ...Category ...Category\n"
        )
        file.write(
            f" Actv Zone Quantity... ..........1 ..........2 ..........3 ..........4\n"
        )
        file.write(
            f" ------------------------------------------------------------------------\n"
        )
        for i in range(len(df)):
            actv_str = str(int(df.iloc[i]["Actv"])).rjust(4)
            zone_str = str(int(df.iloc[i]["Zone"])).rjust(4)
            quantity_str = str(df.iloc[i]["Quantity"]).ljust(11)
            cat_1_str = str(df.iloc[i]["Category1"]).ljust(11)
            cat_2_str = str(df.iloc[i]["Category2"]).ljust(11)
            cat_3_str = str(df.iloc[i]["Category3"]).ljust(11)
            cat_4_str = str(df.iloc[i]["Category4"]).ljust(11)
            file.write(
                f" {actv_str} {zone_str} {quantity_str} {cat_1_str} {cat_2_str} {cat_3_str} {cat_4_str}\n"
            )
        file.write(
            f" 000000000000000000000000000000000000000000000000000000000000000000000000\n"
        )

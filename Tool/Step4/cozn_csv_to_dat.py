from datetime import date
import os


# Function to output to .dat file in AVZN format
def output_to_dat(
    df, path, output_file_name
):
    df["COLevel1"] = df["COLevel1"].map("{:.5e}".format)
    df["COLevel2"] = df["COLevel2"].map("{:.5e}".format)
    df["COLevel3"] = df["COLevel3"].map("{:.5e}".format)
    df["COLevel4"] = df["COLevel4"].map("{:.5e}".format)

    df = df.sort_values(by=["Actv", "Zone"])

    cur_date = date.today()
    with open(os.path.join(path, f"{output_file_name}.dat"), "w") as file:
        file.write(
            f" ========================================================================\n"
        )
        file.write(f" DELTA Model: \n\n")
        file.write(f" {cur_date} \n\n")
        file.write(f"dir_path = {os.path.dirname(os.path.realpath('step4.py'))}\n")
        file.write(
            f" ========================================================================\n"
        )
        file.write(
            f" ------------------------------------------------------------------------\n"
        )
        file.write(f" COZN01: Output activity data by zone\n")
        file.write(
            f" .... .... Total...... ...COLevel1 ...COLevel2 ...COLevel3 ...COLevel4\n"
        )
        file.write(
            f" ------------------------------------------------------------------------\n"
        )
        for i in range(len(df)):
            actv_str = str(int(df.iloc[i]["Actv"])).rjust(4)
            zone_str = str(int(df.iloc[i]["Zone"])).rjust(4)
            cat_1_str = str(df.iloc[i]["COLevel1"]).ljust(11)
            cat_2_str = str(df.iloc[i]["COLevel2"]).ljust(11)
            cat_3_str = str(df.iloc[i]["COLevel3"]).ljust(11)
            cat_4_str = str(df.iloc[i]["COLevel4"]).ljust(11)
            file.write(
                f" {actv_str} {zone_str} {cat_1_str} {cat_2_str} {cat_3_str} {cat_4_str}\n"
            )
        file.write(
            f" 000000000000000000000000000000000000000000000000000000000000000000000000\n"
        )

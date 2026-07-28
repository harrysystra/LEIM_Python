import csv
from itertools import product
import pandas as pd
import os

years = ['2019', '2026', '2031', '2036', '2041'] # must be between 2019 and 2046 inclusive
scenarios = ['core', 'high', 'low', 'behavioural'] # leave alone unless adding new scenarios

input_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step2\\Inputs'
output_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step2\\Outputs'

input_files = [
    'geodef_GISCorrect.csv',
    'Intersection_MSOA-TfSH_Prop.csv',
    'ntem_8.0_Core_ca_data.csv',
    'ntem_8.0_Core_planning_data.csv'
]

# - read input files

def check_inputs(input_dir):
    # check if input directory exists
    if not os.path.exists(input_dir):
        raise ValueError("Input directory does not exist")

    # check if input files exist
    for file in input_files:
        if not os.path.exists(os.path.join(input_dir, file)):
            raise ValueError(f"Input file {file} does not exist in the input directory")

def read_input_files(input_dir):
    # read input files
    geodef_df = pd.read_csv(os.path.join(input_dir, 'geodef_GISCorrect.csv'))
    intersection_df = pd.read_csv(os.path.join(input_dir, 'Intersection_MSOA-TfSH_Prop.csv'))
    core_ca_df = pd.read_csv(os.path.join(input_dir, 'ntem_8.0_Core_ca_data.csv'))[['msoa_zone_id', 'car_ownership'] + years]
    core_planning_df = pd.read_csv(os.path.join(input_dir, 'ntem_8.0_Core_planning_data.csv'))[['msoa_zone_id', 'population'] + years]
    intersection_df.rename(columns={'Proportions MSOA/Zones': 'Proportion'}, inplace=True)
    print("Input files read successfully!")

    return geodef_df, intersection_df, core_ca_df, core_planning_df

# - convert inputs from MSOA to ZonePfSH using proportions

def convert_msoa_to_zonepfsh(intersection_df, core_planning_df):

    #initialise dataframe to store converted data
    population_categories = core_planning_df['population'].unique()
    zonepfsh_numbers = intersection_df['ZonePfSH'].unique()
    zonepfsh_planning_df = pd.DataFrame(list(product(zonepfsh_numbers, population_categories)), columns=['ZonePfSH', 'Population'])
    for year in years:
        zonepfsh_planning_df[year] = 0

    # iterate through each row in the core_planning_df
    i=0
    for _, row in core_planning_df.iterrows():
        i += 1
        print(f"working on row {i}")
        msoa = row["msoa_zone_id"]
        population = row["population"]

        # determine how each msoa is split across the zonepfshs
        msoa_split = {}
        for _, r in intersection_df.iterrows():
            if r["MSOA11CD"] == msoa:
                msoa_split[r["ZonePfSH"]] = r["Proportion"]

        # add the proportion of the msoa's population to the corresponding zonepfsh
        
        for zonepfsh, proportion in msoa_split.items():
            for year in years:
                zonepfsh_planning_df.loc[
                    (zonepfsh_planning_df["ZonePfSH"] == zonepfsh) &
                    (zonepfsh_planning_df["Population"] == population),
                    year
                ] += row[year] * proportion

    print(zonepfsh_planning_df)
    return zonepfsh_planning_df


# - aggregate data up to district level


# - format outputs into correct structure for inputting to step 3


# - output final csvs: 1_high-core, 2_low-core, 3_behavioural-core

if __name__ == "__main__":
    # check inputs
    check_inputs(input_dir)

    # read input files
    geodef_df, intersection_df, core_ca_df, core_planning_df = read_input_files(input_dir)


    convert_msoa_to_zonepfsh(intersection_df, core_planning_df)

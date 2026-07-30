import csv
from itertools import product
import pandas as pd
import os
import tabulate

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
    print("input files read successfully")

    return geodef_df, intersection_df, core_ca_df, core_planning_df

# - create proportion split lookup for MSOA to ZonePfSH

def define_splits(intersection_df):
    msoa_zonepfsh_lookup = {}
    for _, row in intersection_df.iterrows():
        msoa = row["MSOA11CD"]
        zonepfsh = row["ZonePfSH"]
        proportion = row["Proportion"]

        if msoa not in msoa_zonepfsh_lookup:
            msoa_zonepfsh_lookup[msoa] = {}
        msoa_zonepfsh_lookup[msoa][zonepfsh] = proportion
    print("MSOA to ZonePfSH lookup built successfully")
    #print(msoa_zonepfsh_lookup)

    return msoa_zonepfsh_lookup


# - convert inputs from MSOA to ZonePfSH using proportions

def convert_msoa_to_zonepfsh(msoa_zonepfsh_lookup, core_planning_df, intersection_df):

    #initialise dataframe to store converted data
    population_categories = core_planning_df['population'].unique()
    zonepfsh_numbers = intersection_df['ZonePfSH'].unique()
    zonepfsh_planning_df = pd.DataFrame(list(product(zonepfsh_numbers, population_categories)), columns=['ZonePfSH', 'Population'])
    for year in years:
        zonepfsh_planning_df[year] = 0.0

    # iterate through each row in the core_planning_df
    i=0
    for _, row in core_planning_df.iterrows():
        i += 1
        print(f"working on row {i}")
        msoa = row["msoa_zone_id"]
        population = row["population"]

    # retrieve split from msoa_zonepfsh_lookup
        if msoa in msoa_zonepfsh_lookup:
            splits = msoa_zonepfsh_lookup[msoa]
            for zonepfsh, proportion in splits.items():
                for year in years:
                    additional_population = float(row[year]) * float(proportion)
                    try:
                        zonepfsh_planning_df.loc[(zonepfsh_planning_df['ZonePfSH'] == zonepfsh) 
                                                 & (zonepfsh_planning_df['Population'] == population), year] += additional_population
                    except TypeError:
                        print(f"Type error encountered, value is {row[year]} and proportion is {proportion}")
                        

    print(zonepfsh_planning_df)
    return zonepfsh_planning_df


# - aggregate data up to district level

def aggregate_to_districts(zonepfsh_planning_df, geodef_df):
    zonepfsh_district_lookup = zip(geodef_df['Zone'], geodef_df['D30_Districts ID'])
    
    # initialise dataframe to store aggregated data
    district_numbers = geodef_df['D30_Districts ID'].unique()
    population_categories = zonepfsh_planning_df['Population'].unique() 
    zonepfsh_planning_districts_df = pd.DataFrame(list(product(district_numbers, population_categories)), columns=['District', 'Population'])
    for year in years:
        zonepfsh_planning_districts_df[year] = 0.0

    # iterate through each row in the zonepfsh_planning_df
    for _, row in zonepfsh_planning_df.iterrows():
        zonepfsh = row["ZonePfSH"]
        population = row["Population"]

        # retrieve district from zonepfsh_district_lookup
        district = geodef_df.loc[geodef_df['Zone'] == zonepfsh, 'D30_Districts ID'].values[0]

        for year in years:
            additional_population = float(row[year])
            zonepfsh_planning_districts_df.loc[(zonepfsh_planning_districts_df['District'] == district) 
                                                & (zonepfsh_planning_districts_df['Population'] == population), year] += additional_population

    print(zonepfsh_planning_districts_df)


# - format outputs into correct structure for inputting to step 3


# - output final csvs: 1_high-core, 2_low-core, 3_behavioural-core

if __name__ == "__main__":
    # check inputs
    check_inputs(input_dir)

    # read input files
    geodef_df, intersection_df, core_ca_df, core_planning_df = read_input_files(input_dir)

    msoa_zonepfsh_lookup = define_splits(intersection_df)
    zonepfsh_planning_df = convert_msoa_to_zonepfsh(msoa_zonepfsh_lookup, core_planning_df, intersection_df)
    aggregate_to_districts(zonepfsh_planning_df, geodef_df)

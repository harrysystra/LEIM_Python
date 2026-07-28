import csv
import pandas as pd
import os

years = [2019, 2026, 2031, 2036, 2041] # must be between 2019 and 2046 inclusive
scenarios = ['core', 'high', 'low', 'behavioural'] 

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
    core_ca_df = pd.read_csv(os.path.join(input_dir, 'ntem_8.0_Core_ca_data.csv'))
    core_planning_df = pd.read_csv(os.path.join(input_dir, 'ntem_8.0_Core_planning_data.csv'))

    print("Input files read successfully!")

    return geodef_df, intersection_df, core_ca_df, core_planning_df

# - convert inputs from MSOA to ZonePfSH using proportions



# - format data by scenario (core, high, low)


# - aggregate data up to district level


# - format outputs into correct structure for inputting to step 3


# - output final csvs: 1_high-core, 2_low-core, 3_behavioural-core

if __name__ == "__main__":
    # check inputs
    check_inputs(input_dir)

    # read input files
    geodef_df, intersection_df, core_ca_df, core_planning_df = read_input_files(input_dir)
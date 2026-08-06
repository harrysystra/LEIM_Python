import pandas as pd 
import os

#CONFIGURATION
max_iterations = 10
tolerance = 0.1

input_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step4\\Inputs'
output_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step4\\Outputs'

step2_output_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step2\\Outputs'

test_scenarios = ['Low', 'Behavioural', 'High']

year = "2031"

def transform_step2_inputs(input_dir,
                test_scenario):
    test_scenario_co_df = pd.read_csv(os.path.join(input_dir, f'{test_scenario}_co.csv'))
    core_scenario_co_df = pd.read_csv(os.path.join(input_dir, f'Core_co.csv'))

    test_scenario_co_df = test_scenario_co_df.drop(columns=[col for col in test_scenario_co_df.columns if '20' in col and year not in col])
    core_scenario_co_df = core_scenario_co_df.drop(columns=[col for col in core_scenario_co_df.columns if '20' in col and year not in col])

    print(test_scenario_co_df.head())
    print(core_scenario_co_df.head())

    return test_scenario_co_df, core_scenario_co_df

def read_avzn_inputs():
    pass

def starting_point():
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
    transform_step2_inputs(input_dir, 'High')
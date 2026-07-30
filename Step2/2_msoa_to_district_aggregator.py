from itertools import product
import pandas as pd
import os
from rich.progress import track

years = ['2019', '2026', '2031', '2036', '2046'] # must be between 2019 and 2046 inclusive
scenarios = ['Core', 'High'] # leave alone unless adding new scenarios

input_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step2\\Inputs'
output_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step2\\Outputs'


inputs = {'geodef': [
    'geodef_GISCorrect.csv', 
],
'Intersection': [
    'Intersection_MSOA-TfSH_Prop.csv'
],
'Core': [
    'ntem_8.0_Core_ca_data.csv',
    'ntem_8.0_Core_planning_data.csv'
],
'High': [
    'ntem_8.0_High_ca_data.csv',
    'ntem_8.0_High_planning_data.csv'
],
'Low': [
    'ntem_8.0_Low_ca_data.csv',
    'ntem_8.0_Low_planning_data.csv'
],
'Behavioural': [
    'ntem_8.0_Behavioural_ca_data.csv',
    'ntem_8.0_Behavioural_planning_data.csv'
]}


def check_inputs(input_dir, scenarios, inputs):
    """Checks if input directory and input files exist for each scenario"""

    if not os.path.exists(input_dir):
        raise ValueError("Input directory does not exist")

    for scenario in scenarios + ['geodef'] + ['Intersection']:
        for input_file in inputs[scenario]:
            if not os.path.exists(os.path.join(input_dir, input_file)):
                raise ValueError(f"Input file {input_file} does not exist in the input directory")
        


def read_input_files(input_dir, scenario):
    """Reads input files and returns as DataFramas for a given scenario"""

    geodef_df = pd.read_csv(os.path.join(input_dir, 'geodef_GISCorrect.csv'))

    for filename in inputs[scenario]:
        if 'planning' in filename:
            planning_df = pd.read_csv(os.path.join(input_dir, filename))[['msoa_zone_id', 'population'] + years]
        elif 'ca_data' in filename:
            ca_df = pd.read_csv(os.path.join(input_dir, filename))[['msoa_zone_id', 'car_ownership'] + years]
    return geodef_df, planning_df, ca_df



def define_splits(inputs):
    """Reads the Intersection file and creates a lookup for proportional splits between 
    TfSH zones and MSOA"""

    filename = inputs['Intersection'][0]
    print(os.path.join(input_dir, filename))
    intersection_df = pd.read_csv(os.path.join(input_dir, filename))
    intersection_df.rename(columns={'Proportions MSOA/Zones': 'Proportion'}, inplace=True)

    msoa_zonepfsh_lookup = {}
    
    for _, row in track(
        intersection_df.iterrows(),
        total=len(intersection_df),
        description="Building MSOA/ZonePfSH lookup"
    ):
        msoa = row["MSOA11CD"]
        zonepfsh = row["ZonePfSH"]
        proportion = row["Proportion"]

        if msoa not in msoa_zonepfsh_lookup:
            msoa_zonepfsh_lookup[msoa] = {}
        msoa_zonepfsh_lookup[msoa][zonepfsh] = proportion

    return msoa_zonepfsh_lookup, intersection_df



def convert_population_to_zonepfsh(msoa_zonepfsh_lookup: pd.DataFrame,
                              working_data: pd.DataFrame, 
                              intersection_df: pd.DataFrame):

    zonepfsh_numbers = intersection_df['ZonePfSH'].unique()

    population_categories = working_data['population'].unique()
    planning_df = pd.DataFrame(list(product(zonepfsh_numbers, population_categories)), columns=['ZonePfSH', 'Population'])
    for year in years:
        planning_df[year] = 0.0

    for _, row in track(working_data.iterrows(),
                        total=len(working_data),
                        description="Allocating population to TfSH Zones..."):
        msoa = row["msoa_zone_id"]
        population = row["population"]

        if msoa in msoa_zonepfsh_lookup:
            splits = msoa_zonepfsh_lookup[msoa]
            for zonepfsh, proportion in splits.items():
                for year in years:
                    additional_population = float(row[year]) * float(proportion)
                    try:
                        planning_df.loc[(planning_df['ZonePfSH'] == zonepfsh) 
                                                & (planning_df['Population'] == population), year] += additional_population
                    except TypeError:
                        print(f"Type error encountered, value is {row[year]} and proportion is {proportion}")
                            
    return planning_df



def convert_car_to_zonepfsh(msoa_zonepfsh_lookup: pd.DataFrame,
                              working_data: pd.DataFrame, 
                              intersection_df: pd.DataFrame):

    zonepfsh_numbers = intersection_df['ZonePfSH'].unique()

    car_categories = working_data['car_ownership'].unique()
    car_df = pd.DataFrame(list(product(zonepfsh_numbers, car_categories)), columns=['ZonePfSH', 'CarOwnership'])
    for year in years:
        car_df[year] = 0.0

    for _, row in track(working_data.iterrows(),
                        total=len(working_data),
                        description="Allocating car ownership figures to TfSH Zones..."):
        msoa = row["msoa_zone_id"]
        car = row["car_ownership"]

        if msoa in msoa_zonepfsh_lookup:
            splits = msoa_zonepfsh_lookup[msoa]
            for zonepfsh, proportion in splits.items():
                for year in years:
                    additional_cars = float(row[year]) * float(proportion)
                    try:
                        car_df.loc[(car_df['ZonePfSH'] == zonepfsh) 
                                                & (car_df['CarOwnership'] == car), year] += additional_cars
                    except TypeError:
                        print(f"Type error encountered, value is {row[year]} and proportion is {proportion}")
                        
    return car_df



def aggregate_population_to_districts(zonepfsh_level_data: pd.DataFrame, 
                           geodef_df: pd.DataFrame):

    district_numbers = geodef_df['D30_Districts ID'].unique()

    population_categories = zonepfsh_level_data['Population'].unique() 
    zonepfsh_planning_districts_df = pd.DataFrame(list(product(district_numbers, population_categories)), columns=['District', 'Population'])
    for year in years:
        zonepfsh_planning_districts_df[year] = 0.0

    for _, row in track(zonepfsh_level_data.iterrows(),
                        total=len(zonepfsh_level_data),
                        description="Aggregating ZonePfSH population data by D30 District"):
        zonepfsh = row["ZonePfSH"]
        population = row["Population"]

        district = geodef_df.loc[geodef_df['Zone'] == zonepfsh, 'D30_Districts ID'].values[0]

        for year in years:
            additional_population = float(row[year])
            zonepfsh_planning_districts_df.loc[(zonepfsh_planning_districts_df['District'] == district) 
                                                & (zonepfsh_planning_districts_df['Population'] == population), year] += additional_population
    return zonepfsh_planning_districts_df



def aggregate_car_to_districts(zonepfsh_level_data: pd.DataFrame, 
                           geodef_df: pd.DataFrame):

    district_numbers = geodef_df['D30_Districts ID'].unique()
    car_categories = zonepfsh_level_data['CarOwnership'].unique() 
    zonepfsh_car_districts_df = pd.DataFrame(list(product(district_numbers, car_categories)), columns=['District', 'CarOwnership'])
    for year in years:
        zonepfsh_car_districts_df[year] = 0.0
    
    for _, row in track(zonepfsh_level_data.iterrows(),
                        total=len(zonepfsh_level_data),
                        description="Aggregating ZonePfSH car ownership data by D30 District"):
        zonepfsh = row["ZonePfSH"]
        car = row["CarOwnership"]

        district = geodef_df.loc[geodef_df['Zone'] == zonepfsh, 'D30_Districts ID'].values[0]
    
        for year in years:
            additional_cars = float(row[year])
            zonepfsh_car_districts_df.loc[(zonepfsh_car_districts_df['District'] == district) 
                                                & (zonepfsh_car_districts_df['CarOwnership'] == car), year] += additional_cars
    return zonepfsh_car_districts_df



def export_df_as_csv(csv_name: str, table: pd.DataFrame, output_folder: str):
    output_path = os.path.join(output_folder, csv_name)
    table.to_csv(output_path, index=None, header=True)



def run_process_for_selected_scenarios(input_dir,
                                       output_dir,
                                       scenarios):
    
    """Orchestrator function: runs process for all configured scenarios and years"""

    check_inputs(input_dir, scenarios, inputs)

    msoa_zonepfsh_lookup, intersection_df = define_splits(inputs=inputs)

    for scenario in scenarios:
        print(f"WORKING ON SCENARIO: {scenario}")
        geodef_df, planning_df, ca_df = read_input_files(input_dir=input_dir,
                                                                   scenario=scenario)
        planning = convert_population_to_zonepfsh(msoa_zonepfsh_lookup=msoa_zonepfsh_lookup,
                                working_data=planning_df,
                                intersection_df=intersection_df
                                )
        planning_district_level = aggregate_population_to_districts(zonepfsh_level_data=planning,
                                                         geodef_df=geodef_df)
        planning_csv_filename = scenario + "_planning.csv"

        try: 
            export_df_as_csv(csv_name=planning_csv_filename, 
                            table=planning_district_level,
                            output_folder=output_dir)
            print(f"{planning_csv_filename} exported successfully!")
        except:
            print(f"Export of file {planning_csv_filename} failed.")
        
        car_ownership = convert_car_to_zonepfsh(msoa_zonepfsh_lookup=msoa_zonepfsh_lookup,
                                working_data=ca_df,
                                intersection_df=intersection_df
                                )
        car_ownership_district_level = aggregate_car_to_districts(zonepfsh_level_data=car_ownership,
                                                              geodef_df=geodef_df)
        car_ownership_csv_filename = scenario + "_car_ownership.csv"

        try:
            export_df_as_csv(csv_name=car_ownership_csv_filename,
                            table=car_ownership_district_level,
                            output_folder=output_dir)
            print(f"{car_ownership_csv_filename} exported successfully!")
        except:
            print(f"Export of file {car_ownership_csv_filename} failed.")

        

if __name__ == "__main__":

    run_process_for_selected_scenarios(input_dir=input_dir,
                                       output_dir=output_dir,
                                       scenarios=scenarios)
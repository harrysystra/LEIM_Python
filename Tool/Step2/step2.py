from itertools import product
import pandas as pd
import os
from rich.progress import track

years = ['2019', '2026', '2031', '2036', '2046'] # can include any years included in input files (between 2019 and 2046 inclusive)
scenarios = ['Core', 'Low', 'Behavioural','High'] # any combination of: 'Core', 'Low', 'High', 'Behavioural'
#CORE MUST BE LISTED FIRST

input_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Inputs\\Step2'
output_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Outputs\\2_Extended_NTEM_Targets'
step_4_input_dir = 'C:\\Users\\hmackenzie\\OneDrive - SystraGroup\\LEIM_Python\\New_Tool\\Step4\\Inputs'


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
    """Checks if input directory and input files exist for each scenario
    Args:
        - input_dir: full path to the location of the input CSVs
        - scenarios: list containing any combination of the following strings: 'Core', 'High', 'Low', 'Behavioural'
        - inputs: dictionary containing the input files for each scenario
            """

    if not os.path.exists(input_dir):
        raise ValueError("Input directory does not exist")

    if scenarios[0] != 'Core':
        raise ValueError("Core scenario must be listed first in the scenarios list")

    for scenario in scenarios + ['geodef'] + ['Intersection']:
        for input_file in inputs[scenario]:
            if not os.path.exists(os.path.join(input_dir, input_file)):
                raise ValueError(f"Input file {input_file} does not exist in the input directory")
        


def read_input_files(input_dir, scenario):
    """Reads input files and returns as DataFramas for a given scenario
    Args:
        - input_dir: full path to the location of the input CSVs
        - scenario: string containing the scenario for which to read input files
    Returns:
        - geodef_df: DataFrame containing geodef data
        - planning_df: DataFrame containing planning data
        - ca_df: DataFrame containing community activity data"""

    geodef_df = pd.read_csv(os.path.join(input_dir, 'geodef_GISCorrect.csv'))

    for filename in inputs[scenario]:
        if 'planning' in filename:
            planning_df = pd.read_csv(os.path.join(input_dir, filename))[['msoa_zone_id', 'population'] + years]
        elif 'ca_data' in filename:
            ca_df = pd.read_csv(os.path.join(input_dir, filename))[['msoa_zone_id', 'car_ownership'] + years]
    return geodef_df, planning_df, ca_df



def define_splits(inputs):
    """Reads the Intersection file and creates a lookup for proportional splits between 
    TfSH zones and MSOA
    Args:
        - inputs: dictionary containing the input files for each scenario
    Returns:
        - msoa_zonepfsh_lookup: dictionary containing the proportional splits between TfSH zones and MSOA
        - intersection_df: DataFrame containing the intersection data"""

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
    """
    Takes population data given on a per-MSOA basis, and allocates the data to ZonePfSH zones.
    Utilises a lookup created in the define_splits function to define the relationships between ZonePfSH zones and MSOA. 
    Args:
        - msoa_zonepfsh_lookup: DataFrame containing information on MSOA to model zone relationships derived rrom the intersection file
        - working_data: DataFrame containing population data per MSOA
        - intersection_df: DataFrame containing the proportion of MSOA population that is allocated to each ZonePfSH zone, derived from the intersection file
    Returns:
        - planning_df: DataFrame containing population data per ZonePfSH"""
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
    """
    Takes car ownership data given on a per-MSOA basis, and allocates the data to ZonePfSH zones.
    Utilises a lookup created in the define_splits function to define the relationships between ZonePfSH zones and MSOA. 
    Args:
        - msoa_zonepfsh_lookup: DataFrame containing information on MSOA to model zone relationships derived rrom the intersection file
        - working_data: DataFrame containing car ownership data per MSOA
        - intersection_df: DataFrame containing the proportion of MSOA population that is allocated to each ZonePfSH zone, derived from the intersection file
    Returns:
        - car_df: DataFrame containing car ownership data per ZonePfSH
    """
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
    """
    Aggregates population data from population-by-zone (ZonePfSH) up to population-by-district level (i.e. there are multiple zones per district).
    This calculation is based on the zones-to-districts relationships outlined in the geodef_GISCorrect.csv file. 
    Args:
        - zonepfsh_level_data: DataFrame containing population data per ZonePfSH
        - geodef_df: DataFrame containing zone to district allocations
    Returns:
        - zonepfsh_planning_districts_df: DataFrame containing population data per district
    """

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
    """
    Aggregates car ownership data from cars-by-zone (ZonePfSH) up to cars-by-district level (i.e. there are multiple zones per district).
    This calculation is based on the zones-to-districts relationships outlined in the geodef_GISCorrect.csv file. 
    Args:
        - zonepfsh_level_data: DataFrame containing car ownership data per ZonePfSH
        - geodef_df: DataFrame containing zone to district allocations
    Returns:
        - zonepfsh_car_districts_df: DataFrame containing car ownership data per district
    """

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
    """
    Exports df as a csv file and saves to output folder. 
    Args:
        - csv_name: desired filename for output
        - table: pandas DataFrame to convert to csv
        - output_folder: full path to desired output location
    """
    output_path = os.path.join(output_folder, csv_name)
    table.to_csv(output_path, index=None, header=True)



def subtract_dataframes(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    Subtracts the values of two dataframes with the same structure. 
    Args:
        - df1: pandas DataFrame to subtract from
        - df2: pandas DataFrame to subtract
    Returns:
        - result_df: pandas DataFrame containing the result of the subtraction
    """
    result_df = df1.copy()
    for year in years:
        result_df[year] = df1[year] - df2[year]
    return result_df


def run_step2(input_dir: str,
            output_dir: str,
            scenarios: list,
            selected_years: list):
    """
    Main Orchestrator Function: runs process for all configured scenarios and years. 
    To run the process, update the inputs and run this function. 

    Args:
        - input_dir: full path to the location of the input CSVs
        - output_dir: full path to the desired output location
        - scenarios: list containing any combination of:
          'Core', 'Low', 'High', 'Behavioural'
        - selected_years: list of years to export, e.g. [2019, 2026, 2031]
    """
    check_inputs(input_dir, scenarios, inputs)

    msoa_zonepfsh_lookup, intersection_df = define_splits(inputs=inputs)

    core_planning_district_level = None
    core_car_ownership_district_level = None

    for scenario in scenarios:
        print(f"WORKING ON SCENARIO: {scenario}")

        geodef_df, planning_df, ca_df = read_input_files(
            input_dir=input_dir,
            scenario=scenario
        )

        planning = convert_population_to_zonepfsh(
            msoa_zonepfsh_lookup=msoa_zonepfsh_lookup,
            working_data=planning_df,
            intersection_df=intersection_df
        )

        planning_district_level = aggregate_population_to_districts(
            zonepfsh_level_data=planning,
            geodef_df=geodef_df
        )

        planning_csv_filename = scenario + "_planning.csv"

        try:
            export_df_as_csv(
                csv_name=planning_csv_filename,
                table=planning_district_level,
                output_folder=output_dir
            )
            print(f"{planning_csv_filename} exported successfully!")
        except Exception as e:
            print(f"Export of file {planning_csv_filename} failed: {e}")

        car_ownership = convert_car_to_zonepfsh(
            msoa_zonepfsh_lookup=msoa_zonepfsh_lookup,
            working_data=ca_df,
            intersection_df=intersection_df
        )

        car_ownership_district_level = aggregate_car_to_districts(
            zonepfsh_level_data=car_ownership,
            geodef_df=geodef_df
        )

        car_ownership_csv_filename = scenario + "_co.csv"

        try:
            export_df_as_csv(
                csv_name=car_ownership_csv_filename,
                table=car_ownership_district_level,
                output_folder=output_dir
            )
            export_df_as_csv(
                csv_name=car_ownership_csv_filename,
                table=car_ownership_district_level,
                output_folder=step_4_input_dir
            )
            print(f"{car_ownership_csv_filename} exported successfully!")
        except Exception as e:
            print(f"Export of file {car_ownership_csv_filename} failed: {e}")

        # Store Core tables in memory for later comparisons
        if scenario == "Core":
            core_planning_district_level = planning_district_level.copy()
            core_car_ownership_district_level = car_ownership_district_level.copy()

        if scenario != "Core":
            # fallback if Core wasn't run earlier in the same call
            if core_planning_district_level is None:
                core_planning_district_level = pd.read_csv(
                    os.path.join(output_dir, "Core_planning.csv")
                )
            if core_car_ownership_district_level is None:
                core_car_ownership_district_level = pd.read_csv(
                    os.path.join(output_dir, "Core_co.csv")
                )

            planning_difference = subtract_dataframes(
                df1=planning_district_level,
                df2=core_planning_district_level
            )
            planning_difference_csv_filename = scenario + "_planning_difference.csv"

            try:
                export_df_as_csv(
                    csv_name=planning_difference_csv_filename,
                    table=planning_difference,
                    output_folder=output_dir
                )
                print(f"{planning_difference_csv_filename} exported successfully!")
            except Exception as e:
                print(f"Export of file {planning_difference_csv_filename} failed: {e}")

            car_ownership_difference = subtract_dataframes(
                df1=car_ownership_district_level,
                df2=core_car_ownership_district_level
            )
            car_ownership_difference_csv_filename = scenario + "_co_difference.csv"

            try:
                export_df_as_csv(
                    csv_name=car_ownership_difference_csv_filename,
                    table=car_ownership_difference,
                    output_folder=output_dir
                )
                print(f"{car_ownership_difference_csv_filename} exported successfully!")
            except Exception as e:
                print(f"Export of file {car_ownership_difference_csv_filename} failed: {e}")

            # Export individual population category comparison CSVs
            try:
                planning_categories = planning_district_level["Population"].dropna().unique().tolist()

                export_category_difference_csvs(
                    scenario_df=planning_district_level,
                    core_df=core_planning_district_level,
                    category_col="Population",
                    categories=planning_categories,
                    selected_years=selected_years,
                    scenario=scenario,
                    prefix="planning",
                    output_dir=output_dir
                )
            except Exception as e:
                print(f"Export of planning category difference CSVs for {scenario} failed: {e}")

            # Export individual car ownership category comparison CSVs
            try:
                car_ownership_categories = ["no_car", "1_car", "2_cars", "3+_cars"]

                export_category_difference_csvs(
                    scenario_df=car_ownership_district_level,
                    core_df=core_car_ownership_district_level,
                    category_col="CarOwnership",
                    categories=car_ownership_categories,
                    selected_years=selected_years,
                    scenario=scenario,
                    prefix="co",
                    output_dir=output_dir
                )
            except Exception as e:
                print(f"Export of car ownership category difference CSVs for {scenario} failed: {e}")
                

def export_category_difference_csvs(scenario_df: pd.DataFrame,
                                    core_df: pd.DataFrame,
                                    category_col: str,
                                    categories: list,
                                    selected_years: list,
                                    scenario: str,
                                    prefix: str,
                                    output_dir: str):
    """
    Export one CSV per category containing scenario minus core, with columns:
    District, Sum of <year1>, Sum of <year2>, ...

    Args:
        scenario_df: district-level dataframe for current scenario
        core_df: district-level dataframe for Core
        category_col: category column name, e.g. 'Population' or 'CarOwnership'
        categories: list of category values
        selected_years: list like [2019, 2026, 2031]
        scenario: scenario name, e.g. 'High'
        prefix: 'planning' or 'co'
        output_dir: export folder
    """
    year_cols = [str(y) for y in selected_years]

    for category in categories:
        scen_cat = scenario_df[scenario_df[category_col] == category].copy()
        core_cat = core_df[core_df[category_col] == category].copy()

        scen_cat = scen_cat[["District"] + year_cols]
        core_cat = core_cat[["District"] + year_cols]

        merged = scen_cat.merge(
            core_cat,
            on="District",
            how="outer",
            suffixes=("_scenario", "_core")
        ).fillna(0)

        result = pd.DataFrame()
        result["District"] = merged["District"]

        for y in year_cols:
            result[f"Sum of {y}"] = merged[f"{y}_scenario"] - merged[f"{y}_core"]

        safe_category = str(category).replace("+", "plus").replace(" ", "_")
        csv_name = f"{scenario}_{prefix}_{safe_category}_difference.csv"

        export_df_as_csv(
            csv_name=csv_name,
            table=result,
            output_folder=output_dir
        )

        print(f"{csv_name} exported successfully!")



if __name__ == "__main__":

    # run the proces and export as CSVs for each scenario
    run_step2(input_dir=input_dir,
                output_dir=output_dir,
                scenarios=scenarios,
                selected_years=years)
import yaml
from Tool.Step2.step2 import run_step2
from Tool.Step3.step3 import run_step3
from Tool.Step4.step4 import run_step4

with open("config.yaml", "r") as f:
    config = yaml.full_load(f)

def run_tool():

    if config['general']['run_step2']:

        input_directory = config['step2_config']['input_directory']
        output_directory = config['step2_config']['output_directory']
        years = config['step2_config']['years']
        scenarios = config['step2_config']['scenarios']

        run_step2(input_dir=input_directory,
                output_dir=output_directory,
                scenarios=scenarios,
                selected_years=years) 


    if config['general']['run_step3']:
        input_directory = config['step3_config']['input_directory']
        output_directory = config['step3_config']['output_directory']
        step2_output_directory = config['step2_config']['output_directory']
        years = config['step3_config']['years']
        scenarios = config['step3_config']['scenarios']
        geodef_path = config['step3_config']['geodef_path']
        activity_class_path = config['step3_config']['activity_class_path']
        export_csv = config['step3_config']['export_csv']
        export_dat = config['step3_config']['export_dat']

        run_step3(input_dir=input_directory,
        output_dir=output_directory,
        geodef_path = geodef_path,
        scenarios=scenarios,
        years=years,
        activity_class_path=activity_class_path,
        export_csv=export_csv,
        export_dat=export_dat) 



    if config['general']['run_step4']:
        input_directory = config['step4_config']['input_directory']
        output_directory = config['step4_config']['output_directory']
        years = config['step4_config']['years']
        max_iterations = config['step4_config']['max_iterations']
        step2_input_directory = config['step2_config']['input_directory']
        step2_output_directory = config['step2_config']['output_directory']
        scenarios = config['step4_config']['scenarios']

        run_step4(input_dir=input_directory,
                  iter_limit=max_iterations,
                  output_dir=output_directory,
                  years=years,
                  step2_input_dir=step2_input_directory,
                  scenarios=scenarios,
                  step2_output_dir=step2_output_directory)
        

if __name__ == "__main__":
    run_tool()
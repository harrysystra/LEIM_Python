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
        years = config['general']['years']
        scenarios = config['general']['scenarios']
        geodef_path = config['general']['geodef_path']
        activity_class_path = config['step3_config']['activity_class_path']
        export_csv = config['step3_config']['export_csv']
        export_dat = config['step3_config']['export_dat']
        test_code = config['general']['test_code']

        run_step3(input_dir=input_directory,
        output_dir=output_directory,
        geodef_path = geodef_path,
        scenarios=scenarios,
        years=years,
        activity_class_path=activity_class_path,
        export_csv=export_csv,
        export_dat=export_dat,
        test_code = test_code) 



    if config['general']['run_step4']:
        input_directory = config['step4_config']['input_directory']
        output_directory = config['step4_config']['output_directory']
        years = config['general']['years']
        max_iterations = config['step4_config']['max_iterations']
        step2_input_directory = config['step2_config']['input_directory']
        step2_output_directory = config['step2_config']['output_directory']
        step3_output_directory = config['step3_config']['output_directory']
        scenarios = config['general']['scenarios']
        test_code = config['general']['test_code']
        geodef_path = config['general']['geodef_path']

        run_step4(input_dir=input_directory,
                  iter_limit=max_iterations,
                  output_dir=output_directory,
                  years=years,
                  step2_input_dir=step2_input_directory,
                  scenarios=scenarios,
                  step2_output_dir=step2_output_directory,
                  test_code=test_code,
                  step3_output_dir=step3_output_directory,
                  geodef_path=geodef_path)
        

if __name__ == "__main__":
    run_tool()
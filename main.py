import yaml
from Tool.Step2.step2 import run_step2
#from Tool.Step3.step3 import run_step3
#from Tool.Step4.step4 import run_step4

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

if __name__ == "__main__":
    run_tool()
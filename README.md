Before running the tool, you need to check:

1. All inputs are in the Inputs folder
2. CONFIG.yaml contains the correct configuration for your run 

If both of these are set up correctly, then all you need to do is run main.py.

You don't need to change anything inside of main.py or any other .py files in order to configure the run. 


How it Works:

Step 1: Mysterious, doesn't exist... :)
Step 2: Takes the MSOA level NTEM data and aggregates it up to Zone level data & outputs in format to be used as inputs in subsuquent steps. 
Step 3: Takes the Core AVZN and produces AVZN for configured scenarios using data from Step 2 
Step 4: Takes the Core COZN and produces COZN for configured scenarios using data from Step 2 


Output Formats:

Step 2: everything is .csv 
Step 3 and Step 4: .dat and optionally .csv format (choose to include or exclude in the CONFIG.yaml file)


Directory Structure:

For the tool to work, it is important that the directory structure remains consistend and the program can find the correct folders
It should look like this (if it doesn't then rename/create the necessary folders):

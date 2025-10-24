from datetime import datetime as dt
import os
import sys
import logging
import pandas as pd
import requests, zipfile, io, time
import datetime
'''
To load the surveys: 
at the top of the script, load this file, and then write:

    surveys, recoded_surveys = load_surveys(survey_dir)

    first_df = surveys['clinical_administered_data']
    subject_ids = first_df['SUBJECT_ID'].unique()


'''
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# Import custom scripts
repo_dir = os.path.basename(os.getcwd())
sys.path.append(repo_dir)

# Important: KEEP the datestr in the survey name! It's what the app uses to find the most recent downloaded survey
today = datetime.date.today()  
datestr=today.strftime('%b %d, %Y') 

def export_surveys(survey_id_dict, API_TOKEN, survey_dir, verbose=False, recoded=False):
    surveys = {}
    # Replace these with your actual credentials
    DATA_CENTER = 'yul1'  

    for survey_name in survey_id_dict:
        print(f"Exporting {survey_name}...")
        SURVEY_ID = survey_id_dict[survey_name]['SURVEY_ID']

        # Set up headers and URL
        BASE_URL = f"https://{DATA_CENTER}.qualtrics.com/API/v3/surveys/{SURVEY_ID}/export-responses/"
        HEADERS = {
            "Content-Type": "application/json",
            "X-API-TOKEN": API_TOKEN,
        }
        # Start the export
        response = requests.post(BASE_URL, headers=HEADERS, json={"format": "csv", "useLabels": "True"})
        if recoded==True:
                response = requests.post(BASE_URL, headers=HEADERS, json={"format": "csv", "useLabels": "False"})
        progress_id = response.json()["result"]["progressId"]

        # Wait for the export to be complete
        while True:
            check_url = BASE_URL + progress_id
            check_response = requests.get(check_url, headers=HEADERS)
            status = check_response.json()["result"]["status"]
            if status == "complete":
                file_id = check_response.json()["result"]["fileId"]
                break
            elif status == "failed":
                raise Exception("Export failed")
            time.sleep(2)

        # Download the file
        download_url = BASE_URL + f"{file_id}/file"
        download_response = requests.get(download_url, headers=HEADERS, stream=True)

        # Unzip and read the CSV into a DataFrame
        zip_file = zipfile.ZipFile(io.BytesIO(download_response.content))
        csv_file = zip_file.open(zip_file.namelist()[0])
        surveys[survey_name] = pd.read_csv(csv_file)

        if recoded == True:
             surveys[survey_name].to_csv(os.path.join(survey_dir, survey_name, f'{survey_name}_recoded_{datestr}.csv'))
        else:
            surveys[survey_name].to_csv(os.path.join(survey_dir, survey_name, f'{survey_name}_{datestr}.csv'))
        
        print(f'Saved  {survey_name} to {os.path.join(survey_dir, f'{survey_name}_{datestr}.csv')}')


    return surveys



# Dict of all the surveys you want to download
    # To add additional surveys, find survey ID by the URL for the survey you want
    # It will be something like https://rutgers.yul1.qualtrics.com/jfe/form/SV_0pQR9T8rGz1A2jk
    # where SV_0pQR9T8rGz1A2jk is the SURVEY_ID
survey_id_dict = {
    "clinical_administered_data":{
        "SURVEY_ID": "SV_6tBSwRN0CukilQG"
    },
    "clinical_self_report_data":{
        "SURVEY_ID": "SV_78QRYTSOnegCSjQ"
    },
    "mri_self_report_data":{
        "SURVEY_ID": "SV_0UqGfGjgsl2nklU"
    },
    "supplemental_self_report_data":{
        "SURVEY_ID": "SV_08nF8tsZ4NU0rWe"
    },
}



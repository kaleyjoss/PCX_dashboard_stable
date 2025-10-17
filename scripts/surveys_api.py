from datetime import datetime as dt
import os
import sys
import logging
import pandas as pd
import requests, zipfile, io, time
'''
To load the surveys: 
at the top of the script, load this file, and then write:

    surveys, recoded_surveys = load_surveys(surveys_dir)

    first_df = surveys['clinical_administered_data']
    subject_ids = first_df['SUBJECT_ID'].unique()


'''
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Import custom scripts
repo_dir = os.path.basename(os.getcwd())
sys.path.append(repo_dir)

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


def fetch_survey_df(SURVEY_ID, API_TOKEN, DATA_CENTER, recoded=False):
    BASE_URL = f"https://{DATA_CENTER}.qualtrics.com/API/v3/surveys/{SURVEY_ID}/export-responses/"
    HEADERS = {"Content-Type": "application/json", "X-API-TOKEN": API_TOKEN}

    payload = {"format": "csv", "useLabels": str(not recoded)}
    response = requests.post(BASE_URL, headers=HEADERS, json=payload)
    progress_id = response.json()["result"]["progressId"]

    # Poll for completion
    while True:
        check_response = requests.get(BASE_URL + progress_id, headers=HEADERS)
        status = check_response.json()["result"]["status"]
        if status == "complete":
            file_id = check_response.json()["result"]["fileId"]
            break
        elif status == "failed":
            raise Exception("Export failed")
        time.sleep(3)

    # Download and read CSV directly
    download_response = requests.get(BASE_URL + f"{file_id}/file", headers=HEADERS)
    with zipfile.ZipFile(io.BytesIO(download_response.content)) as zf:
        with zf.open(zf.namelist()[0]) as csvfile:
            df = pd.read_csv(csvfile)
    return df


SUBJECT_ID_PATTERN = r"^qual[rm]2\d{2}$"


def add_diagnoses_columns(surveys):
    """Add combined diagnosis columns to clinical_administered_data survey."""
    if "clinical_administered_data" not in surveys:
        logging.warning("No clinical_administered_data in surveys")
        return surveys

    df = surveys["clinical_administered_data"]

    prim_cols = ["SUBJECT_ID"] + [
        col for col in df if "primary_diagnoses" in col
    ]
    df["primary_diagnoses_all"] = (
        df[prim_cols].bfill(axis=1).iloc[:, 1:2]
    )

    other_cols = ["SUBJECT_ID"] + [
        col for col in df if "other_diagnoses" in col
    ]
    df["other_diagnoses_all"] = (
        df[other_cols].bfill(axis=1).iloc[:, 1:2]
    )

    surveys["clinical_administered_data"] = df
    return surveys

def load_surveys(surveys_dir):
    """Load and clean surveys + recoded_surveys."""

    surveys = {}
    recoded_surveys = {}
    API_TOKEN = '8d0zWNKj6WnY0kLjmoecUtwgacbwXBLgQmPT0PWZ'
    DATA_CENTER = 'yul1'  



    for root, dirs, files in os.walk(surveys_dir):
        for survey in survey_id_dict:
            SURVEY_ID = survey_id_dict[survey]["SURVEY_ID"]
            try:
                df = fetch_survey_df(SURVEY_ID, API_TOKEN, DATA_CENTER, recoded=False)
                rdf = fetch_survey_df(SURVEY_ID, API_TOKEN, DATA_CENTER, recoded=True)

                # clean SUBJECT_ID
                df["SUBJECT_ID"] = df["SUBJECT_ID"][2:]
                df["SUBJECT_ID"] = (
                    df["SUBJECT_ID"].astype(str).str.lower().str.replace("pc", "qual")
                )
                mask = df["SUBJECT_ID"].str.strip().str.match(SUBJECT_ID_PATTERN, na=False)
                skipped = df.loc[~mask, "SUBJECT_ID"].tolist()
                if skipped:
                    logging.info(f"{survey} skipped SUBJECT_IDs: {skipped}")
                df = df.loc[mask].copy()

                df[str(survey)] = df["StartDate"] #indicator column of date completed for once merged
                surveys[survey] = df

                rdf["SUBJECT_ID"] = rdf["SUBJECT_ID"][2:]
                rdf["SUBJECT_ID"] = (
                    rdf["SUBJECT_ID"].astype(str).str.lower().str.replace("pc", "qual")
                )
                mask = rdf["SUBJECT_ID"].str.strip().str.match(SUBJECT_ID_PATTERN, na=False)
                rdf = rdf.loc[mask].copy()
                rdf[str(survey)] = rdf["StartDate"] #indicator column of date completed for once merged
                recoded_surveys[survey] = rdf
                    
            except Exception as e:
                logging.warning(f"Skipping {survey}, error: {e}")
                continue

    surveys = add_diagnoses_columns(surveys)
    recoded_surveys = add_diagnoses_columns(recoded_surveys)

    return surveys, recoded_surveys


from datetime import datetime as dt
import os
import sys
import logging
import pandas as pd


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


def extract_survey_date(filename: str):
    """
    Extracts a survey date from a filename of the form '..._<Month Day, Year>.csv'
    Example: 'survey_results_Sep 06, 2025.csv' → datetime(2025, 9, 6)
    """
    try:
        # Grab the last part after the last underscore, before the extension
        datestr = filename.split('_')[-1].split('.')[0]
        return dt.strptime(datestr, '%b %d, %Y')
    except Exception:
        return None
    
def get_most_recent_survey(directory, recoded=False):
    # Allowed Excel extensions
    extensions = (".csv", ".xls", ".xlsx")
    filenames = [f for f in os.listdir(directory) if f.endswith(extensions)]
    if recoded==True:
        filenames = [f for f in filenames if 'recoded' in f]
    else:
        filenames = [f for f in filenames if not 'recoded' in f]
    
    # List Excel files with their sizes
    dates = []
    for filename in filenames:

        survey_date = extract_survey_date(filename)
        if survey_date is not None:
            dates.append({'filename': filename, 'date': survey_date})
            

    if len(dates) > 0:
        dates.sort(key=lambda file: file['date'], reverse=True)
        print(f'Most recent survey: {dates[0]['filename']}')
        return os.path.join(directory, dates[0]['filename'])
    
    
    return None



# constants
SURVEY_NAMES = [
    "clinical_administered_data",
    "clinical_self_report_data",
    "mri_self_report_data",
    "supplemental_self_report_data",
]

subsurvey_key = {
    "panss": "clinical_administered_data",
    "madrs": "clinical_administered_data",
    "ymrs": "clinical_administered_data",
    "bprs": "clinical_administered_data",
    "cssrs": "clinical_administered_data",
}

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

    for root, dirs, files in os.walk(surveys_dir):
        for survey in SURVEY_NAMES:
            if survey not in dirs:
                continue

            survey_dir = os.path.join(root, survey)
            try:
                filepath = get_most_recent_survey(survey_dir)
                filepath_recoded = get_most_recent_survey(survey_dir, recoded=True)

                df = pd.read_csv(filepath)
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

                rdf = pd.read_csv(filepath_recoded)
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


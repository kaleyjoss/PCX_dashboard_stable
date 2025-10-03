from datetime import datetime as dt
import os
import sys
import logging
import pandas as pd


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Import custom scripts
repo_dir = os.path.basename(os.getcwd())
sys.path.append(repo_dir)
from scripts.utils import extract_survey_date, get_most_recent_survey

# folder where your fmriprep reports live
REPORTS_DIR = os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR/PCX/fmriprep_reports')
tracker_df=pd.read_excel(os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Subject_tracker_PCR.xlsx'), sheet_name='tracker')


survey_names = ['clinical_administered_data','clinical_self_report_data',
                     'mri_self_report_data','supplemental_self_report_data']
subsurvey_key = {
    'panss': 'clinical_administered_data',
    'madrs': 'clinical_administered_data',
    'ymrs': 'clinical_administered_data',
    'bprs': 'clinical_administered_data',
    'cssrs': 'clinical_administered_data',

}

subject_id_pattern = r"^qual[rm]2\d{2}$"

surveys={}
recoded_surveys={}
filepath=None
for root, dirs, files in os.walk(surveys_dir):
	for survey in survey_names: 
		if survey in dirs: 
			surveys[survey] = []
			survey_dir = os.path.join(root, survey)
			try:
				filepath = get_most_recent_survey(survey_dir)
				filepath_recoded = get_most_recent_survey(survey_dir, recoded=True)
			except Exception as e:
				print(e)
			if filepath is not None:
				surveys[survey] = pd.read_csv(filepath)
				surveys[survey]['SUBJECT_ID'] = surveys[survey]['SUBJECT_ID'][2:] # skip the question and the {} column
				surveys[survey]['SUBJECT_ID'] = surveys[survey]['SUBJECT_ID'].str.lower()
				surveys[survey]['SUBJECT_ID'] = surveys[survey]['SUBJECT_ID'].str.replace('pc','qual')

				mask = surveys[survey]['SUBJECT_ID'].astype(str).str.strip().str.match(subject_id_pattern, na=False) # boolean mask for valid subject IDs 
				valid_df = surveys[survey][mask] # keep only matching
				# print skipped subject IDs
				skipped = surveys[survey][~mask]
				print(f"{survey} Skipped rows:\n",skipped['SUBJECT_ID'].tolist())
				surveys[survey] = valid_df

				surveys[survey][survey] = surveys[survey]['StartDate']
				surveys[survey]['SUBJECT_ID'] = surveys[survey]['SUBJECT_ID'].str.lower()

				surveys[survey] = surveys[survey]
	
				recoded_surveys[survey]=pd.read_csv(filepath_recoded)
				recoded_surveys[survey]['SUBJECT_ID'] = recoded_surveys[survey]['SUBJECT_ID'][2:] # skip the question and the {} column
				recoded_surveys[survey]['SUBJECT_ID'] = recoded_surveys[survey]['SUBJECT_ID'].str.lower()
				recoded_surveys[survey]['SUBJECT_ID'] = recoded_surveys[survey]['SUBJECT_ID'].str.replace('pc','qual')
				mask = recoded_surveys[survey]['SUBJECT_ID'].astype(str).str.match(subject_id_pattern, na=False) # boolean mask for valid subject IDs 
				valid_df = recoded_surveys[survey][mask] # keep only matching
				recoded_surveys[survey] = valid_df
				recoded_surveys[survey][str(survey)] = recoded_surveys[survey]['StartDate']
				recoded_surveys[survey] = recoded_surveys[survey]


prim_diagnoses_cols = ['SUBJECT_ID']+[col for col in surveys['clinical_administered_data'] if 'primary_diagnoses' in col]
surveys['clinical_administered_data']['primary_diagnoses_all'] = surveys['clinical_administered_data'][prim_diagnoses_cols].bfill(axis=1).iloc[:, 1:2]
other_diagnoses_cols = ['SUBJECT_ID']+[col for col in surveys['clinical_administered_data'] if 'other_diagnoses' in col]
surveys['clinical_administered_data']['other_diagnoses_all'] = surveys['clinical_administered_data'][other_diagnoses_cols].bfill(axis=1).iloc[:, 1:2]


first_df = surveys['clinical_administered_data']
subject_ids = first_df['SUBJECT_ID'].unique()

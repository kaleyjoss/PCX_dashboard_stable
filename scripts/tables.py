import logging
from dash import Dash, _dash_renderer, dash_table
from datetime import datetime as dt
from datetime import timedelta
import numpy as np

survey_cols = [
    "SUBJECT_ID",'SITE_ID','primary_diagnoses_all','other_diagnoses_all',
    'clinical_administered_data', 'mri_self_report_data','supplemental_self_report_data', 
    'MADRS_category','YMRS_category', 'PANSS_Positive_Category','PANSS_Negative_Category','PANSS_General_Category','PANSS_Total_category',
	"sex","age", "ethnic","racial","place_birth", 'name_meds','purpose_meds','panss_total', 'panss_p_total','panss_n_total','panss_g_total', 'bprs_total','ymrs_total','madrs_total',]

display_survey_cols = [col for col in survey_cols if 'total' not in col and 'Category' not in col and 'supplemental' not in col]

two_weeks_ago = dt.now() - timedelta(weeks=2)
today_str = dt.now().strftime('%Y-%m-%d')
two_weeks_ago_str = two_weeks_ago.strftime('%Y-%m-%d')

def render_demographic_df(df, cols):
    if 'SUBJECT_ID' not in cols:
        cols = cols + ['SUBJECT_ID']
    non_present_cols = [col for col in cols if col not in df.columns]
    if len(non_present_cols)>0:
        cols = [col for col in cols if col in df.columns]
        logging.warning(f'Was not able to find these cols in the table: {non_present_cols}. Using {cols}')
    survey_df = df[cols]

    return dash_table.DataTable(
        data=survey_df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in survey_df.columns],
        css=[{
            "selector": ".dash-spreadsheet td div",
            "rule": """
                line-height: 20px;
                max-height: none; min-height: 20px; height: auto;
                display: block;
                white-space: normal;
                overflow-y: visible;
            """
            }],
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in survey_df.to_dict('records')
        ],
        tooltip_duration=None,
        style_cell={
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "fontFamily": "Arial, sans-serif",
            "fontSize": "12px",
            "padding": "8px"
        },
        style_header={
            "backgroundColor": "#AAD5F2",
            "fontWeight": "bold"
        },


        style_data_conditional=[
            {
                "if": {
                    "filter_query": f"{{mri_self_report_data}} >= '{two_weeks_ago_str}'",
                    "column_id": "mri_self_report_data"
                },
                "backgroundColor": "#f0f2f6",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{clinical_administered_data}} >= '{two_weeks_ago_str}'",
                    "column_id": "clinical_administered_data"
                },
                "backgroundColor": "#f0f2f6",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{MADRS_category}} contains 'Mild'",
                    "column_id": "MADRS_category"
                },
                "backgroundColor": "#FFE0E0",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{MADRS_category}} contains 'Moderate'",
                    "column_id": "MADRS_category"
                },
                "backgroundColor": "#FFBABA",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{MADRS_category}} contains 'Severe'",
                    "column_id": "MADRS_category"
                },
                "backgroundColor": "#FF7575",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{YMRS_category}} contains 'Mild'",
                    "column_id": "YMRS_category"
                },
                "backgroundColor": "#FFE0E0",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{YMRS_category}} contains 'Moderate'",
                    "column_id": "YMRS_category"
                },
                "backgroundColor": "#FFBABA",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{YMRS_category}} contains 'Severe'",
                    "column_id": "YMRS_category"
                },
                "backgroundColor": "#FF7575",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{YMRS_category}} contains 'Severe'",
                    "column_id": "YMRS_category"
                },
                "backgroundColor": "#FF7575",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{PANSS_Total_category}} contains 'Mild'",
                    "column_id": "PANSS_Total_category"
                },
                "backgroundColor": "#FFE0E0",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{PANSS_Total_category}} contains 'Moderate'",
                    "column_id": "PANSS_Total_category"
                },
                "backgroundColor": "#FFBABA",
                "color": "black"
            },
            {
                "if": {
                    "filter_query": f"{{PANSS_Total_category}} contains 'Severe'",
                    "column_id": "PANSS_Total_category"
                },
                "backgroundColor": "#FF7575",
                "color": "black"
            },
        ],    )

'''
Light Red → #ffcccc
	•	Light Green → #ccffcc
	•	Light Blue → #cce5ff
	•	Light Yellow → #ffffcc
'''
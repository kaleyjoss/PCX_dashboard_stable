import dash
from dash import Dash, dcc, html, callback, Input, Output, dash_table
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import dash_mantine_components as dmc
import json
import datetime
import os
from datetime import datetime as dt

#external_stylesheet = dbc.themes.CERULEAN
dash.register_page(__name__, path="/survey_data", title='Survey Data', name='Survey Data')

project = os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR/PCX/behavioral')

tracker_df=pd.read_excel(os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Subject_tracker_PCR.xlsx'), sheet_name='tracker')

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

def extract_survey_date(filename):
	datestr = filename.split('_')[-1].split('.')[0]
	try:
		date_obj = dt.strptime(datestr, '%b %d, %Y')
		if date_obj is not None and isinstance(date_obj, dt):
			return date_obj
	except Exception as e:
		logging.debug(f"no datetime in {filename}: {e}")
	
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
			logging.debug(f'filename={filename} -> date={extract_survey_date(filename)}')

	if len(dates) > 0:
		dates.sort(key=lambda file: file['date'], reverse=True)
		logging.debug(dates)
		return os.path.join(directory, dates[0]['filename'])
	
	return None


survey_names = ['clinical_administered_data','clinical_self_report_data',
					 'mri_self_report_data','supplemental_self_report_data']

surveys={}
recoded_surveys={}
for root, dirs, files in os.walk(project):
	for survey in survey_names: 
		if survey in dirs: 
			surveys[survey] = []
			survey_dir = os.path.join(root, survey)
			try:
				filepath = get_most_recent_survey(survey_dir)
				filepath_recoded = get_most_recent_survey(survey_dir, recoded=True)
			except Exception as e:
				logging.error(f'For survey_dir {survey_dir}, {e}')
			if filepath is not None:
				logging.debug(f'most recent survey for {survey}: {os.path.basename(filepath)}')
				surveys[survey] = pd.read_csv(filepath)
				recoded_surveys[survey]=pd.read_csv(filepath_recoded)

first_df = surveys[survey_names[0]]
subject_ids = first_df['SUBJECT_ID'].unique()

survey_to_df = {
	'panss': recoded_surveys['clinical_administered_data'], 
	'madrs': recoded_surveys['clinical_administered_data'],
	'bprs': recoded_surveys['clinical_administered_data'],
	'ymrs': recoded_surveys['clinical_administered_data'],
	'cssrs': recoded_surveys['clinical_administered_data'],
}

def create_sub(df, subject):
	sub_df=df[df['SUBJECT_ID']==subject].copy()
	sub_df=sub_df.reset_index()
	sub_str=sub_df.to_json()
	return sub_df, sub_str


def filter_subject_qualtrics(df, subject):
	return df[df['SUBJECT_ID']==subject]

def render_table(subject, survey_name=None, survey_regex=None, survey_cols=None, df_to_use=None):
	if df_to_use is not None:
		df = df_to_use
		cols =  survey_cols if survey_cols is not None else df.columns.to_list()
	if survey_name is not None and df_to_use is None:
		df = survey_to_df[survey_name]
		cols = [col for col in df.columns if survey_name in col and 'notes' not in col and 'total' not in col]
	if survey_cols is not None:
		search_for_col = survey_cols[0]
		for survey_name in surveys:
			if search_for_col in surveys[survey_name].columns.to_list():
				df = surveys[survey_name]
				cols = [col for col in df.columns if col in survey_cols]
	else:
		return None
	
	if len(cols)==0:
		return html.Div(children=[f'No data for subject {subject}, survey {survey_name}'])
	else:
		if 'SUBJECT_ID' not in cols:
			cols = cols + ['SUBJECT_ID']
		survey_df = df[cols]
		mapping = dict(zip(survey_df.columns, survey_df.iloc[0]))
		sub_df = filter_subject_qualtrics(survey_df, subject)
		long_df = sub_df.melt(id_vars='SUBJECT_ID', var_name='name', value_name='value')
		long_df['label'] = long_df['name'].map(mapping)
		long_df = long_df[['label', 'value']]
		long_df['label'] = long_df['label'].str.split('\n').str[0]
		#long_df = long_df.sort_values('value', ascending=False)
	
		return dash_table.DataTable(
			data=long_df.to_dict('records'),
			columns=[{'id': c, 'name': c} for c in long_df.columns],
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
				} for row in df.to_dict('records')
			],
			tooltip_duration=None,
			style_cell={
				"textAlign": "left",
				"whiteSpace": "normal",
				"height": "auto",
				"fontFamily": "Arial, sans-serif",
				"fontSize": "14px",
				"padding": "8px"
			},
			style_header={
				"backgroundColor": "#f0f2f6",
				"fontWeight": "bold"
			},
			style_data_conditional=[
				{
					"if": {"row_index": "odd"},
					"backgroundColor": "#fafafa"
				}
			]      
		)
	

def render_chart(subject, survey_name=None, survey_regex=None):
	if survey_name is not None:
		df = survey_to_df[survey_name]
		cols = [col for col in df.columns if survey_name in col and 'notes' not in col and 'total' not in col and 'timing' not in col]
		if len(cols)==0:
			return html.Div(children=[f'No data for subject {subject}, survey {survey_name}'])
		else:
			survey_df = df[['SUBJECT_ID']+cols]
			mapping = dict(zip(survey_df.columns, survey_df.iloc[0]))
			sub_df = filter_subject_qualtrics(survey_df, subject)
			long_df = sub_df.melt(id_vars='SUBJECT_ID', var_name='name', value_name='value')
			long_df['label'] = long_df['name'].map(mapping)
			long_df = long_df[['label', 'value']]
			long_df['label'] = long_df['label'].str.split('\n').str[0]
			long_df['label'] = long_df['label'].str.lower()
			long_df['value'] = pd.to_numeric(long_df['value'], errors='coerce')
			fig = px.bar(long_df, x='label', y='value', text_auto='.2s', range_y=[0,10])
			fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
			fig.update_layout(xaxis_tickangle=-35, title=f'Subject {subject}, Survey: {survey_name.upper()}')  
			return dcc.Graph(
				figure=fig,
				config={'displayModeBar': True}, 
				style={'width': '100%',  'height': '100%' },  className = "outer-graph",
			)


def render_graph(subject):
		full_df = pd.DataFrame()
		for survey_name in surveys:
			df = surveys[survey_name]
			df.columns = df.iloc[0]
			sub_df = filter_subject_qualtrics(df, subject)
			full_df = pd.concat([full_df, sub_df], axis=1)
		cols = [col for col in full_df.columns if any(item in col for item in list(survey_to_df.keys())) in col and 'notes' not in col and 'total' not in col and 'timing' not in col]
		if len(cols)==0:
			return html.Div(children=[f'No data for subject {subject}'])
		else:
			long_df = sub_df.melt(id_vars='SUBJECT_ID', var_name='name', value_name='value')
			long_df = long_df[['label', 'value']]
			
			for survey in survey_to_df.keys():
				long_df.loc[long_df['label'].str.contains(survey), 'label'] = long_df.loc[long_df['name'].str.contains(survey), 'name']
			long_df['label'] = long_df['label'].str.split('\n').str[0]
			long_df['label'] = long_df['label'].str.lower()
			long_df['value'] = pd.to_numeric(long_df['value'], errors='coerce')
			fig = px.line(long_df, x='label', y='value', color='', text_auto='.2s', range_y=[0,10])
			fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=True)
			fig.update_layout(xaxis_tickangle=-35)  
			return dcc.Graph(
				figure=fig,
				config={'displayModeBar': True}, 
				style={'width': '100%',  'height': '100%', 'padding': 10},  className = "outer-graph",
			)

def render_overview(subject):
	df = surveys['mri_self_report_data']
	if not subject in surveys['mri_self_report_data']['SUBJECT_ID'].unique():
		if subject.lower() in surveys['mri_self_report_data']['SUBJECT_ID'].unique():
				subject = subject.lower()
		else:
			return None
	survey_cols = [
	"sex",
	"sex_5_TEXT",
	"age",
	"weight",
	"place_birth",
	"marital",
	"marital_6",
	"house",
	"house_7",
	"live_with_whom",
	"live_with_whom_2",
	"native_lang",
	"native_lang_2",
	"ethnic",
	"racial"]
	table = render_table(subject, survey_cols=survey_cols)
	return table


def render_diagnosis(subject):
	df = surveys['clinical_administered_data']
	if not subject in surveys['clinical_administered_data']['SUBJECT_ID'].unique():
		if subject.lower() in surveys['clinical_administered_data']['SUBJECT_ID'].unique():
				subject = subject.lower()
		else:
			return None

	primary_diagnoses_cols = [col for col in df.columns if 'primary_diagnoses' in col]+['SUBJECT_ID']
	primary = df[primary_diagnoses_cols]
	primary_sub = primary[primary['SUBJECT_ID']==subject]
	primary_sub_diagnoses = primary_sub.values.flatten()
	primary = [item for item in primary_sub_diagnoses if not pd.isna(item) and subject not in item]
	other_diagnoses_cols = [col for col in df.columns if 'other_diagnoses' in col]+['SUBJECT_ID']
	other = df[other_diagnoses_cols]
	other_sub = other[other['SUBJECT_ID']==subject]
	other_sub_diagnoses = other_sub.values.flatten()
	other = [item for item in other_sub_diagnoses if not pd.isna(item) and subject not in item]

	return primary, other

layout = html.Div([
	dcc.Location(id="url"),
	html.H1(children='Subject Viewer', style={'margin':20}),
	
	html.Div(children=[
		dcc.Markdown(id='caption'),
		dcc.Markdown(id='diagnosis', style={'width': '30%', 'padding': '10px'}),


		html.Div(children=[
			html.Div(id='sub-overview', style={'width': '30%', 'padding': '10px'}),
			html.Div(id='surveys', 
					children=[
						html.Div(id='session-notes'),
						html.Div(id='scan-notes'),
						dcc.RadioItems(list(survey_to_df.keys()), id='survey_choice', value='panss'),
						dcc.Tabs(id="content-type", value='Chart', children=[
							dcc.Tab(label='Chart', value='Chart'),
							dcc.Tab(label='Table', value='Table'),
							])
					], style={'width': '30%','padding': '10px'}
			),
			html.Div(id='tabs-content', style={'width': '30%','padding': '10px'})

		], style={
			'display': 'flex',
			'flexDirection': 'row',   # ensures they’re side by side
			'justifyContent': 'space-between'  # adds spacing between columns
		}),
	])
])



@callback(
	Output(component_id='sub-overview', component_property='children'),
	Input(component_id='subject-id', component_property='data'),
)
def update_subject(subject):
	sub_overview = render_overview(subject)
	return subject, sub_overview

@callback(
	Output(component_id='session-notes', component_property='children'),
	Input(component_id='subject-picker', component_property='value')
)
def update_subject(subject):
	session_notes = render_table(subject, survey_cols=['Session Notes (anything missing, MRI notes)'], df_to_use=tracker_df)
	return session_notes

@callback(
	Output(component_id='scan-notes', component_property='children'),
	Input(component_id='subject-picker', component_property='value')
)
def update_subject(subject):
	scan_notes = render_table(subject, survey_cols=['MRI Scan Notes'], df_to_use=tracker_df)
	return scan_notes

@callback(
	Output(component_id='caption', component_property='children'), 
	Output(component_id='diagnosis', component_property='children'),
	Input(component_id='subject-id', component_property='data')
)
def update_caption(subject):
	primary, other = render_diagnosis(subject)

	subject_text = '''
	### Your subject is {}
	'''.format(subject)

	diagnoses_text = f'''
	#### Primary Diagnoses: {primary}
	Other diagnoses: {other}
	'''
	return subject_text, diagnoses_text

@callback(
		Output('tabs-content', 'children'),
		Input('survey_choice', 'value'),
		Input('content-type', 'value'),
		Input('subject-id', 'data'),
)
def render_content(survey, contentType, subject):
	if contentType=='Table':
		return render_table(subject, survey_name=survey)
	if contentType=='Chart':
		return render_chart(subject, survey_name=survey)


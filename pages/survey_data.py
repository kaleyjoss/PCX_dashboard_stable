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
import sys

# Import custom scripts
from scripts.surveys import load_surveys, subsurvey_key
from scripts.paths import load_paths
dashboard_dir = os.path.basename(os.getcwd())
sys.path.append(dashboard_dir)

#external_stylesheet = dbc.themes.CERULEAN
dash.register_page(__name__, path="/survey_data", title='Survey Data', name='Survey Data')

paths_dict = load_paths()
tracker_df=paths_dict['tracker_df']
surveys_dir = paths_dict['surveys_dir']
surveys, recoded_surveys = load_surveys(surveys_dir)

first_df = surveys['clinical_administered_data']
subject_ids = first_df['SUBJECT_ID'].unique()

import logging
logging.basicConfig(
	level=logging.INFO,        # Minimum logging level
	format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

def create_sub(df, subject):
	sub_df=df[df['SUBJECT_ID']==subject].copy()
	sub_df=sub_df.reset_index()
	sub_str=sub_df.to_json()
	return sub_df, sub_str


def filter_subject_qualtrics(df, subject):
	return df[df['SUBJECT_ID']==subject]

#table = render_table(subject, surveys, subsurvey_key, survey_name=survey_name, survey_cols=survey_cols)

def render_table(subject, surveys, subsurvey_key, survey_name=None, sub_survey_name=None, survey_regex=None, survey_cols=None, df_to_use=None):
	if df_to_use is not None:
		df = df_to_use
		if sub_survey_name is not None: 
			cols = [col for col in df.columns.to_list() if sub_survey_name in col and 'notes' not in col and 'total' not in col]
		elif survey_cols is not None:
			cols =  [col for col in df.columns.to_list() if col in survey_cols]
		else:
			cols = df.columns.to_list()
	elif survey_cols is not None:
		if survey_name is not None:
			df = surveys[survey_name]
			cols = [col for col in survey_cols if col in df.columns.to_list()]
		elif survey_name is None:
			search_for_col = survey_cols[0]
			for survey_name in surveys:
				if search_for_col in surveys[survey_name].columns.to_list():
					df = surveys[survey_name]
					cols = [col for col in df.columns if col in survey_cols]
	elif sub_survey_name is not None:
		if survey_name is not None:
			df = surveys[survey_name]
			cols = [col for col in df.columns if sub_survey_name in col and 'notes' not in col and 'total' not in col]
		
	else:
		return html.Div(children=[f'Not enough keywords to render_table -- {subject}'])
	
	#logging.info(f'For subject {subject}, rendering table of {cols}. {df.head(2)}')
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
				} for row in long_df.to_dict('records')
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
	

def render_chart(subject, recoded_surveys, subsurvey_key, sub_survey_name, survey_name=None):
	if survey_name is not None:
		df = recoded_surveys[survey_name]
	if sub_survey_name is not None:
		df = recoded_surveys[subsurvey_key[sub_survey_name]]
		cols = [col for col in df.columns if sub_survey_name in col and 'notes' not in col and 'total' not in col and 'timing' not in col]
		if len(cols)==0:
			return html.Div(children=[f'No data for subject {subject}, survey {sub_survey_name}'])
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
			fig.update_layout(xaxis_tickangle=-35, title=f'Subject {subject}, Survey: {sub_survey_name.upper()}')  
			return dcc.Graph(
				figure=fig,
				config={'displayModeBar': True}, 
				style={'width': 500,  'height': 300},  className = "outer-graph",
			)


def render_graph(subject, recoded_surveys, sub_survey_name, survey_name=None):
	full_df = pd.DataFrame()
	if survey_name is not None:
		full_df = recoded_surveys[survey_name]
	elif sub_survey_name is not None:
		df = recoded_surveys[subsurvey_key[sub_survey_name]]
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
			style={'width': 500,  'height': 300, 'padding': 1 },  className = "outer-graph",
		)

def render_overview(subject, surveys, survey_name):
	df = surveys[survey_name]
	if subject is None:
		return html.Div(children=['No subject selected'])
	if not subject in surveys[survey_name]['SUBJECT_ID'].unique():
		if subject.lower() in surveys[survey_name]['SUBJECT_ID'].unique():
				subject = subject.lower()
		else:
			return html.Div(children=[f'Subject {subject} has not completed the MRI scan yet.'])
	return render_table(subject, surveys, subsurvey_key, survey_cols=demographic_survey_cols)

def render_diagnosis(subject, surveys, survey_name):
	df = surveys[survey_name]
	if subject is not None and subject not in surveys[survey_name]['SUBJECT_ID'].unique():
		if subject.lower() in surveys[survey_name]['SUBJECT_ID'].unique():
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
		dcc.Markdown(id='diagnosis', style={'width': '100%', 'padding': '0px'}),


		html.Div(children=[
			html.Div(id='sub-overview', style={'width': '20%', 'padding': '0px'}),
			html.Div(id='survey-container', 
					children=[
						html.Div(id='session-notes'),
						html.Div(id='scan-notes'),
					], style={'width': '20%','padding': '0px'}
			),
			html.Div(id='chart-container', children=[
				dcc.RadioItems((['panss', 'bprs', 'ymrs', 'madrs', 'cssrs']), id='sub-survey-name', value='panss'),
				dcc.Tabs(id="content-type", value='Chart', children=[
					dcc.Tab(label='Chart', value='Chart'),
					dcc.Tab(label='Table', value='Table'),
					]),
				html.Div(id='tabs-content', style={'width': 500,'padding': '5px'})
			]),

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
	sub_overview = render_overview(subject, surveys, survey_name='mri_self_report_data')
	return sub_overview


@callback(
	Output(component_id='session-notes', component_property='children'),
	Input(component_id='subject-id', component_property='data'),
)
def update_subject(subject):
	session_notes = render_table(subject, surveys, subsurvey_key, survey_cols=['Session Notes (anything missing, MRI notes)'], df_to_use=tracker_df)
	return session_notes


@callback(
	Output(component_id='scan-notes', component_property='children'),
	Input(component_id='subject-id', component_property='data'),

)
def update_subject(subject):
	scan_notes = render_table(subject, surveys, subsurvey_key, survey_cols=['MRI Scan Notes'], df_to_use=tracker_df)
	return scan_notes


@callback(
	Output(component_id='caption', component_property='children'), 
	Output(component_id='diagnosis', component_property='children'),
	Input(component_id='subject-id', component_property='data'),
)
def update_caption(subject):
	primary, other = render_diagnosis(subject, surveys, survey_name='clinical_administered_data')

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
		Input('subject-id', 'data'),
		Input('sub-survey-name', 'value'),
		Input('content-type', 'value'),
)

def render_content(subject, sub_survey_name, contentType):
	if contentType=='Table':
		return render_table(subject, surveys, subsurvey_key, sub_survey_name=sub_survey_name)
	if contentType=='Chart':
		return render_chart(subject, recoded_surveys, subsurvey_key, sub_survey_name=sub_survey_name)


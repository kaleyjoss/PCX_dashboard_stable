import dash
from dash import Dash, dcc, html, callback, Input, Output, dash_table
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import dash_mantine_components as dmc
import json
#external_stylesheet = dbc.themes.CERULEAN
dash.register_page(__name__, path="/surveys", title='Survey Data', name='Survey Data')

data=pd.read_excel('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/Subject_tracker_PCR.xlsx', sheet_name='clean_data')
subject_ids = data['Qual ID'].unique()

clinRatings=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_ClinicalVisit_ClinicianRatings/PCX_ClinicalVisit_ClinicianRatings_June 18, 2025_17.59.csv')
supp=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_SupplementalBattery/PCX_SupplementalBattery_June 18, 2025_17.12.csv')
fmriBattery=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_fMRIVisit_SelfReport/PCX_fMRIVisit_SelfReport_June 18, 2025_17.13.csv')
clinBattery=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_ClinicalVisit_ClinicianRatings/PCX_ClinicalVisit_ClinicianRatings_June 18, 2025_17.59.csv')

survey_to_df = {
	'panss': clinRatings, 
	'madrs': clinRatings,
	'bprs': clinRatings,
	'ymrs': clinRatings,
	'cssrs': clinRatings,
	'fam_conditions': fmriBattery,
	'asi': fmriBattery,
	'dass': fmriBattery,
	'stai': clinBattery,
	'neoffi': clinBattery,
	'bapq': clinBattery,
	'qids': clinBattery,
}

def create_sub(df, subject):
	sub_df=df[df['Qual ID']==subject].copy()
	sub_df=sub_df.reset_index()
	sub_str=sub_df.to_json()
	return sub_df, sub_str


def filter_subject_qualtrics(df, subject):
	return df[df['SUBJECT_ID']==subject]

def render_table(subject, survey_name=None, survey_regex=None):
	if survey_name is not None:
		df = survey_to_df[survey_name]
		cols = [col for col in df.columns if survey_name in col and 'notes' not in col and 'total' not in col]
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
			long_df = long_df.sort_values('value', ascending=False)
		
		return dash_table.DataTable(
			data=long_df.to_dict('records'),
			columns=[{'id': c, 'name': c} for c in long_df.columns],
			css=[{
				'selector': '.dash-spreadsheet td div',
				'rule': '''
					line-height: 15px;
					max-height: 30px; min-height: 30px; height: 30px;
					display: block;
					overflow-y: hidden;
				'''
			}],
			tooltip_data=[
				{
					column: {'value': str(value), 'type': 'markdown'}
					for column, value in row.items()
				} for row in df.to_dict('records')
			],
			tooltip_duration=None,
			style_cell={'textAlign': 'left'})      
	else:
		return None

def render_chart(subject, survey_name=None, survey_regex=None):
	if survey_name is not None:
		df = survey_to_df[survey_name]
		cols = [col for col in df.columns if survey_name in col and 'notes' not in col and 'total' not in col]
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
			fig.update_layout(xaxis_tickangle=-35)  
			return dcc.Graph(
				figure=fig,
				config={'displayModeBar': True}, 
				style={'width': '100%',  'height': '100%' },  className = "outer-graph",
			)


def render_graph(subject):
		full_df = pd.DataFrame()
		for df in [clinRatings, clinBattery, supp, fmriBattery]:
			df.columns = df.iloc[0]
			sub_df = filter_subject_qualtrics(df, subject)
			full_df = pd.concat([full_df, sub_df], axis=1)
		cols = [col for col in full_df.columns if any(item in col for item in list(survey_to_df.keys())) in col and 'notes' not in col and 'total' not in col]
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
			fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
			fig.update_layout(xaxis_tickangle=-35)  
			return dcc.Graph(
				figure=fig,
				config={'displayModeBar': True}, 
				style={'width': '100%',  'height': '100%' },  className = "outer-graph",
			)

layout = html.Div([
	dcc.Location(id="url"),
	html.H1(children='Subject Viewer', style={'margin':20}),
	html.Div(children=[
		html.Div(children=[
			html.Div("Use this dropdown to select the subject"),
			dcc.Dropdown(subject_ids, id='subject-picker',clearable=False, value='qualr200'),
			dcc.Store(id='subject-id'),
			dcc.Markdown(id='caption'),
		], style={'width': '48%', 'float': 'left', 'display': 'inline-block'}),
		html.Div(children=[
			dcc.RadioItems(list(survey_to_df.keys()), id='survey', value='panss'),
			dcc.Tabs(id="content-type", value='Chart', children=[
				dcc.Tab(label='Chart', value='Chart'),
				dcc.Tab(label='Table', value='Table'),
			]),
			html.Div(id='tabs-content')
		], style={'width': '48%', 'right': '', 'display': 'inline-block'}),
	], style={'display': 'flex', 'margin':20, 'flexDirection': 'row'}
	),
])

@callback(
	Output(component_id='subject-id', component_property='data'),
	Input(component_id='subject-picker', component_property='value')
)
def update_subject(subject):
	return subject


@callback(
	Output(component_id='caption', component_property='children'), 
	Input(component_id='subject-id', component_property='data')
)
def update_caption(subject):
	markdown_text = '''
	### Your subject is {}
	'''.format(subject)
	return markdown_text

@callback(
		Output('tabs-content', 'children'),
		Input('survey', 'value'),
		Input('content-type', 'value'),
		Input('subject-id', 'data'),
)
def render_content(survey, contentType, subject):
	if contentType=='Table':
		return render_table(subject, survey_name=survey)
	if contentType=='Chart':
		return render_chart(subject, survey_name=survey)


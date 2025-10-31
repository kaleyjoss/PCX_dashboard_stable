import os
import sys
import re
import dash
from dash import html, dcc, callback, Input, Output
import plotly 
import plotly.express as px
import pandas as pd
import xarray as xr
import importlib
import logging
import pickle
import inspect
import os
import sys
from dash import Dash, html, dcc, Input, Output, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import os
import glob

# Import custom scripts
dashboard_dir = os.path.basename(os.getcwd())
sys.path.append(dashboard_dir)
from scripts.update_dataframes import update_dfs
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
	importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
	importlib.reload(sys.modules['scripts.sub_id'])
from scripts.update_dataframes import update_dfs
from scripts.paths import load_paths
from scripts.surveys_loader import load_surveys

# Register page into dash app as pagename
dash.register_page(__name__, path="/passive_data", title='Passive Data', name='Passive Data')

sensor_to_file_dict = {'gps': ['gps_freq','gps_freq2','gps_dist'],
					   'accel': ['accel_activityScores'],
					   'power': ['power_activityScores']}


app_answers = ['Cheerful', 'Stressed', 'Down', 'Relaxed', 'Down', 'Strange', 
			   'Content', 'Suspicious', 'Relaxed', 'Racing', 'Enthusiastic', 
			   'Auditory', 'Empty', 'Anxious', 'Concentrate', 'Irritable', 
			   'Confused', 'Visual', 'Handle', 'Function', 'Socialp', 'Sociald',
			   'Negative','Positive']

# === Paths ===
paths_dict = load_paths()
pcx_dir = paths_dict["pcx_dir"]
mindlamp_dir = paths_dict['mindlamp_dir']
DATA_DIR = os.path.join(mindlamp_dir, 'data')


# === Layout ===
layout = dbc.Container([
	dbc.Row([
		dbc.Col([
			html.H3("Participant Dashboard"),
			html.Hr(),
			html.Div(id='data-status', className='text-muted'),
			dcc.Checklist(id='survey-cols', value=['Cheerful'], options=app_answers, inline=False,
				style={
					'display': 'flex',
					'flexDirection': 'column',
					'gap': '3px',  # adds nice vertical spacing
					'margin': '5px 5px',
					'fontSize': '10px'
				}),
			], width=3),

		dbc.Col([
			dcc.Tabs(id='tabs', value='tab-sensor', children=[
				dcc.Tab(label='Sensor Heatmaps', value='tab-sensor'),
				dcc.Tab(label='Survey Responses', value='tab-survey'),
			]),
			html.Div(id='tab-content', style={'marginTop': 20}),
		], width=9)
	]),
	html.Hr(),
	html.Hr(),
	html.Div(id='app-questions')
], fluid=True)


@callback(
	Output('tab-content', 'children'),
	Output('data-status', 'children'),
	Input(component_id='subject-id', component_property='data'),
	Input('tabs', 'value'),
	Input('survey-cols', 'value'),

)
def update_tab(subject_id, active_tab, survey_cols):
	if subject_id is None:
		return html.Div("No subject selected"), ""
	if active_tab is None:
		return html.Div("No tab selected"), ""

	if active_tab=='tab-sensor':
		if not subject_id:
			return "Please select a participant.", "⚠️ No subject selected."
		if 'qual' in subject_id:
			subject_id = subject_id.replace('qualr','PCR').replace('qualm','PCM')

		subj_path = os.path.join(DATA_DIR, subject_id, 'phone', 'processed')
		if not os.path.exists(subj_path):
			return html.Div(f"No sensor activity data found. Looked in {subj_path} "), f"❌ No data in {subj_path}"

		# ---- Tab 1: HEATMAP ----
		if active_tab == 'tab-sensor':
			figs = []
			status_msgs = []
			for sensor in sensor_to_file_dict:
				for file in sensor_to_file_dict[sensor]:
					path = f'{os.path.join(subj_path, sensor)}'
					if not os.path.exists(path):
						status_msgs.append(f"❌ {sensor}: folder missing")
						continue
					
					csvs = glob.glob(os.path.join(path, f"**{file}**.csv"))
					if not csvs:
						status_msgs.append(f"⚠️ {sensor}: no CSVs")
						continue

					df = pd.read_csv(sorted(csvs)[-1])  # take latest
					num_df = df[[col for col in df.columns if 'activityScore' in col]]
					# Drop empty rows/days, this happens bc participants start some time after start of study
					num_df_clean = num_df.dropna(axis=0, how='all')
					
					if num_df_clean.empty:
						status_msgs.append(f'{file} exists but no data has been collected.')
						continue
					
					status_msgs.append(f'Found {file} csv')

					
					fig = px.imshow(
						num_df_clean.values,
						origin='lower',
						color_continuous_scale='Viridis',
						labels={'x': "Hour of Day", 'y': "Day"},
						title=f"{file.capitalize()})"
					)
					fig.update_layout(
						height=400, width=300,
						margin=dict(l=10, r=10, t=30, b=30),
						coloraxis_showscale=False
					)
					figs.append(dcc.Graph(figure=fig, style={'margin': '15px'}))

			if not figs:
				return html.Div(f"No sensor activity data found. Looked in {subj_path} "), f"{status_msgs} ⚠️ No data to show"

			grid = html.Div(
				figs,
				style={
					'display': 'flex',
					'flexWrap': 'wrap',
					'justifyContent': 'center',
					'gap': '10px'
				}
			)
			return grid, html.Ul([html.Li(msg) for msg in status_msgs])


	# ---- Tab 3: FIGURES ----
	elif active_tab == 'tab-survey':
		if not subject_id:
			return "Please select a participant.", "⚠️ No subject selected."
		if 'qual' in subject_id:
			subject_id = subject_id.replace('qualr','PCR').replace('qualm','PCM')

		subj_path = os.path.join(DATA_DIR, subject_id, 'phone', 'processed')
		if not os.path.exists(subj_path):
			return html.Div("No data found for this sensor."), f"❌ No data in {subj_path}"

		survey_path = os.path.join(subj_path, 'survey')
		csvs = glob.glob(os.path.join(survey_path, f"**surveyAnswers_activityScores**.csv"))
		if not csvs:
			return html.Div("No survey data found."), f"⚠️ No survey CSVs from {survey_path}"
		df = pd.read_csv(sorted(csvs)[-1])
		if 'day' in df.columns:
			df['day'] = pd.to_numeric(df['day'], errors='coerce')
		else:
			return html.Div(f"Survey {os.path.basename(csvs[-1])} had no 'day' column"), f"Survey {os.path.basename(csvs[-1])} had no 'day' column"
		fig = px.line(df, x='day', y=survey_cols, title=f'Subject {subject_id} Survey Responses')
		return dcc.Graph(figure=fig), f"✅ Survey: {os.path.basename(csvs[-1])}"


# @callback(
#     Output(component_id='survey-graph', component_property='children'),
#     Output(component_id='survey-msgs', component_property='children'),
#     Input(component_id='subject-id', component_property='data'),
#     Input('survey-cols', 'value'),   
# )
# def update_survey(subject_id, survey_cols):
#     if not subject_id:
#         return "Please select a participant.", "⚠️ No subject selected."
#     if 'qual' in subject_id:
#         subject_id = subject_id.replace('qualr','PCR').replace('qualm','PCM')

#     subj_path = os.path.join(DATA_DIR, subject_id, 'phone', 'processed')
#     if not os.path.exists(subj_path):
#         return html.Div("No data found for this sensor."), f"❌ No data in {subj_path}"

#     survey_path = os.path.join(subj_path, 'survey')
#     csvs = glob.glob(os.path.join(survey_path, f"**surveyAnswers_activityScores**.csv"))
#     if not csvs:
#         return html.Div("No survey data found."), f"⚠️ No survey CSVs from {survey_path}"
#     df = pd.read_csv(sorted(csvs)[-1])
#     if 'day' in df.columns:
#         df['day'] = pd.to_numeric(df['day'], errors='coerce')
#     else:
#         return html.Div(f"Survey {os.path.basename(csvs[-1])} had no 'day' column"), f"Survey {os.path.basename(csvs[-1])} had no 'day' column"
#     fig = px.line(df, x='day', y=survey_cols, title=f'Subject {subject_id} Survey Responses')
#     return dcc.Graph(figure=fig), f"✅ Survey: {os.path.basename(csvs[-1])}"

@callback(
    Output('app-questions', 'children'),
    Input('subject-id', 'data')
)
def return_app_questions(subject_id):
    return dbc.Row([
		html.H3("Questions on the App Surveys"),
        dbc.Col([
            html.H4("Emotions"),
            dcc.Markdown('Rate on the below scale for the following emotions: **Relaxed, tense, energetic, fatigued, happy, sad, stressed, hostile, irritable, alert, ashamed, inspired, upset, afraid, lonely, outgoing**'),
            dcc.Markdown('''
            1) Not at all  
            2) A little  
            3) Moderately  
            4) Quite a bit  
            5) Extremely
            '''),
            html.H4("Social"),
            dcc.Markdown('''
            **Social in Person (socialp)**.   
            1) I spent almost all of my time alone  
            2) I interacted with others but little more than superficial interactions  
            3) I interacted with others in a meaningful way  
            4) I extensively interacted with close friends or family or a significant other  
            5) I experienced an unusually deep connection with another person  

            **Social Digitally (sociald)**   
            1) I spent almost no time interacting with others on my phone or computer  
            2) I interacted with others but little more than superficial messages  
            3) I interacted with others on my phone or computer in a meaningful way  
            4) I extensively interacted with close friends or family or a significant other  
            5) I experienced an unusually deep connection through a digital interaction
            '''),
            html.H4("Stress and Anxiety"),
            html.Div('''
            **Able to manage stress (empty)**     
            1) Very unsuccessful  
            2) A little bit successful  
            3) Moderately successful  
            4) Very successful  
            5) Extremely successful  

            **Anxious (anxious)**     
            1) Completely relaxed  
            2) Relaxed  
            3) Typical, some moments of anxiety
            '''),
        ], width=3),

        dbc.Col([
            html.H4('Physical'),
            dcc.Markdown('''
            **Physically Active**   
            1) Minimal movement, didn’t get off the couch  
            2) Little more than getting around my living space  
            3) Only did what was necessary (walking to do errands)  
            4) Exercised 30 min or less  
            5) Exercised 30–60 min  
            6) Exercised more than 60 min  

            **Hungry**   
            1) Not hungry at all, and ate much less than I normally would  
            2) Not as hungry as usual, ate slightly less than normal  
            3) Typical level of hunger, ate all my normal meals and foods  
            4) More hungry than usual, ate a little more than usual (extra portion or snack)  
            5) Surprisingly hungry, ate a lot more than usual (extra meal or binge)  
            '''),
        ], width=3),

        dbc.Col([
            html.H4('Consumption'),
            dcc.Markdown('''
            **Consuming Caffeine**    
            1) None  
            2) One cup of coffee, tea, or soft drink  
            3) Two cups of coffee, tea, or soft drink  
            4) Three cups of coffee, tea, or soft drink  
            5) More than three cups of coffee, tea, or soft drink  

            **Consuming Alcohol**     
            1) None  
            2) One drink  
            3) Two drinks  
            4) Three or four drinks  
            5) Five or more drinks  

            **Consuming Cannabis or CBD**     
            1) Zero times  
            2) Once  
            3) Twice  
            4) Three times  
            5) Four or more times  

            **Taking Medications**     
            1) None / I don’t usually take prescribed medication  
            2) Less than usual (forgot, skipped, or reduced a dose)  
            3) As prescribed (same as usual)  
            4) More than usual (increased dose or took an extra dose)  
            5) Substantially more than usual (two or more extra)  

            **Menstruating**     
            1) No  
            2) Uncertain – maybe just beginning  
            3) Yes with light flow or minimal cramping  
            4) Yes with medium flow or moderate cramping  
            5) Yes with heavy flow or very painful cramping  
            6) Not Applicable  
            '''),
            html.H4('Psychosis'),
            dcc.Markdown('''
            **Bothered by hearing voices**     
            1) Not at all  
            2) A little  
            3) Moderately  
            4) Quite a bit  
            5) Extremely  

            **Bothered by seeing things others could not**     
            1) Not at all  
            2) A little  
            3) Moderately  
            4) Quite a bit  
            5) Extremely  

            **Feeling like other people are out to get you or cause you trouble**     
            1) Not at all  
            2) A little  
            3) Moderately  
            4) Quite a bit  
            5) Extremely  
            '''),
        ], width=3)
    ])
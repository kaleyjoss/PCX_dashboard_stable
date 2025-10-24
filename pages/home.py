# Ensure compatibility with React 18

import dash
from dash import html, Input, Output, callback, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import Dash, _dash_renderer, dash_table
from dash_iconify import DashIconify
_dash_renderer._set_react_version("18.2.0")
import logging
import os
import sys
import dash
from dash import html, dcc, callback, Input, Output
import dash
from dash import html, dcc, callback, Input, Output
import plotly 
import plotly.express as px
import pandas as pd
import xarray as xr
import importlib
import logging
import re
import pickle
import inspect
from datetime import timedelta
from datetime import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import datetime
from datetime import  timedelta
from datetime import datetime as dt
import numpy as np
import os
import re
import logging
import pandas as pd
import xarray as xr
import plotly.express as px
import plotly.graph_objects as go

# ===============================================
# Dash Page Registration
# ===============================================
# Registers this file as the main '/' page of the Dash multi-page app
dash.register_page(__name__, 
	path='/', # these 3 are automatically generated like this, but you can edit them
	title='Home',
	name='Home'
)


# ===============================================
# Logging Configuration
# ===============================================
logging.basicConfig(
	filename='dashboard.log',        # File to write logs to, saved in working directory
	filemode='a',              # 'a' for append, 'w' to overwrite each time
	level=logging.INFO,        # Minimum logging level
	format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)


# ===============================================
# Custom Script Imports (from local `scripts` directory)
# ===============================================
dashboard_dir = os.path.basename(os.getcwd())
sys.path.append(dashboard_dir)

from scripts import sub_id, paths, surveys_loader, surveys_api, tables
# Do the below if any of the above packages aren't updating to the most recent version
if 'scripts.paths' in sys.modules:
	importlib.reload(sys.modules['scripts.paths'])

# ===============================================
# Load Paths and Survey Data
# ===============================================
paths_dict = paths.load_paths()
project_dir = paths_dict["project_dir"]
surveys_dir = paths_dict["surveys_dir"]
demographic_df_dir = paths_dict["demographic_df_dir"]
tracker_df = paths_dict["tracker_df"]
surveys, recoded_surveys = surveys_loader.load_surveys(surveys_dir)
surveys = surveys_loader.add_diagnoses_columns(surveys)


# ===============================================
# Site-based Filtering and Duration Conversion
# ===============================================
session1 = surveys['clinical_administered_data']
session2 = surveys['mri_self_report_data']
session1sr = surveys['clinical_self_report_data']
session3 = surveys['supplemental_self_report_data']

# Make a column in each session DF, named the name of the survey, filled by the date it was done (for combining later)
session1['clinical_administered_data'] = pd.to_datetime(surveys['clinical_administered_data']['StartDate'], errors='raise')
session2['mri_self_report_data'] = pd.to_datetime(surveys['mri_self_report_data']['StartDate'], errors='raise')
session1sr['clinical_self_report_data'] = pd.to_datetime(surveys['clinical_self_report_data']['StartDate'], errors='raise')
session3['supplemental_self_report_data'] = pd.to_datetime(surveys['supplemental_self_report_data']['StartDate'], errors='raise')

subject_ids = session1['SUBJECT_ID'].unique()
print(f'session1 head:: len {len(session1)}')


session1['duration_mins'] = pd.to_numeric(session1['Duration (in seconds)'])/60
session1_r = session1[session1['SITE_ID']=='Rutgers']
session1_m = session1[session1['SITE_ID'] == 'McLean']

# ===============================================
# Compute Recoded Survey Totals (PANSS, YMRS, etc.)
# ===============================================
s1_recoded = recoded_surveys['clinical_administered_data']
panss_p_total_cols = [f'panss_p0{str(i)}' for i in range(1,8)]
panss_n_total_cols = [f'panss_n0{str(i)}' for i in range(1,8)]
panss_g_total_cols = [f'panss_g0{str(i)}' for i in range(1,8)]
bprs_total_cols = [f'bprs_0{str(i)}' for i in range(1,10)]+[f'bprs_1{i}' for i in range(0,9)]
ymrs_total_cols = [f'ymrs_0{str(i)}' for i in range(1,10)]+[f'ymrs_1{i}' for i in range(0,2)]
madrs_total_cols = [f'madrs_0{str(i)}' for i in range(1,10)]+['madrs_10']

all_cols = panss_p_total_cols+panss_n_total_cols+panss_g_total_cols+bprs_total_cols+ymrs_total_cols+madrs_total_cols
s1_recoded[all_cols] = s1_recoded[all_cols].astype(float)

s1_recoded_newcols = pd.DataFrame({
	'SUBJECT_ID':  s1_recoded['SUBJECT_ID'],
	'panss_p_total': s1_recoded[panss_p_total_cols].copy().sum(axis=1),
	'panss_n_total': s1_recoded[panss_n_total_cols].copy().sum(axis=1),
	'panss_g_total': s1_recoded[panss_g_total_cols].copy().sum(axis=1),
	'bprs_total': s1_recoded[bprs_total_cols].copy().sum(axis=1),
	'ymrs_total': s1_recoded[ymrs_total_cols].copy().sum(axis=1),
	'madrs_total': s1_recoded[madrs_total_cols].copy().sum(axis=1)
	})

s1_panss_total = pd.DataFrame({'panss_total': s1_recoded_newcols[['panss_p_total','panss_n_total','panss_g_total']].sum(axis=1)})
s1_recoded = pd.concat([s1_recoded_newcols, s1_panss_total], axis=1)

session1sr['duration_mins'] = pd.to_numeric(session1sr['Duration (in seconds)'])/60
session1sr_r = session1sr[session1sr['SITE_ID']=='Rutgers']
session1sr_m = session1sr[session1sr['SITE_ID'] == 'McLean']

session2['duration_mins'] = pd.to_numeric(session2['Duration (in seconds)'])/60
session2_r = session2[session2['SITE_ID']=='Rutgers']
session2_m = session2[session2['SITE_ID'] == 'McLean']

total_real = len(session1_r) + len(session1_m)

# Pie charts
primary_pie = px.pie(session1, names='primary_diagnoses_all', title=f'Subject Primary Diagnoses - {len(session1)} subjects')
other_pie = px.pie(session1, names='other_diagnoses_all', title=f'Subject Other Diagnoses - {len(session1)} subjects')

# ===============================================
# Merge All Sessions into a Unified Demographic DF
# ===============================================
survey_cols = [ "SUBJECT_ID",'SITE_ID','primary_diagnoses_all','other_diagnoses_all',
	'clinical_administered_data', 'mri_self_report_data','supplemental_self_report_data', 
	'MADRS_category','YMRS_category', 'PANSS_Positive_Category','PANSS_Negative_Category','PANSS_General_Category','PANSS_Total_category',
	"sex","age", "ethnic","racial","place_birth", 'name_meds','purpose_meds','panss_total', 'panss_p_total','panss_n_total','panss_g_total', 'bprs_total','ymrs_total','madrs_total',]

display_survey_cols = [col for col in survey_cols if 'total' not in col and 'Category' not in col and 'supplemental' not in col]
session0_merge = session1[[col for col in survey_cols if col in session1.columns]]
session1_merge = session1sr[[col for col in survey_cols if col in session1sr.columns]]
session2_merge = session2[[col for col in survey_cols if col in session2.columns]]
session3_merge = session3[[col for col in survey_cols if col in session3.columns]]
session1recoded_merge = s1_recoded[[col for col in survey_cols if col in s1_recoded.columns]]

# align on SUBJECT_ID first
s1 = session1_merge.set_index("SUBJECT_ID")
s2 = session2_merge.set_index("SUBJECT_ID")
s3 = session3_merge.set_index("SUBJECT_ID")
s0 = session0_merge.set_index("SUBJECT_ID")
srecoded = session1recoded_merge.set_index('SUBJECT_ID')
demographic_df = s1.combine_first(s2).combine_first(s3).combine_first(s0).combine_first(srecoded).reset_index()

# Add in session notes from notion tracker
notes_df = tracker_df.set_index('SUBJECT_ID')
notes_df = notes_df[['Session Notes','MRI scan notes']]
combined_df = demographic_df.combine_first(notes_df)

demographic_df = surveys_loader.categorize_scores(combined_df)
# Add the dates of the surveys to the dataframe
# demographic_df["clinical_administered_data"] = pd.to_datetime(surveys["clinical_administered_data"]['StartDate'], errors="coerce")
# demographic_df["mri_self_report_data"] = pd.to_datetime(surveys["mri_self_report_data"]['StartDate'], errors="coerce")
demographic_df = demographic_df.drop_duplicates()
today = dt.today()
today_str = today.strftime('%b %d %Y')
demographic_df.to_csv(os.path.join(demographic_df_dir, f'demographic_df_{today_str}.csv'))

# Define 2 weeks ago
two_weeks_ago = dt.now() - timedelta(weeks=2)
today_str = dt.now().strftime('%Y-%m-%d')
two_weeks_ago_str = two_weeks_ago.strftime('%Y-%m-%d')

# Filter
recent_cad = demographic_df[demographic_df['clinical_administered_data'] >= two_weeks_ago]
num_recent_clin = len(recent_cad)
recent_mri = demographic_df[demographic_df['mri_self_report_data'] >= two_weeks_ago]
num_recent_mri = len(recent_mri)
recent_demographics = pd.concat([recent_cad, recent_mri])
num_recent_subs = len(recent_demographics)


recent_demographics_clean = (
	recent_demographics.groupby("SUBJECT_ID")
	.agg(lambda x: ", ".join(x.dropna().astype(str).unique()))
	.reset_index())


mri = demographic_df[["SUBJECT_ID", "mri_self_report_data"]].copy()
mri = mri.dropna(subset=["mri_self_report_data"])

# Full date range
mri_date_range = pd.date_range(mri["mri_self_report_data"].min(), mri["mri_self_report_data"].max())

# Cumulative counts
mri_counts = mri["mri_self_report_data"].value_counts().sort_index()
cumulative_mri_counts = mri_counts.cumsum()
cumulative_mri = cumulative_mri_counts.reindex(mri_date_range, method='ffill').fillna(0)

last_mri_date = cumulative_mri.index.max()
last_mri_value = cumulative_mri.iloc[-1]

clin = demographic_df[["SUBJECT_ID", "clinical_administered_data"]].copy()
clin = clin.dropna(subset=["clinical_administered_data"])

# Full date range
clin_date_range = pd.date_range(clin["clinical_administered_data"].min(), clin["clinical_administered_data"].max())

# Cumulative counts
clin_counts = clin["clinical_administered_data"].value_counts().sort_index()
cumulative_clin_counts = clin_counts.cumsum()
cumulative_clin = cumulative_clin_counts.reindex(clin_date_range, method='ffill').fillna(0)

last_clin_date = cumulative_clin.index.max()
last_clin_value = cumulative_clin.iloc[-1]

## also RMR df is just defined in here 
rmr = pd.DataFrame({
	"Date": [
		"Apr 1 2025", "Aug 1 2025", "Dec 1 2025",
		"Apr 1 2026", "Aug 1 2026", "Dec 1 2026",
		"Apr 1 2027", "Aug 1 2027", "Dec 1 2027",
		"Apr 1 2028"
	],
	"Quarter": [
		"Q1", "Q2", "Q3", "Q4", "Q5",
		"Q6", "Q7", "Q8", "Q9", "Q10"
	],
	"Participants per site": [
		13, 14, 13, 14, 13,
		14, 13, 14, 13, 14
	]
})
# Add cumulative and total columns
rmr["Site Cumulative"] = rmr["Participants per site"].cumsum()
rmr["Total"] = rmr["Site Cumulative"] * 2
rmr["Date"] = pd.to_datetime(rmr["Date"])
rmr = rmr.set_index("Date")

# --- Interpolate expected totals to make it linear over time
rmr_linear = rmr["Total"].reindex(
	pd.date_range(rmr.index.min(), rmr.index.max(), freq="D")
).interpolate()

cutoff = last_mri_date + pd.Timedelta(days=180)
rmr_linear = rmr_linear.loc[:cutoff]



# Tracker Visual
subs_df = paths_dict['tracker_df']
subs_df_binary = subs_df.fillna(0)
subs_df_filtered = subs_df_binary.loc[subs_df_binary['Clinical Interview Session'] != 0, :]
subs_df_filtered = subs_df_filtered.loc[:, ~subs_df_filtered.columns.str.contains('Unnamed', case=False)]
tags_row = subs_df_filtered.iloc[0]

def filter_by_tag(df, tags_row, desired_tags):
	matching_cols = []
	for tag in desired_tags:
		matching = tags_row[tags_row.astype(str).str.contains(tag, na=False)].index.tolist()
		matching_cols.extend(matching)

	# Remove duplicates while preserving order
	matching_cols = list(dict.fromkeys(matching_cols))

	return df[matching_cols]

tracker_df = filter_by_tag(subs_df_filtered, tags_row, ['id','tracker'])

# # Now the structure is:
# # |PCR ID:  | SUBJECT_ID |     Session Date    |   Session Time     | <-- these are all columns in tracker
# # |tags     |  id     | tracker, scheduling | tracker, scheduling| ...
# # |PCR200   |qualr200 |     <value>         |       <value>      | ...


icons = {
	'up': "tabler:arrow-up-right",
	'down': "tabler:arrow-down-right",
}


r_prog = int((len(session1_r)/135)*100)
r_scans_prog = int((len(session2_r)/135)*100)
m_prog = int((len(session1_m)/135)*100)
m_scans_prog = int((len(session2_m)/135)*100)

data = [
	{'label': 'Rutgers Clinical Interview', 'stats': len(session1_r), 'progress': r_prog, 'color': 'red', 'icon': 'up'},
	{'label': 'Rutgers Scans', 'stats': len(session2_r), 'progress': r_scans_prog, 'color': 'red', 'icon': 'up'},
	{'label': 'McLean Clinical Interview', 'stats': len(session1_m), 'progress': m_prog, 'color': 'blue', 'icon': 'up'},
	{'label': 'McLean Scans', 'stats': len(session2_m), 'progress': m_scans_prog, 'color': 'blue', 'icon': 'up'},
]



def StatsRing():
	stats = []
	for stat in data:
		Icon = icons[stat['icon']]
		stats.append(
			dmc.Paper(
				children=[
					dmc.Group(
						children=[
							dmc.RingProgress(
								size=80,
								roundCaps=True,
								thickness=8,
								sections=[{'value': stat['progress'], 'color': stat['color']}],
								label=dmc.Center(
									DashIconify(icon=Icon, width=20, height=20)
								)
							),
							dmc.Box(
								children=[
									dmc.Text(stat['label'], c="dimmed", size="xs", tt="uppercase", fw=700),
									dmc.Text(str(stat['stats']), fw=700, size="xl"),
								]
							)
						]
					)
				],
				withBorder=True,
				radius="md",
				p="xs",
			)
		)

	return dmc.SimpleGrid(
		children=stats,
		cols={"base": 4, "sm": 1},
		p="lg"
	)



# App layout
layout = html.Div([
	dmc.MantineProvider(children=[
		dmc.Text('PCX Current Status',  c='blue', tt='uppercase',style={"fontSize": 40},),
		StatsRing(),
	   ],
	),
	dmc.MantineProvider(children=[
		dmc.Text(f'All Subject sessions from the last 2 weeks ({num_recent_clin} clinical interviews, {num_recent_mri} MRI scans)',  c='blue',style={"fontSize": 30}),
	html.Div(tables.render_demographic_df(recent_demographics, display_survey_cols)),
	dmc.MantineProvider(children=[
		dmc.Text('Current + Projected Clinical Interviews',  c='blue',style={"fontSize": 30}),
		dmc.Text(f'Currently our real rate is: {num_recent_clin/2} subjects per week (both sites, {num_recent_clin/4} per site)',  c='blue',style={"fontSize": 20})]),        
		dmc.Text(f'Adjust rate below to see the projected progress at different rates',  c='grey',style={"fontSize": 18})]),        
	dcc.Slider(
		id='weekly-rate-slider-clin',
		min=0,
		max=20,
		step=0.5,
		value=num_recent_clin/2,  # initial weekly rate autofilled as current real rate
		marks={i: str(i) for i in range(0, 6, 1)}),
	dcc.Graph(id='clin-done-graph'),

	dmc.MantineProvider(children=[
		dmc.Text('Current + Projected MRI Scans',  c='blue',style={"fontSize": 30}),
		dmc.Text(f'Currently our real rate is: {num_recent_mri/2} subjects per week (both {num_recent_mri/4} per site)',  c='blue',style={"fontSize": 20})]),
		dmc.Text(f'Adjust rate below to see the projected progress at different rates',  c='grey',style={"fontSize": 18}),
	dcc.Slider(
		id='weekly-rate-slider-mri',
		min=0,
		max=20,
		step=0.5,
		value=num_recent_mri/2,   # initial weekly rate autofilled as current real rate
		marks={i: str(i) for i in range(0, 6, 1)}),
	dcc.Graph(id='mri-done-graph'),
	dmc.Group(id='graphs', children=[
		html.Div(id='graphs', children=[
			dcc.Graph(figure=primary_pie, id='primary-pie'),
			dcc.Graph(figure=other_pie, id='other-pie'),
			]),
		]),
	# html.Div(id='duration-container', children=[
	#         dcc.RadioItems((['Rutgers', 'McLean']), id='site', value='Rutgers'),
	#         dcc.Tabs(id="session", value='Clinical Interview Session', children=[
	#             dcc.Tab(label='Clinical Interview Session', value='Clinical Interview Session'),
	#             dcc.Tab(label='Clinical Self-Report', value='Clinical Self-Report'),
	#             dcc.Tab(label='fMRI Self-Report', value='fMRI Self-Report'),
	#         ]),

	#         html.Div(id='table-duration', style={'width': 500,'padding': '5px'}),
	#         html.Div(id='chart-duration', style={'width': 500,'padding': '5px'}),
	# ]),

]),




# # Controls to filter the figure by subject ID and
# @callback(
#     Output('dashboard-graph', 'figure'),
#     Input('subject-id', 'data')
# )

# def cb(subject_id):
#     if subject_id is None:
#         filtered_df = tracker_df
#     else:
#         filtered_df = tracker_df[tracker_df['SUBJECT_ID'] == subject_id]
	
#     # Binarize non-zero values
#     filtered_df_bin = filtered_df.where(filtered_df == 0, 1)
#     #display(filtered_df_bin)
	
#     # Create the figure
#     fig = px.imshow(filtered_df_bin, origin='lower',
#                     title="Tasks Completed by Participants",
#                     zmin=0, zmax=1, color_continuous_scale=[[0, "white"], [1, "black"]],
#                     labels=dict(x="Tasks Completed", y="Subject", color="Done = Black"),
#                     x=filtered_df.columns,
#                     y=filtered_df['SUBJECT_ID'],
#                     width=1500, height=800)
#     return fig


@callback(
	Output('table-duration', 'children'),
	Output('chart-duration', 'children'),
	Input('site', 'value'),
	Input('session', 'value'),
)

def cb(site, session):
	if session=='Clinical Interview Session':
		if site=='McLean':
			df = session1_m
		else:
			df = session1_r
	if session=='Clinical Self-Report':
		if site=='McLean':
			df = session1sr_m
		else:
			df = session1sr_r
	if session=='fMRI Self-Report':
		if site=='McLean':
			df = session2_m
		else:
			df = session2_r
	cols = ['SUBJECT_ID','RecordedDate', 'duration_mins','primary_diagnoses_all', 'other_diagnoses_all']
	cols_present = [col for col in cols if col in df.columns]


	
	#Bar chart of duration for each sub
	fig = px.bar(df, x='SUBJECT_ID', y='duration_mins', text_auto='.2s', range_y=[0,120])

	return tables.render_demographic_df(df, cols_present), dcc.Graph(figure=fig,config={'displayModeBar': True},style={'width': 500,  'height': 300},  className = "outer-graph")



# -----------------------------
# Callback
# -----------------------------
@callback(
	Output('clin-done-graph', 'figure'),
	Input('weekly-rate-slider-clin', 'value')
)
def update_mri_graph(weekly_rate):
	# Convert weekly rate to daily
	daily_rate = weekly_rate / 7

	# Project next 180 days
	projection_dates = pd.date_range(start=last_clin_date + pd.Timedelta(days=1), periods=180)
	projected_values = last_clin_value + daily_rate * np.arange(1, 180)
	
	fig = go.Figure()
	# Actual cumulative
	fig.add_trace(go.Scatter(x=cumulative_clin.index, y=cumulative_clin.values,
							 mode='lines+markers', name='Actual Cumulative', line=dict(color='blue', width=1,)))
	# Projected
	fig.add_trace(go.Scatter(x=projection_dates, y=projected_values,
							 mode='lines', name='Projected (based on slider)', line=dict(color='blue', width=1, dash='dash')))

	fig.add_trace(go.Scatter(x=rmr_linear.index, y=rmr_linear.values,
							 mode='lines', name='RMR Goal Values', line=dict(color='orange', width=1)))

	# Highlight next quarter
	fig.add_vrect(x0=last_mri_date, x1=last_mri_date + pd.Timedelta(days=180),
				  fillcolor="gray", opacity=0.1, layer="below", line_width=0, annotation_text="Next Quarter")

	fig.update_layout(title=f"Actual vs Projected Clinical Interview Trajectory", 
					  xaxis_title="Date", yaxis_title="Cumulative Participants",
					  template="plotly_white", height=500)
	fig.update_layout(title_subtitle_text=f'At Weekly Rate {weekly_rate} subjects/week')
	return fig


@callback(
	Output('mri-done-graph', 'figure'),
	Input('weekly-rate-slider-mri', 'value')
)
def update_mri_graph(weekly_rate):
	# Convert weekly rate to daily
	daily_rate = weekly_rate / 7

	# Project next 180 days
	projection_dates = pd.date_range(start=last_mri_date + pd.Timedelta(days=1), periods=180)
	projected_values = last_mri_value + daily_rate * np.arange(1, 180)
	
	fig = go.Figure()
	# Actual cumulative
	fig.add_trace(go.Scatter(x=cumulative_mri.index, y=cumulative_mri.values,
							 mode='lines+markers', name='Actual Cumulative', line=dict(color='blue', width=1,)))
	# Projected
	fig.add_trace(go.Scatter(x=projection_dates, y=projected_values,
							 mode='lines', name='Projected (based on slider)', line=dict(color='blue', width=1, dash='dash')))

	fig.add_trace(go.Scatter(x=rmr_linear.index, y=rmr_linear.values,
							 mode='lines', name='RMR Goal Values', line=dict(color='orange', width=1)))

	# Highlight next quarter
	fig.add_vrect(x0=last_mri_date, x1=last_mri_date + pd.Timedelta(days=180),
				  fillcolor="gray", opacity=0.1, layer="below", line_width=0, annotation_text="Next Quarter")

	fig.update_layout(title=f"Actual vs Projected MRI Scan Trajectory", 
					  xaxis_title="Date", yaxis_title="Cumulative Participants",
					  template="plotly_white", height=500)
	fig.update_layout(title_subtitle_text=f'At Weekly Rate {weekly_rate} subjects/week')
	return fig


@callback(
	Output('shown-rate-text-clin', 'children'),
	Input('weekly-rate-slider-clin', 'value')
)
def update_shown_rate(weekly_rate):
	return f'Projected progress given weekly clincal rate of {weekly_rate} sessions per week: '


@callback(
	Output('shown-rate-text-mri', 'children'),
	Input('weekly-rate-slider-mri', 'value')
)
def update_shown_rate(weekly_rate):
	return f'Projected progress given weekly MRI rate of {weekly_rate} scans per week: '

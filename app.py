import dash
from dash import Dash, dcc, html, callback, Input, Output, dash_table
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import dash_mantine_components as dmc
import json
#external_stylesheet = dbc.themes.CERULEAN
subject_viewer_app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN], use_pages=True,  pages_folder="pages")

data=pd.read_excel('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/Subject_tracker_PCR.xlsx', sheet_name='clean_data')
subject_ids = data['PCR ID'].unique()

clinRatings=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_ClinicalVisit_ClinicianRatings/PCX_ClinicalVisit_ClinicianRatings_June 18, 2025_17.59.csv')
supp=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_SupplementalBattery/PCX_SupplementalBattery_June 18, 2025_17.12.csv')
fmriBattery=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_fMRIVisit_SelfReport/PCX_fMRIVisit_SelfReport_June 18, 2025_17.13.csv')
clinBattery=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_ClinicalVisit_ClinicianRatings/PCX_ClinicalVisit_ClinicianRatings_June 18, 2025_17.59.csv')


def create_sub(df, subject):
    sub_df=df[df['Qual ID']==subject].copy()
    sub_df=sub_df.reset_index()
    sub_str=sub_df.to_json()
    return sub_df, sub_str


def filter_subject(df, subject):
    return df[df['SUBJECT_ID']==subject]

def render_table(df, subject, survey_name=None, survey_regex=None):
    if survey_name:
        cols = [col for col in df.columns if survey_name in col and 'notes' not in col and 'total' not in col]
    survey_df = df[['SUBJECT_ID']+cols]
    mapping = dict(zip(survey_df.columns, survey_df.iloc[0]))
    sub_df = filter_subject(survey_df, subject)
    long_df = sub_df.melt(id_vars='SUBJECT_ID', var_name='name', value_name='value')
    long_df['label'] = long_df['name'].map(mapping)
    long_df = long_df[['label', 'value']]
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
        style_cell={'textAlign': 'left'}
        )        
    

def render_graph(df, subject, survey_name=None, survey_regex=None):
    if survey_name:
        cols = [col for col in df.columns if survey_name in col and 'notes' not in col and 'total' not in col]
    survey_df = df[['SUBJECT_ID']+cols]
    mapping = dict(zip(survey_df.columns, survey_df.iloc[0]))
    sub_df = filter_subject(survey_df, subject)
    long_df = sub_df.melt(id_vars='SUBJECT_ID', var_name='name', value_name='value')
    long_df['label'] = long_df['name'].map(mapping)
    long_df = long_df[['label', 'value']]
    long_df = long_df.sort_values('value', ascending=False)     
    fig = px.bar(long_df, x='label', y='value')
    
    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False}, 
        style={'width': '100%',  'height': '100%' },  className = "outer-graph",
    )

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# Sidebar with navigation
sidebar = html.Div(
    [
        html.H2("PCX Study", className="display-4"),
        html.Hr(),
        html.P("Interactive dashboard for the PCX study.", className="lead"),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("By Subject", href="/passive_data", active="exact"),
                dbc.NavLink("Dashboard", href="/surveys", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

subject_viewer_app.layout = html.Div([
    sidebar,
    html.H1(children='Subject Viewer', style={'margin':20}),
    html.Div(children=[
        html.Div(children=[
            dcc.Store(id='subject-id'),
            dcc.Store(id='subject-dict'),
            html.Div("Use this dropdown to select the subject"),
            dcc.Dropdown(subject_ids, id='subject-picker',clearable=False, value='qualr200'),
            dcc.Markdown(id='caption'),
        ], style={'width': '48%', 'float': 'left', 'display': 'inline-block'}),
        html.Div(children=[
            dcc.RadioItems(['Table', 'Graph'], id='content-type', value='Table'),
            dcc.Tabs(id="tabs", value='rsri', children=[
                dcc.Tab(label='RSRI', value='rsri'),
                dcc.Tab(label='PANSS', value='panss'),
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
        Input('tabs', 'value'),
        Input('content-type', 'value'),
        Input('subject-id', 'data'),
)
def render_content(tab, content, subject):
    if content=='Table':
        render_table(df, subject, survey_name=tab)
        #return html.Div(f'Table ({content} for tab {tab} for subject {subject})')
    if content=='Graph':
        #render_graph(df, subject, survey_name=tab)
        #return html.Div(f'Graph ({content} for tab {tab} for subject {subject})')
        if tab:
            cols = [col for col in df.columns if tab in col and 'notes' not in col and 'total' not in col]
        survey_df = df[['SUBJECT_ID']+cols]
        mapping = dict(zip(survey_df.columns, survey_df.iloc[0]))
        sub_df = filter_subject(survey_df, subject)
        long_df = sub_df.melt(id_vars='SUBJECT_ID', var_name='name', value_name='value')
        long_df['label'] = long_df['name'].map(mapping)
        long_df = long_df[['label', 'value']]
        long_df = long_df.sort_values('value', ascending=False)     
        fig = px.bar(long_df, x='label', y='value')
            
        dcc.Graph(
            figure=fig,
            config={'displayModeBar': False}, 
            style={'width': '100%',  'height': '100%' },  className = "outer-graph",
        )
    
if __name__ == '__main__':
    subject_viewer_app.run(debug=True, jupyter_mode="external", port=8050)
    

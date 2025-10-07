import os
import sys
import re
import dash
from dash import html, dcc, callback, Input, Output
import plotly 
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import xarray as xr
import importlib
import logging
import pickle
import inspect

# Set project dir in a consistent way with app.py
project_dir = os.getcwd()
basename = os.path.basename(os.getcwd())
sys.path.append(basename)

# Import custom scripts
from scripts.update_dataframes import update_dfs
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])
from scripts.utils import fig_layout

# Register page into dash app as pagename
dash.register_page(__name__, path="/subject")

# Set up logging
logging.basicConfig(
    filename='subject.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

# Function to load data consistent with app.py's approach
def load_data():
    try:
        # Update DFs using the same function as in app.py
        subs_df, mindlamp_df, selected_cols, readable_cols = update_dfs(project_dir)
        
        # Create dataframes for each sensor
        power_df = mindlamp_df[mindlamp_df['sensor'] == 'power'] if 'sensor' in mindlamp_df.columns else pd.DataFrame()
        accel_df = mindlamp_df[mindlamp_df['sensor'] == 'accel'] if 'sensor' in mindlamp_df.columns else pd.DataFrame()
        gps_df = mindlamp_df[mindlamp_df['sensor'] == 'gps'] if 'sensor' in mindlamp_df.columns else pd.DataFrame()
        
        return subs_df, mindlamp_df, power_df, accel_df, gps_df, selected_cols, readable_cols
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        # Return empty dataframes if there's an error
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), [], []

# Load data
subs_df, mindlamp_df, power_df, accel_df, gps_df, selected_cols, readable_cols = load_data()

# App layout with styling consistent with app.py
layout = html.Div([
    html.H1('Data by Subject', style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    html.Div([
        html.Div([
            dcc.Dropdown(
                id="subject_id", 
                value=power_df['subject_id'].unique()[0] if not power_df.empty and 'subject_id' in power_df.columns else None, 
                clearable=False,
                options=[{"label": f'{y}', "value": y} for y in power_df['subject_id'].unique()] if not power_df.empty and 'subject_id' in power_df.columns else [],
                style={'width': '100%'}
            )
        ], style={'width': '70%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.RadioItems(
                id='days', 
                value='All days', 
                options=['All days', 'Weekdays', 'Weekends'],
                inline=True,
                style={'marginLeft': '20px'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ], style={'display': 'flex', 'marginBottom': '20px'}),
    
    html.Div([
        dcc.Graph(figure={}, id='phone_use-graph', style={'height': '400px'}),
        dcc.Graph(figure={}, id='daily_phoneuse-graph', style={'height': '400px'}),
        dcc.Graph(figure={}, id='activity-graph', style={'height': '400px'}),
        dcc.Graph(figure={}, id='gps-graph', style={'height': '400px'})
    ])
])

# Callbacks with unique names to avoid conflicts
@callback(
    Output(component_id='phone_use-graph', component_property='figure'),
    Input(component_id='subject_id', component_property='value'),
    Input(component_id='days', component_property='value')
)
def update_phone_use_graph(subject_id, days):
    """Callback to update the phone use graph based on the selected id"""
    if power_df.empty or 'subject_id' not in power_df.columns or not subject_id:
        # Return empty figure with message if no data
        fig = go.Figure()
        fig.update_layout(
            title="No phone use data available",
            annotations=[{
                'text': "No phone activity data loaded. Please check data files.",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    sub = subject_id
    sub_df = power_df.query("subject_id == @sub")
    
    if sub_df.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.update_layout(
            title=f"No phone use data for {sub}",
            annotations=[{
                'text': f"No phone activity data found for {sub}",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    
    # Check if we still have data after filtering
    if sub_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"No {days.lower()} phone use data for {sub}",
            annotations=[{
                'text': f"No {days.lower()} phone activity data found for {sub}",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    try:
        xr_power = xr.DataArray(sub_df[selected_cols].values, 
                            dims=["Days", "Hours of the Day"],
                            coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
        
        # Create figure using plotly graph objects for consistency with app.py
        fig = go.Figure()
        
        # Add heatmap
        fig.add_trace(
            go.Heatmap(
                z=xr_power.values,
                x=readable_cols,
                y=sub_df['day'],
                colorscale='viridis',
                zmin=0,
                zmax=60
            )
        )
        
        # Update layout to be consistent with app.py style
        fig.update_layout(
            title=f'Phone Activity (minutes each hour) for {sub}',
            xaxis_title="Hours of the Day",
            yaxis_title="Days",
            height=400,
            template="plotly_white"
        )
    except Exception as e:
        logging.error(f"Error creating phone use graph: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating phone use graph",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 16}
            }]
        )
    
    return fig

@callback(
    Output(component_id='daily_phoneuse-graph', component_property='figure'),
    Input(component_id='days', component_property='value')
)
def update_daily_phoneuse_graph(days):
    """Callback to update the daily phone use graph"""
    if power_df.empty or 'daily_mins' not in power_df.columns:
        # Return empty figure with message if no data
        fig = go.Figure()
        fig.update_layout(
            title="No daily phone use data available",
            annotations=[{
                'text': "No daily phone activity data loaded. Please check data files.",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    if days == 'All days':
        power_df_filtered = power_df
    elif days == 'Weekdays':
        power_df_filtered = power_df[power_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        power_df_filtered = power_df[power_df['weekday'].astype(str).str.contains('6|7')]
    
    # Check if we have data after filtering
    if power_df_filtered.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"No {days.lower()} daily phone use data available",
            annotations=[{
                'text': f"No {days.lower()} daily phone activity data found",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    try:
        # Create figure using plotly graph objects for consistency with app.py
        fig = go.Figure()
        
        # Add lines for each subject
        for subject in power_df_filtered['subject_id'].unique():
            subject_data = power_df_filtered[power_df_filtered['subject_id'] == subject]
            fig.add_trace(
                go.Scatter(
                    x=subject_data['day'],
                    y=subject_data['daily_mins'],
                    mode='lines+markers',
                    name=subject
                )
            )
        
        # Update layout to be consistent with app.py style
        fig.update_layout(
            title=f'Phone Activity (minutes each day) for {days}',
            xaxis_title="Day",
            yaxis_title="Minutes",
            height=400,
            template="plotly_white",
            legend_title="Subject ID"
        )
    except Exception as e:
        logging.error(f"Error creating daily phone use graph: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating daily phone use graph",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 16}
            }]
        )
    
    return fig

@callback(
    Output(component_id='activity-graph', component_property='figure'),
    Input(component_id='subject_id', component_property='value'),
    Input(component_id='days', component_property='value')
)
def update_activity_graph(subject_id, days):
    """Callback to update the activity graph based on the selected id"""
    if accel_df.empty or 'subject_id' not in accel_df.columns or not subject_id:
        # Return empty figure with message if no data
        fig = go.Figure()
        fig.update_layout(
            title="No activity data available",
            annotations=[{
                'text': "No activity data loaded. Please check data files.",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    sub = subject_id
    sub_df = accel_df.query("subject_id == @sub")
    
    if sub_df.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.update_layout(
            title=f"No activity data for {sub}",
            annotations=[{
                'text': f"No activity data found for {sub}",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    
    # Check if we still have data after filtering
    if sub_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"No {days.lower()} activity data for {sub}",
            annotations=[{
                'text': f"No {days.lower()} activity data found for {sub}",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    try:
        xr_activity = xr.DataArray(sub_df[selected_cols].values, 
                          dims=["Days", "Hours of the Day"],
                          coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
        
        # Create figure using plotly graph objects for consistency with app.py
        fig = go.Figure()
        
        # Add heatmap
        fig.add_trace(
            go.Heatmap(
                z=xr_activity.values,
                x=readable_cols,
                y=sub_df['day'],
                colorscale='viridis',
                zmin=0,
                zmax=60
            )
        )
        
        # Update layout to be consistent with app.py style
        fig.update_layout(
            title=f'Physical Activity (acceleration speed) minutes each hour for {sub}',
            xaxis_title="Hours of the Day",
            yaxis_title="Days",
            height=400,
            template="plotly_white"
        )
    except Exception as e:
        logging.error(f"Error creating activity graph: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating activity graph",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 16}
            }]
        )
    
    return fig

@callback(
    Output(component_id='gps-graph', component_property='figure'),
    Input(component_id='subject_id', component_property='value'),
    Input(component_id='days', component_property='value')
)
def update_gps_graph(subject_id, days):
    """Callback to update the GPS graph based on the selected id"""
    if gps_df.empty or 'subject_id' not in gps_df.columns or not subject_id:
        # Return empty figure with message if no data
        fig = go.Figure()
        fig.update_layout(
            title="No GPS data available",
            annotations=[{
                'text': "No GPS data loaded. Please check data files.",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    sub = subject_id
    sub_df = gps_df.query("subject_id == @sub")
    
    if sub_df.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.update_layout(
            title=f"No GPS data for {sub}",
            annotations=[{
                'text': f"No GPS data found for {sub}",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    
    # Check if we still have data after filtering
    if sub_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"No {days.lower()} GPS data for {sub}",
            annotations=[{
                'text': f"No {days.lower()} GPS data found for {sub}",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return fig
    
    try:
        xr_gps = xr.DataArray(sub_df[selected_cols].values, 
                           dims=["Days", "Hours of the Day"],
                           coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
        
        # Create figure using plotly graph objects for consistency with app.py
        fig = go.Figure()
        
        # Add heatmap
        fig.add_trace(
            go.Heatmap(
                z=xr_gps.values,
                x=readable_cols,
                y=sub_df['day'],
                colorscale='viridis',
                zmin=0,
                zmax=60
            )
        )
        
        # Update layout to be consistent with app.py style
        fig.update_layout(
            title=f'Mobility (distance each hour) for {sub}',
            xaxis_title="Hours of the Day",
            yaxis_title="Days",
            height=400,
            template="plotly_white"
        )
    except Exception as e:
        logging.error(f"Error creating GPS graph: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating GPS graph",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 16}
            }]
        )
    
    return fig
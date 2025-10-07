import os
import sys
import dash
from dash import Dash, dcc, html, Input, Output, ALL, Patch, callback, _dash_renderer, no_update, ctx, State, set_props
_dash_renderer._set_react_version("18.2.0")
import dash_bootstrap_components as dbc
import logging
import importlib
import pandas as pd
import json
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
import warnings
import glob
import numpy as np
import re
warnings.simplefilter(action='ignore', category=DeprecationWarning)

# Import custom scripts
basename = os.path.basename(os.getcwd())
sys.path.append(basename)
from scripts import utils
from scripts.utils import iconify, CheckboxChip, expendable_box, fig_layout
from scripts.sidebar_layout import sidebar
from scripts.client_side_callbacks import drawer_sidebar_togle, theme_switcher_callback
from components.shadowbox import ShadowBox

if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])

import scripts.sub_id as sub_id
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])

import scripts.update_dataframes as dfs
if 'scripts.update_dataframes' in sys.modules:
    importlib.reload(sys.modules['scripts.update_dataframes'])


# Create app
app = Dash(__name__, use_pages=True, pages_folder="pages", external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Activity Score Dashboard"


# Load the data
project_dir = os.getcwd()
logging.info(f"PROJECT DIR: {project_dir}")
mindlamp_df, subs_df, selected_cols, readable_cols = dfs.update_dfs(project_dir)

# Create dataframes for each sensor
power_df = mindlamp_df[mindlamp_df['sensor'] == 'power'] if 'sensor' in mindlamp_df.columns else pd.DataFrame()
accel_df = mindlamp_df[mindlamp_df['sensor'] == 'accel'] if 'sensor' in mindlamp_df.columns else pd.DataFrame()
gps_df = mindlamp_df[mindlamp_df['sensor'] == 'gps'] if 'sensor' in mindlamp_df.columns else pd.DataFrame()

# Get unique subjects
subjects = [str(item) for item in mindlamp_df['subject_id'].unique() if item]
subject_groups = ['group1', 'group2']  # Default groups, can be customized

# Create a dictionary of human-readable column names
legend = pd.DataFrame({
    'field': ['weekday', 'day', 'sensor'],
    'readable_name': ['Day of Week', 'Day of Study', 'Sensor Type']
})

_filters = dict(zip([i for i in legend['field'].to_list()], legend['readable_name']))

# Add sensor selector at the top
sensor_selector = dmc.SegmentedControl(
    id="sensor-selector",
    value="gps",
    data=[
        {"value": "gps", "label": "GPS"},
        {"value": "power", "label": "Power"},
        {"value": "accel", "label": "Accelerometer"}
    ],
    size="md",
    radius="xl",
    style={"marginBottom": "15px", "width": "300px"}
)

# Helper functions
def make_filter(filters):
    s = ""
    for key, value in filters.items():
        if value:
            s = s + f"`{key}` == {value} & "
    if s:
        s = s[:-3]
    return s


def filter_df(df, subjects, feature, sub, selected_sensor=None):
    # Filter by subjects
    df = df[df[sub].isin(subjects)]
    
    # Filter by sensor if specified
    if selected_sensor:
        df = df[df['sensor'] == selected_sensor]
    
    # Group by feature if specified
    if feature:
        groupby = [sub, feature]
    else:
        groupby = [sub]

    # Aggregate data
    df = df.groupby(groupby).agg(
        days=('day', 'nunique'),
        daily_mins=('daily_mins', 'sum'),
    ).reset_index()
    
    return df


def _underscores(text):
    parts = text.split('_')
    result = []

    for i, part in enumerate(parts):
        result.append(part)
        if i < len(parts) - 1:  
            if i % 2 == 0:
                result.append(' ')
            else:
                result.append('<br>')

    return ''.join(result)


def make_data_traces(df, feature, subject_group):
    data = []
    if feature:
        groups = df[feature].unique()
        for c in groups:
            _f = df[df[feature] == c] 
            data.append(
                go.Bar(name=str(c), x=_f[subject_group], y=_f['daily_mins'], marker=dict(line=dict(width=0.01))),
            )
    else:
        data.append(
            go.Bar(x=df[subject_group], y=df['daily_mins'], marker=dict(line=dict(width=0.01))),
        )
    return data


def make_hourly_heatmap(df, subject_id, selected_sensor):
    # Filter the dataframe for the selected subject and sensor
    subject_df = df[(df['subject_id'] == subject_id) & (df['sensor'] == selected_sensor) & (df['type']=='activityScores')]
    
    if subject_df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title=f"No hourly activity data for {subject_id} - {selected_sensor}",
            height=300
        )
        return fig
    
    # Get the hour columns
    hour_cols = [col for col in subject_df.columns if col.startswith('activityScore_hour')]
    
    # Create a matrix for the heatmap (days x hours)
    heat_data = []
    y_labels = []
    
    for _, row in subject_df.iterrows():
        day_values = [row[col] if not pd.isna(row[col]) else 0 for col in hour_cols]
        heat_data.append(day_values)
        y_labels.append(f"Day {int(row['day'])}")
    
    # Create the heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heat_data,
        x=[f"Hour {i+1}" for i in range(len(hour_cols))],
        y=y_labels,
        colorscale='Viridis',
        colorbar=dict(title='Activity Score')
    ))
    
    fig.update_layout(
        title=f"Hourly Activity Scores - {subject_id} - {selected_sensor}",
        height=300,
        yaxis=dict(autorange="reversed")  # To have day 1 at the top
    )
    
    return fig


shadow_box = dmc.CheckboxGroup(
    id="sub-graphs-chips",
    value=[],
    children=[
        dmc.Box(
            mt=35,
            style={'whiteSpace': 'nowrap'},
            children=ShadowBox().layout(
                children=[
                    dmc.Box(
                        style={
                            'boxShadow': 'rgba(219, 166, 232, 0.1) 0px 3px 12px',
                            "borderRadius": '20px',
                            "margin": '10px 10px',
                            "padding": '5px 10px 5px 0px',
                        },
                        children=[
                            CheckboxChip(label=f"{i}", value=f"{i}", size='lg', className='check-box-group-id')
                        ]
                    )
                    for i in _filters
                ]
            )
        )
    ]
)

search_component = dmc.Box(
    id="outer-search",
    style={
        'position': 'fixed',
        'left': '50%',
        'top': '0px',
        'transform': 'translateX(-50%)',
        'zIndex': 10000
    },
    children=[
        dmc.Popover(
            width=650,
            position="bottom-start",
            withArrow=False,
            shadow="md",
            transitionProps={
                "transition": "slide-up",
                "duration": 200,
                "timingFunction": "ease"
            },
            zIndex=2000,
            children=[
                dmc.PopoverTarget(
                    dmc.Box(
                        p=15,
                        w=650,
                        children=[
                            dmc.TextInput(
                                leftSection=iconify(icon="iconamoon:search-thin"),
                                rightSection=dmc.SegmentedControl(
                                    id='segmented-product-or-category',
                                    value="Subject",
                                    data=[
                                        {
                                            "value": "Subject", 
                                            "label": dmc.Center([
                                                iconify(icon='iconamoon:category-thin', width=16), 
                                                html.Span('Subject')
                                            ], style={"gap": 10})
                                        },
                                        {
                                            "value": "Group", 
                                            "label": dmc.Center([
                                                iconify(icon='weui:shop-outlined', width=16), 
                                                html.Span('Group')
                                            ], style={"gap": 10})
                                        },
                                    ],
                                    size='xs',
                                    radius='lg'
                                ),
                                id='input-box',
                                placeholder='Search by Subject ID or Group',
                                styles={
                                    "root": {
                                        'boxShadow': 'rgba(100, 100, 111, 0.2) 0px 7px 29px 0px',
                                        'borderRadius': '20px',
                                        'position': 'relative',
                                        'zIndex': 10000
                                    },
                                    "input": {'height': '45px', 'borderRadius': '20px'},
                                    "section": {'padding': '10px', 'width': 'auto'}
                                }
                            )
                        ]
                    )
                ),
                dmc.PopoverDropdown(
                    id='search-output',
                    style={
                        'marginTop': '-80px', 'paddingTop': '70px',
                        'borderRadius': '20px 20px 10px 10px'
                    },
                    styles={"root": {'boxShadow': 'rgba(100, 100, 111, 0.2) 0px 7px 29px 0px'}},
                    children=dmc.CheckboxGroup(
                        id="search-checkbox-group",
                        children=[],
                        value=[]
                    )
                )
            ]
        )
    ]
)

back = dmc.Paper(
    h='100%',
    w='100%',
    shadow='xs',
    radius='lg',
    pos='relative',
    className='bg-switch-darker',
    id='sub-graphs',
    children=[]
)

# Add hourly heatmap view
hourly_view = dmc.Paper(
    h='100%',
    w='100%',
    shadow='xs',
    radius='lg',
    pos='relative',
    className='bg-switch-darker',
    id='hourly-view',
    style={'marginTop': '20px'},
    children=[]
)

content = dmc.Box(
    id='content',
    children=[
        dmc.Box(
            id='main-content-top-section',
            children=[
                # Add sensor selector to the top
                dmc.Box(
                    style={'display': 'flex', 'justifyContent': 'bottom', 'margin': '20px 0'},
                    children=[sensor_selector]
                ),
                dmc.ActionIcon(
                    id='color-scheme-toggle',
                    n_clicks=0,
                    variant="transparent",
                    style={'position': 'absolute', 'right': '0px', 'top': '1px'},
                ),
                dmc.ActionIcon(
                    size="md",
                    variant="transparent",
                    id="drawer-sidebar-button",
                    n_clicks=0,
                ),
                search_component,
                shadow_box,
            ]
        ),
        dmc.Box(
            id='main-content-graph-section',
            p='10px',
            style={'position': 'relative', 'width': '100%', 'height': '100%'},
            children=[
                back,
                hourly_view
            ]
        )
    ]
)

app.layout = dmc.MantineProvider(
    id="mantine-provider",
    children=[
        dmc.Box(
            children=[
                sidebar(subs_df, _filters),
                content,
                dcc.Store(id='sto', data={'initial': 'my data'}),
                dcc.Store(id='selected-subject', data=None),
                dash.page_container
            ]
        )
    ]
)


@callback(
    Output("search-checkbox-group", "children"),
    Input('input-box', 'value'),
    Input('segmented-product-or-category', 'value'),
    Input("search-checkbox-group", "value"),
    prevent_intial_call=True
)
def update_output(value, segmented, selected_products):
    if ctx.triggered_id == 'segmented-product-or-category':
        set_props("map-select-product", {'value': []})
        set_props("map-select-product", {'data': []})
        selected_products = []
        
    if ctx.triggered_id == 'search-checkbox-group':
        if selected_products:
            set_props("map-select-product", {'value': selected_products[-1]})
        set_props("map-select-product", {'data': selected_products})
        
    if segmented == 'Subject':
        items = subjects
    else:
        items = subject_groups

    def found_items(items):
        return dmc.ScrollArea(
            h=350,
            w='100%',
            mt=10,
            children=dmc.Stack(
                children=[
                    dmc.Checkbox(
                        label=str(i).replace("_", " ").title(),
                        value=i,
                        size='sm',
                        styles={"label": {"paddingInlineStart": 8, 'color': 'gray'}}
                    )
                    for i in items
                ]
            )
        )

    if value:
        return found_items(
            sorted(set(sorted([i for i in items if value.lower() in i.lower()])[:30] + selected_products))
        )

    return found_items(
        sorted(set(items[:30] + selected_products))
    )


def make_bar_chart(df, subjects, feature, subject_group, selected_sensor):
    # Filter data based on selected sensor and other criteria
    df = filter_df(df, subjects, feature, subject_group, selected_sensor)
    
    if df.empty:
        # Return a message if no data
        return dmc.Box(
            style={'width': '100%', 'height': '50%', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'},
            p='2%',
            children=[
                dmc.Text(f"No data available for the selected {subject_group} and {selected_sensor} sensor", align="center")
            ]
        )
    
    df[subject_group] = df[subject_group].apply(_underscores)
    data = make_data_traces(df, feature, subject_group)

    fig = go.Figure(
        data=data,
        layout=fig_layout
    )
    fig.update_layout(
        legend=dict(orientation="h"),
        title=f"{selected_sensor.upper()} Activity - Daily Minutes"
    )
    
    g = dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={'width': '100%', 'height': '100%'},
        className="outer-graph",
        id={"type": "activity-graph", "index": feature if feature else 'overall'}
    )
    
    return dmc.Box(
        style={'width': '100%', 'height': '50%', "position": "relative"},
        p='2%',
        id={"type": "maximize-graph", "index": 'my_index' if not feature else feature},
        children=[
            dcc.Store(id={"type": "remember-graph-setting", "index": 'my_index' if not feature else feature}),
            dmc.ActionIcon(
                iconify('system-uicons:fullscreen', width=15),
                size="lg",
                style={"position": "absolute", "right": "0px", "top": "0px"},
                variant="subtle",
                id={"type": "action-maximize-graph", "index": 'my_index' if not feature else feature},
                n_clicks=0,
            ),
            dmc.Paper(
                p=5,
                style={'width': '100%', 'height': '100%', 'borderRadius': '15px'},
                shadow='sm',
                children=[g]
            )
        ]
    )


@callback(
    Output("sub-graphs", "children"),
    Output("selected-subject", "data"),
    Input({"type": "checkbox-options", "index": ALL}, "value"),
    Input("search-checkbox-group", "value"),
    Input('sub-graphs-chips', 'value'),
    Input('segmented-product-or-category', 'value'),
    Input("sensor-selector", "value"),
    State("selected-subject", "data"),
    prevent_intial_call=True
)
def display_output(_filters, subjects, features, subject_group, selected_sensor, selected_subject):
    if not subjects:
        return [], None
    
    # Process filters
    converted_dict = {item['id']['index']: item.get('value') for item in ctx.inputs_list[0] if item.get('value')}
    filters = make_filter(converted_dict)

    if filters:
        df = mindlamp_df.query(filters)
    else:
        df = mindlamp_df
    
    # Store the first subject for hourly view
    new_selected_subject = subjects[0] if subjects else None
    
    _children = Patch()

    if not features:
        g = make_bar_chart(df, subjects, '', subject_group, selected_sensor)
        _children.clear()
        _children.append(g)
    else:
        _children.clear()
        for feature in features:
            g = make_bar_chart(df, subjects, feature, subject_group, selected_sensor)
            _children.append(g)

    return _children, new_selected_subject


@callback(
    Output("hourly-view", "children"),
    Input("selected-subject", "data"),
    Input("sensor-selector", "value"),
    prevent_intial_call=True
)
def update_hourly_view(selected_subject, selected_sensor):
    if not selected_subject:
        return []
    
    fig = make_hourly_heatmap(mindlamp_df, selected_subject, selected_sensor)
    
    return dmc.Box(
        style={'width': '100%', 'height': 'auto'},
        children=[
            dmc.Text(f"Hourly Activity for {selected_subject}", size="lg", weight=500, align="center", mb=10),
            dcc.Graph(
                figure=fig,
                config={'displayModeBar': False},
                style={'width': '100%'}
            )
        ]
    )


@callback(
    Output({"type": "activity-graph", "index": ALL}, "clickData"),
    Input({"type": "activity-graph", "index": ALL}, "clickData"),
    State("selected-subject", "data"),
    prevent_intial_call=True
)
def handle_graph_click(click_data, current_subject):
    # Find which graph was clicked and get the subject ID
    if any(click_data):
        for i, data in enumerate(click_data):
            if data:
                # Extract subject ID from clicked point
                try:
                    subject_id = data['points'][0]['x'].split()[0]  # Get first part before space
                    # Update selected subject
                    set_props("selected-subject", {'data': subject_id})
                    # Reset click data for all graphs
                    return [None] * len(click_data)
                except (KeyError, IndexError):
                    pass
    
    # If no valid click, return unchanged
    return dash.no_update


ShadowBox().callback()
drawer_sidebar_togle()
theme_switcher_callback()

# Set up logging
logging.basicConfig(
    filename='app.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(pathname)s - %(message)s'
)

if __name__ == "__main__":
    app.run(debug=True, port=8090)
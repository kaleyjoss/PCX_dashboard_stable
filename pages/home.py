import dash
from dash import html, Input, Output, callback, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import logging


dash.register_page(__name__, 
    path='/', # these 3 are automatically generated like this, but you can edit them
    title='Home',
    name='Home'
)

layout = dbc.Container([
    html.H1("Home Page"),
    dbc.Col([
        dcc.Link('Go to Data by Subject', href='/subject'),
        html.Br(),
        dcc.Link('Go to Dashboard', href='/dashboard'),
        html.Br(),
    ])
])
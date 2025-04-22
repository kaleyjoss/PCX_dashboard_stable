import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import logging



# Create app
app = Dash(__name__, use_pages=True, pages_folder="pages", external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "My Multi-Page App"
# Sidebar styling
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
                dbc.NavLink("By Subject", href="/subject", active="exact"),
                dbc.NavLink("Dashboard", href="/dashboard", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

# Content area where page content will be rendered
content = html.Div(dash.page_container, style=CONTENT_STYLE)

# Final layout
app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content
])



# Set up logging
logging.basicConfig(
    filename='app.log',        # File to write logs to, saved in working directory
    filemode='a',              # 'a' for append, 'w' to overwrite each time
    level=logging.INFO,        # Minimum logging level
    format='%(asctime)s - %(pathname)s - %(message)s'
)

if __name__ == "__main__":
    app.run(debug=True, port=8090)

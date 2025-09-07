
from dash_iconify import DashIconify 
import pandas as pd
from dash import dcc, html
import dash_mantine_components as dmc
import dash_ag_grid as dag
import os
from datetime import datetime as dt
import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")



def extract_survey_date(filename: str):
    """
    Extracts a survey date from a filename of the form '..._<Month Day, Year>.csv'
    Example: 'survey_results_Sep 06, 2025.csv' → datetime(2025, 9, 6)
    """
    try:
        # Grab the last part after the last underscore, before the extension
        datestr = filename.split('_')[-1].split('.')[0]
        return dt.strptime(datestr, '%b %d, %Y')
    except Exception:
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
            

    if len(dates) > 0:
        dates.sort(key=lambda file: file['date'], reverse=True)

        return os.path.join(directory, dates[0]['filename'])
    
    return None


def iconify(icon, color = 'dark', width=20, cN = '_'):
    return DashIconify(
        icon=icon,  
        color=color, 
        width = width, 
        className=cN
    )

def badge(children, color = 'dark'):
    return dmc.Badge(
        children=children,  
        color=color, 
    )

def CheckboxChip(label, value, **kwargs):
    return dmc.Checkbox(
        **kwargs,
        label=label, 
        value=value, 
        p = 0,
        iconColor = 'blue',
        # size = 'lg',
        
        styles = {
                "input": {
                    "display":'none', "height":'50px',   "padding":'5px 15px 5px 0px', 
                },
                "label": {
                    "cursor":'pointer',
                "padding":'0px 15px 0px 0px', "fontSize" :'14px',  'display': 'inline-block', 'color': 'gray',
                },
            }
    )
def expendable_box(id, rootClass, titleText, children):
    return dmc.Paper(
        id=id,
        shadow='md',
        className=rootClass,
        children=[
            dmc.Box(titleText, className="vertical-text"),
            dmc.Box(titleText, className="horizontal-text"),
            dmc.Box(children=children, className="children-content")
        ]
    )

fig_layout = dict(
    yaxis_tickprefix = '$ ', 
    barcornerradius=15,
    font=dict(
        family="verdana, arial, sans-serif",
        size=14,
        color='gray'
    ),
        template="plotly_white" ,     
        autosize = True,
        margin=dict( t=0, b=20),
)
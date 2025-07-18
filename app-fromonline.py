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
warnings.simplefilter(action='ignore', category=DeprecationWarning)

# Import custom scripts
project_dir = os.path.basename(os.getcwd())
sys.path.append(project_dir)
from scripts import update_dataframes
importlib.reload(update_dataframes)
from scripts import utils
from scripts.utils import iconify, CheckboxChip, expendable_box, fig_layout
from scripts.sidebar_layout import sidebar
from scripts.client_side_callbacks import drawer_sidebar_togle, theme_switcher_callback
from components.shadowbox import ShadowBox
from components.flipcard import FlipCard
from scripts.update_dataframes import update_dfs
import scripts.paths as paths
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])



# Create app
app = Dash(__name__, use_pages=True, pages_folder="pages", external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "My Multi-Page App"


# Set PCX Project Data path
pcx_dir = os.path.expanduser("~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2")

# Update DFs
subs_df, mindlamp_df, selected_cols, readable_cols = update_dfs(pcx_dir)
power_df = mindlamp_df[mindlamp_df['sensor']=='power']
accel_df = mindlamp_df[mindlamp_df['sensor']=='accel']
gps_df = mindlamp_df[mindlamp_df['sensor']=='gps']


subjects =   [str(item )for item in mindlamp_df['subject_id'].unique() if item ]
subject_groups = ['group1', 'group2']

legend = pd.read_csv("data/readable_names.csv", header=0)

_filters= dict(zip([i for i in legend['field'].to_list()],legend['readable_name']))

# Helper functions
def make_filter(filters):
    s = ""
    for key, value in filters.items():
        if value:
            s = s + f"`{key}` == { value} & "
    s = s[:-3]
    return s


def filter_df(df, subjects,  feature, sub):

    df = df[df[sub].isin(subjects)]
    if feature:
        groupby = [sub, feature]

    else:
        groupby = sub

# #change -- this needs to filter differently for my df / uses 
    df = df.groupby(groupby).agg(
        days=('Days', 'count'),
        daily_mins=('Daily Sum of Sensor', 'sum'),
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
        groups = list(df[feature].unique())
        for c in groups:
            _f = df[df[feature]==c] 
            data.append(
                go.Bar(name=c, x=_f[subject_group], y=_f['daily_mins'],  marker=dict(line=dict(width=0.01))),
            )
    else:
        data.append(
            go.Bar( x=df[subject_group], y=df['daily_mins'],  marker=dict(line=dict(width=0.01))),
    )
    return data 

def plotly_bar_layout():
    fig = go.Figure([])
    fig.update_layout(yaxis_tickprefix = '$ ',  barcornerradius=15)
    fig.update_layout(
        font=dict(
            family="verdana, arial, sans-serif",
            size=14,
            color='gray'
        ),
        template="plotly_white" ,     
        autosize = True,
        margin=dict( t=0, b=20),
        xaxis=dict(),
        yaxis=dict(),
        )
    return fig




shadow_box =   dmc.CheckboxGroup(
    id="sub-graphs-chips",
    value = [],
    children=[
        dmc.Box(
                mt = 35,
                style = {    'whiteSpace': 'nowrap'},
                children =  ShadowBox().layout(
                    children = [
                    dmc.Box(
                
                        style = { 'boxShadow': 'rgba(219, 166, 232, 0.1) 0px 3px 12px', "borderRadius":'20px',  "margin":'10px 10px', "padding":'5px 10px 5px 0px', },

                        children = [
                            CheckboxChip(label = f"{i}", value=f"{i}", size= 'lg', className='check-box-group-id',) 
                        ]
                    )
                    
                    for i in _filters
                ]
                )
            )
    ]
)

search_component = dmc.Box(
        id = "outer-search",
        style = {
            'position': 'fixed',
            'left': '50%',
            'top': '0px',
            'transform': 'translateX(-50%)',
            'zIndex':10000
        },
        children = [
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
                children = [    
                    dmc.PopoverTarget(
                        dmc.Box(
                            p=15,
                            w= 650,
                            children = [
                                dmc.TextInput(
                                    leftSection=iconify(icon="iconamoon:search-thin"),
                                    rightSection=dmc.SegmentedControl(
                                            id = 'segmented-product-or-category',
                                            value = "Category",
                                            data = [
                                                {"value": "Category", "label": dmc.Center([iconify(icon='iconamoon:category-thin', width=16), html.Span('Category')],style={"gap": 10})},
                                                {"value": "Product", "label":  dmc.Center([iconify(icon='weui:shop-outlined', width=16), html.Span('Product')],style={"gap": 10})},

                                                ], size='xs', radius='lg'),
                                    id='input-box',  
                                    placeholder='Search by Product or Category',
                                    styles={
                                        "root": { 'boxShadow': 'rgba(100, 100, 111, 0.2) 0px 7px 29px 0px', 'borderRadius':'20px', 'position': 'relative', 'zIndex':10000},
                                        "input": { 'height': '45px', 'borderRadius':'20px', },
                                        "section": {'padding':'10px', 'width':'auto'}
                                    }
                                )
                            ]
                        )
                    ),
                    dmc.PopoverDropdown(
                        id ='search-output', 
                        style = {
                            'marginTop': '-80px', 'paddingTop': '70px',
                            'borderRadius': '20px 20px 10px 10px'
                        },
                        styles={"root": { 'boxShadow': 'rgba(100, 100, 111, 0.2) 0px 7px 29px 0px'}},
                        children= dmc.CheckboxGroup(
                            id="search-checkbox-group",
                            children = [],
                            value =[]
                        )
                    )
                ]
            )
        ]
    )


back = dmc.Paper(
    h = '100%',
    w = '100%',
    shadow = 'xs',
    radius = 'lg',
    pos = 'relative',  
    className = 'bg-switch-darker',
    id='sub-graphs',
    children = []
)

# front=  dmc.Box(
#     h = '100%',
#     w = '100%',
#     id = 'map-container',
#     pos = "relative",
#     children = [
#         dmc.Box(id= 'map', h = '100%'),
#         dmc.Box(
#             id = 'legend',
#             style={"position": "absolute", "bottom": "20px","left": "2%", "zIndex": "20",},
#             children = [   
#             ]
#         ),
#         dmc.SegmentedControl(
#             id="map-select-product",
#             style={"position": "absolute", "bottom": "10px","left": "30%", "zIndex": "30",  'transform': 'translateX(-50%)'},
#             radius='lg',
#             styles={"root":{'backgroundColor':'#efeaea'}},
#             data=[],
#             mb=10,
#         ),
#         dmc.Paper(
#             h = '100%',
#             w = '100%',
#             shadow="lg",
#             children = [
#                 expendable_box(
#                     "state-filter",  
#                     "expandable-box", 
#                     dmc.Text('FILTERS', p =10), 
#                     dmc.CheckboxGroup(  
#                         children =dmc.Paper(
#                             style = {'boxShadow':'rgba(0, 0, 0, 0.1) 0px 0px 5px 0px, rgba(0, 0, 0, 0.1) 0px 0px 1px 0px !important',      
#                                      "position": "absolute", "top": "0px",
#                                     "height":" 100%",
#                                     "width": "100%" 
#                                     },
#                             shadow = 'lg',
#                             p = 10,
#                             children =[
#                                 dmc.Box(
#                                     dmc.Switch(
#                                         id = 'select-all-states',
#                                         size="sm",
#                                         radius="lg",
#                                         label="Select ALL",
#                                         mb = 10,
#                                         p = 8,
#                                         checked = True,
#                                         styles={"label": {"color": 'gray'}},
#                                     ),      
#                                     style = {"position": "absolute",  "top": "0px","width": "100%"},
#                                     p = 8,
#                                 ),
#                                 dmc.Box(
#                                     id = 'states-check-data',
#                                     mt = 50,
#                                      style={
#                                         "height": "100%",
#                                         "overflow": "scroll"
#                                     }
#                                 )
#                             ]
#                         )
#                     ) 
#                 )
#             ]
#         )    
#     ]
# )

# flip_card = FlipCard(
#     front=front,
#     back=back,
#     button=dmc.Button(
#         id='flip-button',  
#         variant="outline", 
#         n_clicks=0,  
#         size = 'sm', 
#         color= 'grape', 
#         style={"position": "absolute", "top": "0px", "right": "70px"}
#     )
# )

content =   dmc.Box(
    id = 'content',
    children= [
        dmc.Box(
            id = 'main-content-top-section',
            children=[
                dmc.ActionIcon(
                    id = 'color-scheme-toggle',
                    n_clicks=0, 
                    variant= "transparent",
                    style = {'position':'absolute','right':'0px','top':'1px' },
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
        # dmc.Box(
        #     id = 'main-content-graph-section',
        #     p ='10px',
        #     style = {'position': 'relative','width': '100%','height': '100%' },
        #     children=[
        #         dcc.Store('map-data'),
        #         flip_card.layout()           
        #     ]
        # )   
    ]
)


app.layout =  dmc.MantineProvider(
    id="mantine-provider",
    children = [
        dmc.Box(
            children = [
                sidebar(subs_df, _filters),
                content,
                dcc.Store(id = 'sto', data = {'initila':'my data'}),
            ]
        )
    ]
)


@callback(
    Output("search-checkbox-group", "children"), 
    Input('input-box', 'value'),
    Input('segmented-product-or-category', 'value'),
    Input("search-checkbox-group", "value"), 
    prevent_intial_call = True
)
def update_output(value, segmented, selected_prodcuts):

    if ctx.triggered_id =='segmented-product-or-category':
        set_props("map-select-product", {'value': []})
        set_props("map-select-product", {'data': []})
        selected_prodcuts = []
    if ctx.triggered_id =='search-checkbox-group':
        if selected_prodcuts:
            set_props("map-select-product", {'value': selected_prodcuts[-1]})
        set_props("map-select-product", {'data': selected_prodcuts})
        
    if segmented =='Subject':
        items = subjects
    else:
        items = subject_groups

    def found_items(items):
        return  dmc.ScrollArea(
                    h=350, 
                    w='100%',
                    mt=10,
                    children =  dmc.Stack(
                        children = [
                            dmc.Checkbox(
                                label=str(i).replace("_"," ").title(), 
                                value=i, 
                                size = 'sm',
                                styles={"label": {"paddingInlineStart": 8, 'color':'gray'}}
                            ) 
                            for i in items
                        ]
                    ) 
                )

    if value:  
        return found_items(
            sorted(set(sorted([i for i in items if value.lower() in i.lower() ])[:30] + selected_prodcuts))
        ) 
 
    return found_items(
        sorted(set(items[:30] + selected_prodcuts))
    ) 

def make_bar_chart(mindlamp_df, subjects,  feature, subject_group):
   
    df = filter_df(mindlamp_df, subjects,  feature, subject_group)
    df[subject_group] = df[subject_group].apply(_underscores)
    data = make_data_traces(df, feature, subject_group)

    fig = go.Figure(
        data=data, 
        layout= fig_layout
    )
    fig.update_layout(legend=dict(orientation="h"))
    g = dcc.Graph(  
        figure= fig, 
        config={'displayModeBar': False}, 
        style={'width': '100%',  'height': '100%' },  className = "outer-graph",
    )
    return dmc.Box(
        style={'width': '100%',  'height': '50%', "position":"relative" },
        p='2%',
        id={"type": "maximize-graph", "index":'my_index' if not feature else feature},
        children = [
            dcc.Store(id = {"type": "remember-graph-setting", "index": 'my_index' if not feature else feature}),
            dmc.ActionIcon(
                iconify ('system-uicons:fullscreen', width = 15),
                size="lg",
                style = { "position":"absolute",  "right":"0px",  "top":"0px" },
                variant="subtle",
                id={"type": "action-maximize-graph", "index": 'my_index' if not feature else feature},
                n_clicks=0,
            ),
            dmc.Paper(
                p = 5,
                style={'width': '100%',  'height': '100%',   'borderRadius': '15px'  },
                shadow='sm',
                children =[
                   g
                ]
            )
        ]
    )

@callback(
    Output("sub-graphs", "children"),
    Input({"type": "checkbox-options", "index": ALL}, "value"),
    Input("search-checkbox-group", "value"),
    Input('sub-graphs-chips', 'value'),
    Input('segmented-product-or-category', 'value'),
    
    prevent_intial_call = True
)
def display_output(_filters,   subjects, features, subject_group): 
    
    if not subjects:
        return []
    
    converted_dict = {item['id']['index']: item.get('value') for item in ctx.inputs_list[0] if item.get('value')}
    filters = make_filter(converted_dict)

    if filters:
        df = mindlamp_df.query(filters)
    else:
        df = mindlamp_df

    # def make_map_series (df, subjects, subject_group):

    #     df = df.groupby(["shipping_state", "Q_demos_state", subject_group]).agg(
    #                 lat=('lat', 'first'),
    #                 lon=('lon', 'first'),
    #                 unique_orders=(f"{subject_group}", 'count'),
    #                 daily_mins=('Purchase daily_mins Per Unit', 'sum'),
    #         ).reset_index()
    #     df['id'] = df['shipping_state']
      
    #     points = df[[ "id", "lat", "lon", "Q_demos_state"]].drop_duplicates(subset = ['id']).to_dict('records')
    #     points = json.dumps(points)
    #     df = df[[ "id", "Q_demos_state", subject_group, "daily_mins",  'unique_orders']]
    #     arrows = df[df[subject_group].isin(subjects)].values.tolist()
    #     return points, arrows
    
    # points, arrow = make_map_series (df, subjects, subject_group)

    # set_props("map-data", {'data': {'points':points, 'arrow':arrow}})
    
    _chidren = Patch()

    if ctx.triggered_id == 'search-checkbox-group':
        if not features:

            g = make_bar_chart(df, subjects,  '', subject_group)
            _chidren.clear()
            _chidren.append(g)
        else:
            _chidren.clear()
            for feature in features:
                g = make_bar_chart(df, subjects,  feature, subject_group)
                _chidren.append(g)
    else:
        if not features:
            g = make_bar_chart(df, subjects,  '', subject_group)
            _chidren.clear()
            _chidren.append(g)
        else:
            _chidren.clear()
            for feature in features:
                g = make_bar_chart(df, subjects,  feature, subject_group)
                _chidren.append(g)

    return _chidren

ShadowBox().callback()
# flip_card.app_callbacks()

drawer_sidebar_togle()
theme_switcher_callback()

# Set up logging
logging.basicConfig(
    filename='app.log',        # File to write logs to, saved in working directory
    filemode='a',              # 'a' for append, 'w' to overwrite each time
    level=logging.INFO,        # Minimum logging level
    format='%(asctime)s - %(pathname)s - %(message)s'
)

if __name__ == "__main__":
    app.run(debug=True, port=8090)

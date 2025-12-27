import dash
from dash import html
from dash import dcc
import dash_table
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import mplcursors
from matplotlib.font_manager import FontProperties
from collections import defaultdict
from prettytable import PrettyTable

from Home.Running.Shoe.shoe import cal_table_result, field_names

result = cal_table_result()

# dash
app = dash.Dash(__name__)
# df = pd.DataFrame(result, columns=field_names)
df = pd.DataFrame(result)
# 创建布局

df.columns = field_names

# Define a function to format the "Done" column
def format_done_column(value):
    if value:
        return "√"
    else:
        return ""

df["Done"] = df["Done"].apply(format_done_column)

app.layout = html.Div([
    dash_table.DataTable(
        id='table',
        columns=[{'name': col, 'id': col} for col in df.columns],
        # columns=columns,
        data=df.to_dict('records'),
        # style_table={'height': '1500px', "width": "1200px", 'overflowY': 'auto'},
        style_table={"width": "1200px", 'overflowY': 'auto'},
        style_cell={
            'font_family': 'Arial, sans-serif',
            'font_size': '16px',
            'minWidth': 0, 'maxWidth': 150, 'whiteSpace': 'normal',  # 自适应宽度
            'textAlign': 'center', 'verticalAlign': 'middle',
        },
        # Conditionally format the "Done" column
        style_data_conditional=[
            {
                'if': {'column_id': 'Done'},
                'textAlign': 'center',
                'width': '50px',  # Adjust the width as needed
            },
        ],
    )
])

if __name__ == '__main__':
    app.run_server(debug=False)

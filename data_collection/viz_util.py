import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

class InteractiveLineChart:
    def __init__(self, title, data_path, numeric_cols, categorical_cols, x_axis_cols, port=8050): 
        self.title = title
        self.df = pd.read_csv(data_path)

        self.app = dash.Dash(__name__)
        
        self.x_axis_cols = x_axis_cols
        self.numeric_columns = numeric_cols
        self.categorical_columns = categorical_cols
        self.port = port

        self.build_layout()
        self.add_callbacks()

    def build_layout(self):
        self.app.layout = html.Div([
            html.H1(self.title),
            
            html.Div([
                html.H3("Plotting Options"),
                html.Div([
                    html.Div([
                        html.Label("X-Axis"),
                        dcc.Dropdown(id="x-axis", options=[{"label": col, "value": col} for col in self.x_axis_cols], value='ws_ratio'),
                    ], style={"width": "23%", "display": "inline-block", "padding": "10px"}),

                    html.Div([
                        html.Label("Y-Axis"),
                        dcc.Dropdown(id="y-axis", options=[{"label": col, "value": col} for col in self.numeric_columns], value="_missRatio", multi=True),
                    ], style={"width": "23%", "display": "inline-block", "padding": "10px"}),

                    html.Div([
                        html.Label("Line Color"),
                        dcc.Dropdown(id="line-color", options=[{"label": col, "value": col} for col in self.categorical_columns], value=None),
                    ], style={"width": "23%", "display": "inline-block", "padding": "10px"}),

                    html.Div([
                        html.Label("Line Shape"),
                        dcc.Dropdown(id="line-shape", options=[{"label": col, "value": col} for col in self.categorical_columns], value=None),
                    ], style={"width": "23%", "display": "inline-block", "padding": "10px"}),

                    html.Div([
                        html.Label("Point Shape"),
                        dcc.Dropdown(id="point-shape", options=[{"label": col, "value": col} for col in self.categorical_columns], value=None),
                    ], style={"width": "23%", "display": "inline-block", "padding": "10px"}),
                ], style={"overflow": "visible"})
            ], style={"width": "100%", "display": "inline-block", "overflow": "visible"}),

            # Section for data selection
            html.Div([
                html.H3("Data Selection"),
                html.Div([
                    *[html.Div([
                        html.Label(col),
                        dcc.Dropdown(
                            id=f"filter-{col}", 
                            options=[{"label": str(v), "value": str(v)} if self.df[col].dtype == 'bool' else {"label": v, "value": v} for v in sorted(self.df[col].unique())], 
                            multi=True
                        )
                    ], style={"width": "23%", "display": "inline-block", "padding": "10px"}) for col in self.categorical_columns]
                ], style={"overflow": "visible"})
            ], style={"width": "100%", "display": "inline-block", "overflow": "visible"}),

            # Graph output
            html.Div(id="graphs", style={"overflow": "visible", "textAlign": "center"})
        ], style={"overflow": "visible"})

    def add_callbacks(self):
        @self.app.callback(
            Output("graphs", "children"),
            [Input("x-axis", "value"),
             Input("y-axis", "value"),
             Input("line-color", "value"),
             Input("line-shape", "value"),
             Input("point-shape", "value")] +
            [Input(f"filter-{col}", "value") for col in self.categorical_columns]
        )
        def update_chart(x_col, y_cols, line_color, line_shape, point_shape, *filters):
            filtered_df = self.df.copy()
            filtered_df = filtered_df.sort_values(by=x_col)

            filters = list(filters) 

            for i, col in enumerate(self.categorical_columns):
                if filters[i]:
                    # Convert string boolean values back to actual booleans
                    if self.df[col].dtype == 'bool':
                        filters[i] = [v == 'True' for v in filters[i]]
                    filtered_df = filtered_df[filtered_df[col].isin(filters[i])]


            if isinstance(y_cols, str):
                y_cols = [y_cols]

            graphs = []
            for y_col in y_cols:
                fig = px.line(filtered_df, x=x_col, y=y_col, color=line_color, 
                              line_dash=line_shape, symbol=point_shape, markers=True, category_orders=
                              {
                                col: sorted(df[col].unique())  for col in self.categorical_columns
                              }
                             )
                fig.update_layout(title=f"{x_col} - {y_col}", xaxis={
                    "type": "category",
                    "categoryorder": "array",
                    "categoryarray": sorted(self.df[x_col].unique())
                })
                graphs.append(dcc.Graph(figure=fig, style={"width": "65%", "height": "510px", "display": "inline-block"}))

            return graphs

    def run(self):
        self.app.run_server(debug=True, port=self.port)
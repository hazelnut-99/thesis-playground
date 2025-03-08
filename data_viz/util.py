import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import plotly.data as px_data  

class InteractiveLineChart:
    def __init__(self):
        # Using a public dataset: gapminder
        self.df = px_data.gapminder()

        self.app = dash.Dash(__name__)

        self.numeric_columns = self.df.select_dtypes(include=['number']).columns
        self.categorical_columns = self.df.select_dtypes(exclude=['number']).columns

        self.build_layout()
        self.add_callbacks()

    def build_layout(self):
        self.app.layout = html.Div([
            html.H1("Interactive Line Chart - Gapminder Dataset"),
            
            # Section for plotting options
            html.Div([
                html.H3("Plotting Options"),
                html.Div([
                    html.Div([
                        html.Label("X-Axis"),
                        dcc.Dropdown(id="x-axis", options=[{"label": col, "value": col} for col in self.numeric_columns], value="year"),
                    ], style={"width": "30%", "display": "inline-block", "padding": "10px"}),

                    html.Div([
                        html.Label("Y-Axis"),
                        dcc.Dropdown(id="y-axis", options=[{"label": col, "value": col} for col in self.numeric_columns], value="gdpPercap", multi=True),
                    ], style={"width": "30%", "display": "inline-block", "padding": "10px"}),

                    html.Div([
                        html.Label("Line Color"),
                        dcc.Dropdown(id="line-color", options=[{"label": col, "value": col} for col in self.categorical_columns], value="continent"),
                    ], style={"width": "30%", "display": "inline-block", "padding": "10px"}),

                    html.Div([
                        html.Label("Line Shape"),
                        dcc.Dropdown(id="line-shape", options=[{"label": col, "value": col} for col in self.categorical_columns], value=None),
                    ], style={"width": "30%", "display": "inline-block", "padding": "10px"}),

                    html.Div([
                        html.Label("Point Shape"),
                        dcc.Dropdown(id="point-shape", options=[{"label": col, "value": col} for col in self.categorical_columns], value=None),
                    ], style={"width": "30%", "display": "inline-block", "padding": "10px"}),
                ], style={"overflow": "visible"})
            ], style={"width": "100%", "display": "inline-block", "overflow": "visible"}),

            # Section for data selection
            html.Div([
                html.H3("Data Selection"),
                html.Div([
                    *[html.Div([
                        html.Label(col),
                        dcc.Dropdown(id=f"filter-{col}", options=[{"label": v, "value": v} for v in self.df[col].unique()], multi=True)
                    ], style={"width": "30%", "display": "inline-block", "padding": "10px"}) for col in self.categorical_columns]
                ], style={"overflow": "visible"})
            ], style={"width": "100%", "display": "inline-block", "overflow": "visible"}),

            # Graph output
            html.Div(id="graphs", style={"overflow": "visible"})
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

            for i, col in enumerate(self.categorical_columns):
                if filters[i]:
                    filtered_df = filtered_df[filtered_df[col].isin(filters[i])]

            if isinstance(y_cols, str):
                y_cols = [y_cols]

            graphs = []
            for y_col in y_cols:
                fig = px.line(filtered_df, x=x_col, y=y_col, color=line_color, line_dash=line_shape, symbol=point_shape, markers=True)
                fig.update_layout(title=f"{x_col} - {y_col}")
                graphs.append(dcc.Graph(figure=fig))

            return graphs

    def run(self):
        self.app.run_server(debug=True)


# chart = InteractiveLineChart()
# chart.run()
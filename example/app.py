import htmltools
import pandas as pd
import plotly.express as px
from shinywidgets import output_widget, render_widget

from shiny import App, reactive, render, req, ui


class COL_NAMES:
    year = "Year"
    country = "Country"
    pop = "Population"
    lifeExp = "Life Expectancy"
    gdpPercap = "GDP per capita"


# Load the Gapminder dataset
df = px.data.gapminder().rename(columns=COL_NAMES.__dict__)

# Prepare a summary DataFrame
summary_df = (
    df.groupby(COL_NAMES.country)
    .agg(
        {
            COL_NAMES.pop: ["max"],
            COL_NAMES.lifeExp: ["max"],
            COL_NAMES.gdpPercap: ["max"],
        }
    )
    .reset_index()
    .rename(columns={})
)


summary_df.columns = [col[0] for col in summary_df.columns.values]

app_ui = ui.page_fillable(
    {"class": "p-3"},
    # "Gapminder Data",
    ui.layout_columns(
        ui.card(
            ui.h3("Maximum ", ui.code("gapminder"), " values per country"),
            ui.output_data_frame("summary_data"),
            height="800px",
            full_screen=True,
        ),
        ui.TagList(
            ui.card(
                ui.output_ui("country_detail_pop_ui"),
                height="400px",
            ),
            ui.card(output_widget("country_detail_percap"), height="400px"),
        ),
        col_widths=[7, 5],
    ),
)


def server(input, output, session):

    @render.ui
    def country_detail_pop_ui():
        if summary_data.data_view(selected=True).empty:
            return ui.span(
                "Please select a country's row in the table",
                style=htmltools.css(**{"color": "lightgrey"}),
            )
        return output_widget("country_detail_pop")

    def styles_fn(dt: pd.DataFrame):
        dt_top_5 = {
            COL_NAMES.pop: list(dt[COL_NAMES.pop].nlargest(5)),
            COL_NAMES.gdpPercap: list(dt[COL_NAMES.gdpPercap].nlargest(5)),
            COL_NAMES.lifeExp: list(dt[COL_NAMES.lifeExp].nlargest(5)),
        }
        top_1 = {
            COL_NAMES.pop: dt_top_5[COL_NAMES.pop][0],
            COL_NAMES.gdpPercap: dt_top_5[COL_NAMES.gdpPercap][0],
            COL_NAMES.lifeExp: dt_top_5[COL_NAMES.lifeExp][0],
        }
        top_5 = {
            COL_NAMES.pop: dt_top_5[COL_NAMES.pop][4],
            COL_NAMES.gdpPercap: dt_top_5[COL_NAMES.gdpPercap][4],
            COL_NAMES.lifeExp: dt_top_5[COL_NAMES.lifeExp][4],
        }
        return [
            {
                "cols": [COL_NAMES.pop],
                "rows": list(
                    dt.loc[:, COL_NAMES.pop].apply(lambda x: x >= top_5[COL_NAMES.pop])
                ),
                "style": {"background-color": "#f8d7da99"},  # red
            },
            {
                "cols": [COL_NAMES.gdpPercap],
                "rows": list(
                    dt.loc[:, COL_NAMES.gdpPercap].apply(
                        lambda x: x >= top_5[COL_NAMES.gdpPercap]
                    )
                ),
                "style": {"background-color": "#d4edda77"},  # green
            },
            {
                "cols": [COL_NAMES.lifeExp],
                "rows": list(
                    dt.loc[:, COL_NAMES.lifeExp].apply(
                        lambda x: x >= top_5[COL_NAMES.lifeExp]
                    )
                ),
                "style": {"background-color": "#cce5ff99"},  # blue
            },
            {
                "cols": [COL_NAMES.pop],
                "rows": list(
                    dt.loc[:, COL_NAMES.pop].apply(lambda x: x == top_1[COL_NAMES.pop])
                ),
                "style": {"border": "solid 2px #ed969e"},  # red
            },
            {
                "cols": [COL_NAMES.gdpPercap],
                "rows": list(
                    dt.loc[:, COL_NAMES.gdpPercap].apply(
                        lambda x: x == top_1[COL_NAMES.gdpPercap]
                    )
                ),
                "style": {"border": "solid 2px #9ed6ac"},  # green
            },
            {
                "cols": [COL_NAMES.lifeExp],
                "rows": list(
                    dt.loc[:, COL_NAMES.lifeExp].apply(
                        lambda x: x == top_1[COL_NAMES.lifeExp]
                    )
                ),
                "style": {"border": "solid 2px #80beff"},  # blue
            },
        ]

    @render.data_frame
    def summary_data():
        return render.DataGrid(
            summary_df.round(2),
            selection_mode="rows",
            styles=styles_fn,
            editable=True,
            filters=True,
        )

    @summary_data.set_patch_fn
    def _(*, patch: render.CellPatch):
        if patch["column_index"] == 0:
            return patch["value"]
        if patch["column_index"] == 1:
            return int(patch["value"])
        return float(patch["value"])

    @reactive.calc
    def filtered_df():
        req(not summary_data.data_view(selected=True).empty)
        sum_selected_rows = summary_data.cell_selection()["rows"]
        countries = summary_data.data().iloc[list(sum_selected_rows), :][
            COL_NAMES.country
        ]
        # Filter data for selected countries
        return df[df[COL_NAMES.country].isin(countries)]

    @render_widget
    def country_detail_pop():
        return px.line(
            filtered_df(),
            x=COL_NAMES.year,
            y=COL_NAMES.pop,
            color=COL_NAMES.country,
            title="Population Over Time",
        )

    @render_widget
    def country_detail_percap():
        return px.line(
            filtered_df(),
            x=COL_NAMES.year,
            y=COL_NAMES.gdpPercap,
            color=COL_NAMES.country,
            title="GDP per Capita Over Time",
        )


app = App(app_ui, server)

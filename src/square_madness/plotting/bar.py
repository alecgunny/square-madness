import math

import pandas as pd
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    FixedTicker,
    HoverTool,
    InlineStyleSheet,
    LinearColorMapper,
    Span,
    TabPanel,
    Tabs,
)
from bokeh.palettes import Viridis256
from bokeh.plotting import figure

from square_madness.plotting.utils import PLOT_SIZE

BAR_WIDTH = 350
BUY_IN_PER_SQUARE = 40


def _gambler_stats(grid: pd.DataFrame) -> pd.DataFrame:
    df = (
        grid[grid["gambler"] != ""]
        .groupby("gambler")
        .agg(
            revenue=("payout", "sum"),
            num_squares=("gambler", "count"),
            actual_prob=("prob", "sum"),
        )
        .reset_index()
    )
    df["profit"] = df["revenue"] - df["num_squares"] * BUY_IN_PER_SQUARE
    df["expected_prob"] = df["num_squares"] / 100
    df["edge"] = df["actual_prob"] - df["expected_prob"]
    return df


def plot_profits(grid: pd.DataFrame, bg_color: str) -> figure:
    stats = _gambler_stats(grid).sort_values("profit", ascending=True)
    gambler_names = stats["gambler"].tolist()

    source = ColumnDataSource(
        dict(
            gambler=gambler_names,
            revenue=stats["revenue"].tolist(),
            profit=stats["profit"].tolist(),
        )
    )

    p = figure(
        title="Profits",
        y_range=gambler_names,
        width=BAR_WIDTH,
        height=PLOT_SIZE,
        toolbar_location=None,
        x_axis_label="Amount ($)",
    )

    r_profit = p.hbar(
        y="gambler",
        right="profit",
        height=0.6,
        source=source,
        color="#2196F3",
        fill_alpha=0.6,
        line_alpha=0.9,
        legend_label="Profit",
    )
    r_revenue = p.hbar(
        y="gambler",
        right="revenue",
        height=0.6,
        source=source,
        color="#4CAF50",
        fill_alpha=0.6,
        line_alpha=0.9,
        legend_label="Revenue",
    )

    p.add_tools(
        HoverTool(
            renderers=[r_revenue],
            tooltips=[("Gambler", "@gambler"), ("Revenue", "$@revenue")],
        )
    )
    p.add_tools(
        HoverTool(
            renderers=[r_profit],
            tooltips=[("Gambler", "@gambler"), ("Profit", "$@profit")],
        )
    )

    zero_line = Span(location=0, dimension="height", line_color="#777777", line_width=1)
    p.add_layout(zero_line)

    p.background_fill_color = bg_color
    p.yaxis.major_label_orientation = math.pi / 4
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.legend.location = "top_left"
    p.legend.background_fill_alpha = 0.7

    return p


def plot_edge(grid: pd.DataFrame, bg_color: str) -> figure:
    stats = _gambler_stats(grid).sort_values("edge", ascending=True)
    gambler_names = stats["gambler"].tolist()
    n_squares = stats["num_squares"].tolist()
    unique_counts = sorted(set(n_squares))
    n = len(unique_counts)
    palette = (
        [Viridis256[128]] if n == 1 else [Viridis256[int(i * 255 / (n - 1))] for i in range(n)]
    )

    mapper = LinearColorMapper(
        palette=palette,
        low=min(unique_counts) - 0.5,
        high=max(unique_counts) + 0.5,
    )

    source = ColumnDataSource(
        dict(
            gambler=gambler_names,
            edge=(stats["edge"] * 100).tolist(),
            num_squares=n_squares,
        )
    )

    p = figure(
        title="Edge",
        y_range=gambler_names,
        width=BAR_WIDTH,
        height=PLOT_SIZE,
        toolbar_location=None,
        x_axis_label="Edge (actual − expected probability, %)",
    )

    bars = p.hbar(
        y="gambler",
        right="edge",
        height=0.6,
        source=source,
        fill_color={"field": "num_squares", "transform": mapper},
        line_color={"field": "num_squares", "transform": mapper},
        fill_alpha=0.6,
        line_alpha=0.9,
    )

    p.add_tools(
        HoverTool(
            renderers=[bars],
            tooltips=[
                ("Gambler", "@gambler"),
                ("Edge", "@edge{0.00}%"),
                ("Squares Owned", "@num_squares"),
            ],
        )
    )

    zero_line = Span(location=0, dimension="height", line_color="#777777", line_width=1)
    p.add_layout(zero_line)

    color_bar = ColorBar(
        color_mapper=mapper,
        location=(0, 0),
        title="Squares",
        ticker=FixedTicker(ticks=unique_counts),
    )
    p.add_layout(color_bar, "right")

    p.background_fill_color = bg_color
    p.yaxis.major_label_orientation = math.pi / 4
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None

    return p


def generate_bar(grid: pd.DataFrame, tabs_stylesheet: InlineStyleSheet, bg_color: str) -> Tabs:
    return Tabs(
        tabs=[
            TabPanel(child=plot_profits(grid, bg_color), title="Profits"),
            TabPanel(child=plot_edge(grid, bg_color), title="Edge"),
        ],
        stylesheets=[tabs_stylesheet],
    )

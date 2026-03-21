import pandas as pd
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    FixedTicker,
    HoverTool,
    LinearColorMapper,
    NumeralTickFormatter,
)
from bokeh.palettes import Oranges, RdYlGn, Viridis256
from bokeh.plotting import figure

from square_madness.plotting.utils import DIGITS, DISCRETE_THRESHOLD, PLOT_SIZE


def _build_heatmap(
    title: str,
    grid_df: pd.DataFrame,
    value_col: str,
    palette: list,
    low: float,
    high: float,
    unique_vals: list | None = None,
    tooltips: list | str | None = None,
    extra_cols: dict | None = None,
    formatter=None,
) -> figure:
    data = dict(
        x=[str(int(wd)) for wd in grid_df["winning_digit"]],
        y=[str(int(ld)) for ld in grid_df["losing_digit"]],
        values=grid_df[value_col].tolist(),
        gamblers=grid_df["gambler"].tolist(),
    )
    if extra_cols:
        data.update(extra_cols)
    source = ColumnDataSource(data)

    mapper = LinearColorMapper(palette=palette, low=low, high=high)

    p = figure(
        title=title,
        x_range=DIGITS,
        y_range=list(reversed(DIGITS)),
        width=PLOT_SIZE + 120,
        height=PLOT_SIZE,
        toolbar_location=None,
        x_axis_label="Winning Digit",
        y_axis_label="Losing Digit",
    )

    rect = p.rect(
        x="x",
        y="y",
        width=0.95,
        height=0.95,
        source=source,
        fill_color={"field": "values", "transform": mapper},
        fill_alpha=0.6,
        line_color={"field": "values", "transform": mapper},
        line_alpha=0.9,
        line_width=2.5,
    )

    p.grid.grid_line_color = None

    if tooltips is not None:
        p.add_tools(HoverTool(renderers=[rect], tooltips=tooltips))

    p.text(
        x="x",
        y="y",
        text="gamblers",
        source=source,
        text_align="center",
        text_baseline="middle",
        text_font_size="9pt",
        angle=0.785,  # 45 degrees in radians
    )

    color_bar_kwargs = {"color_mapper": mapper, "location": (0, 0)}
    if unique_vals is not None:
        color_bar_kwargs["ticker"] = FixedTicker(ticks=unique_vals)
    if formatter is not None:
        color_bar_kwargs["formatter"] = formatter
    color_bar = ColorBar(**color_bar_kwargs)
    p.add_layout(color_bar, "right")

    return p


def plot_frequency(grid: pd.DataFrame) -> figure:
    return _build_heatmap(
        "Historical Frequency",
        grid,
        "prob",
        Viridis256,
        grid["prob"].min(),
        grid["prob"].max(),
        tooltips=[
            ("Gambler", "@gamblers"),
            ("Winning Digit", "@x"),
            ("Losing Digit", "@y"),
            ("Historical Probability", "@values{0.00%}"),
        ],
        formatter=NumeralTickFormatter(format="0.00%"),
    )


def plot_hits(grid: pd.DataFrame) -> figure:
    hit_vals = sorted(grid["hits"].unique().tolist())
    n_hits = min(max(len(hit_vals), 3), 9)
    hits_palette = list(reversed(Oranges[n_hits]))
    return _build_heatmap(
        "Hits",
        grid,
        "hits",
        hits_palette,
        grid["hits"].min() - 0.5,
        grid["hits"].max() + 0.5,
        unique_vals=hit_vals,
        tooltips="""
            <div style="padding:6px;background-color:#313338;color:#cccccc;font-size:12px">
                <b>@gamblers</b><br>
                Winning: @x &nbsp;|&nbsp; Losing: @y<br>
                Hits: @values<br>
                <hr style="border-color:#555;margin:4px 0">
                @games_html{safe}
            </div>
        """,
        extra_cols={"games_html": grid["games_html"].tolist()},
    )


def plot_payouts(grid: pd.DataFrame) -> figure:
    payout_vals = sorted(grid["payout"].unique().tolist())
    n_unique = len(payout_vals)
    if n_unique < DISCRETE_THRESHOLD:
        n_colors = min(max(n_unique, 3), 11)
        return _build_heatmap(
            "Payouts",
            grid,
            "payout",
            RdYlGn[n_colors],
            grid["payout"].min() - 0.5,
            grid["payout"].max() + 0.5,
            unique_vals=payout_vals,
            tooltips=[
                ("Gambler", "@gamblers"),
                ("Winning Digit", "@x"),
                ("Losing Digit", "@y"),
                ("Total Payout", "$@values"),
            ],
        )
    return _build_heatmap(
        "Payouts",
        grid,
        "payout",
        Viridis256,
        grid["payout"].min(),
        grid["payout"].max(),
        tooltips=[
            ("Gambler", "@gamblers"),
            ("Winning Digit", "@x"),
            ("Losing Digit", "@y"),
            ("Total Payout", "$@values"),
        ],
    )

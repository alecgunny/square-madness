import logging
from pathlib import Path

import pandas as pd
from bokeh.embed import file_html
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    FixedTicker,
    HoverTool,
    LinearColorMapper,
    NumeralTickFormatter,
    TabPanel,
    Tabs,
)
from bokeh.palettes import Oranges, RdYlGn, Viridis256
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.themes import Theme
from jsonargparse import ArgumentParser

from square_madness.log import configure
from square_madness.scraper import update_scores

logger = logging.getLogger(__name__)

ROUND_PAYOUTS = {0: 20, 1: 40, 2: 80, 3: 160, 4: 320, 5: 800}
ROUND_NAMES = {
    0: "1st Round",
    1: "2nd Round",
    2: "Sweet 16",
    3: "Elite 8",
    4: "Final Four",
    5: "National Championship",
}

DIGITS = [str(i) for i in range(10)]
DISCRETE_THRESHOLD = 7
PLOT_SIZE = 800
BG_COLOR = "#313338"

THEME = Theme(
    json={
        "attrs": {
            "Plot": {
                "background_fill_color": BG_COLOR,
                "border_fill_color": BG_COLOR,
                "outline_line_color": "#555555",
            },
            "Axis": {
                "axis_line_color": "#777777",
                "axis_label_text_color": "#cccccc",
                "major_label_text_color": "#cccccc",
                "major_tick_line_color": "#777777",
                "minor_tick_line_color": "#555555",
            },
            "Title": {"text_color": "#eeeeee"},
            "ColorBar": {
                "background_fill_color": BG_COLOR,
                "major_label_text_color": "#cccccc",
                "bar_line_color": "#555555",
            },
        }
    }
)


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


def initialize_grid(
    squares_df: pd.DataFrame,
    frequencies_df: pd.DataFrame,
) -> pd.DataFrame:
    full_grid = pd.DataFrame(
        [(wd, ld) for wd in range(10) for ld in range(10)],
        columns=["winning_digit", "losing_digit"],
    )
    grid = full_grid.merge(squares_df, on=["winning_digit", "losing_digit"], how="left")
    grid["gambler"] = grid["gambler"].fillna("")
    grid = grid.merge(frequencies_df, on=["winning_digit", "losing_digit"], how="left")
    grid["frequency"] = grid["frequency"].fillna(0)
    total = grid["frequency"].sum()
    grid["prob"] = grid["frequency"] / total if total > 0 else 0.0
    return grid


def add_game_results(grid: pd.DataFrame, results_df: pd.DataFrame) -> pd.DataFrame:
    if results_df.empty:
        grid["hits"] = 0
        grid["payout"] = 0
        grid["games_html"] = ""
        return grid

    hits = results_df.groupby(["winning_digit", "losing_digit"]).size().reset_index(name="hits")
    grid = grid.merge(hits, on=["winning_digit", "losing_digit"], how="left")

    payouts = results_df.copy()
    payouts["payout"] = payouts["round"].map(ROUND_PAYOUTS)
    payouts_sum = payouts.groupby(["winning_digit", "losing_digit"])["payout"].sum().reset_index()
    grid = grid.merge(payouts_sum, on=["winning_digit", "losing_digit"], how="left")

    games_html_rows = []
    for (wd, ld), group in results_df.groupby(["winning_digit", "losing_digit"]):
        sections = []
        for round_num, round_group in group.groupby("round"):
            round_name = ROUND_NAMES[round_num]
            game_lines = "<br>".join(
                f"{row['winning_team']}: {row['winning_score']}, "
                f"{row['losing_team']}: {row['losing_score']}"
                for _, row in round_group.iterrows()
            )
            sections.append(f'<b style="color:#aaaaaa">{round_name}</b><br>{game_lines}')
        games_html_rows.append(
            {
                "winning_digit": wd,
                "losing_digit": ld,
                "games_html": '<hr style="border-color:#555;margin:4px 0">'.join(sections),
            }
        )
    games_html_df = pd.DataFrame(games_html_rows)
    grid = grid.merge(games_html_df, on=["winning_digit", "losing_digit"], how="left")

    grid["hits"] = grid["hits"].fillna(0).astype(int)
    grid["payout"] = grid["payout"].fillna(0).astype(int)
    grid["games_html"] = grid["games_html"].fillna("")
    return grid


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


def generate_grid(
    results_df: pd.DataFrame,
    frequencies_df: pd.DataFrame,
    squares_df: pd.DataFrame,
) -> Tabs:
    grid = initialize_grid(squares_df, frequencies_df)
    grid = add_game_results(grid, results_df)

    return Tabs(
        tabs=[
            TabPanel(child=plot_frequency(grid), title="Historical Frequency"),
            TabPanel(child=plot_hits(grid), title="Hits"),
            TabPanel(child=plot_payouts(grid), title="Payouts"),
        ]
    )


def main(
    frequencies_file: str = "score_frequencies.csv",
    squares_file: str = "squares.csv",
    output_file: str = "grid.html",
) -> None:
    frequencies_df = pd.read_csv(frequencies_file)
    squares_df = pd.read_csv(squares_file)
    results_df = update_scores()
    layout = generate_grid(results_df, frequencies_df, squares_df)
    html = file_html(layout, CDN, title="Square Madness", theme=THEME)
    html = html.replace(
        "</head>",
        f"<style>body {{ background-color: {BG_COLOR}; margin: 0; }}</style>\n</head>",
        1,
    )
    Path(output_file).write_text(html)
    logger.info("Saved grid to %s", output_file)


def cli() -> None:
    configure()

    parser = ArgumentParser()
    parser.add_function_arguments(main)
    args = parser.parse_args()
    main(**vars(args))


if __name__ == "__main__":
    cli()

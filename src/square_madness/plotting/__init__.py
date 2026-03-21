import logging
from pathlib import Path

import pandas as pd
from bokeh.embed import file_html
from bokeh.models import TabPanel, Tabs
from bokeh.resources import CDN
from jsonargparse import ArgumentParser

from square_madness.plotting.heatmap import plot_frequency, plot_hits, plot_payouts
from square_madness.plotting.utils import BG_COLOR, THEME
from square_madness.scraper import update_scores
from square_madness.utils import ROUND_NAMES, ROUND_PAYOUTS, configure_logging

logger = logging.getLogger(__name__)


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
    configure_logging()

    parser = ArgumentParser()
    parser.add_function_arguments(main)
    args = parser.parse_args()
    main(**vars(args))


if __name__ == "__main__":
    cli()

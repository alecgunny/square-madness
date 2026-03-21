from typing import NamedTuple

from bokeh.models import InlineStyleSheet
from bokeh.themes import Theme

DIGITS = [str(i) for i in range(10)]
DISCRETE_THRESHOLD = 7
PLOT_SIZE = 800


class PlotTheme(NamedTuple):
    bg_color: str
    bar_bg_color: str
    theme: Theme
    tabs_stylesheet: InlineStyleSheet


def _tabs_stylesheet(border: str, color: str) -> InlineStyleSheet:
    return InlineStyleSheet(
        css=f"""
.bk-tab {{
    font-size: 14px;
    padding: 8px 16px;
    border: 1px solid {border};
    border-bottom: none;
    color: {color};
}}
"""
    )


def _theme(
    bg: str, border: str, axis: str, label: str, title: str, tick: str, minor_tick: str
) -> Theme:
    return Theme(
        json={
            "attrs": {
                "Plot": {
                    "background_fill_color": bg,
                    "border_fill_color": bg,
                    "outline_line_color": border,
                },
                "Axis": {
                    "axis_line_color": axis,
                    "axis_label_text_color": label,
                    "major_label_text_color": label,
                    "major_tick_line_color": tick,
                    "minor_tick_line_color": minor_tick,
                },
                "Title": {"text_color": title},
                "ColorBar": {
                    "background_fill_color": bg,
                    "major_label_text_color": label,
                    "bar_line_color": border,
                },
            }
        }
    )


THEMES: dict[str, PlotTheme] = {
    "discord": PlotTheme(
        bg_color="#313338",
        bar_bg_color="#3c3f46",
        theme=_theme(
            bg="#313338",
            border="#555555",
            axis="#777777",
            label="#cccccc",
            title="#eeeeee",
            tick="#777777",
            minor_tick="#555555",
        ),
        tabs_stylesheet=_tabs_stylesheet("#555555", "#cccccc"),
    ),
    "midnight": PlotTheme(
        bg_color="#0d1117",
        bar_bg_color="#161b22",
        theme=_theme(
            bg="#0d1117",
            border="#30363d",
            axis="#30363d",
            label="#8b949e",
            title="#c9d1d9",
            tick="#30363d",
            minor_tick="#21262d",
        ),
        tabs_stylesheet=_tabs_stylesheet("#30363d", "#8b949e"),
    ),
    "dracula": PlotTheme(
        bg_color="#282a36",
        bar_bg_color="#313244",
        theme=_theme(
            bg="#282a36",
            border="#44475a",
            axis="#6272a4",
            label="#f8f8f2",
            title="#bd93f9",
            tick="#6272a4",
            minor_tick="#44475a",
        ),
        tabs_stylesheet=_tabs_stylesheet("#44475a", "#f8f8f2"),
    ),
    "nord": PlotTheme(
        bg_color="#2e3440",
        bar_bg_color="#3b4252",
        theme=_theme(
            bg="#2e3440",
            border="#3b4252",
            axis="#4c566a",
            label="#d8dee9",
            title="#e5e9f0",
            tick="#4c566a",
            minor_tick="#3b4252",
        ),
        tabs_stylesheet=_tabs_stylesheet("#4c566a", "#d8dee9"),
    ),
    "monokai": PlotTheme(
        bg_color="#272822",
        bar_bg_color="#32332d",
        theme=_theme(
            bg="#272822",
            border="#49483e",
            axis="#75715e",
            label="#f8f8f2",
            title="#a6e22e",
            tick="#75715e",
            minor_tick="#49483e",
        ),
        tabs_stylesheet=_tabs_stylesheet("#49483e", "#f8f8f2"),
    ),
}

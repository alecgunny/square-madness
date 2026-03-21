from bokeh.themes import Theme

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

from jsonargparse import ArgumentParser

from square_madness.plotting.app import main as generate_grid_main
from square_madness.utils import configure_logging


def main(
    frequencies_file: str = "score_frequencies.csv",
    squares_file: str = "squares.csv",
    output_file: str = "app.html",
    theme_name: str = "nord",
) -> None:
    generate_grid_main(
        frequencies_file=frequencies_file,
        squares_file=squares_file,
        output_file=output_file,
        theme_name=theme_name,
    )


def cli() -> None:
    configure_logging()

    parser = ArgumentParser()
    parser.add_function_arguments(main)
    args = parser.parse_args()
    main(**vars(args))


if __name__ == "__main__":
    cli()

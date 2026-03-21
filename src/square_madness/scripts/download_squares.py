import logging

import gspread
import pandas as pd
from google.auth import default
from jsonargparse import ArgumentParser

from square_madness.utils import configure_logging

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
WINNING_DIGITS_RANGE = "C2:L2"
LOSING_DIGITS_RANGE = "B3:B12"
GRID_RANGE = "C3:L12"


def main(
    sheet_id: str,
    output_file: str = "squares.csv",
) -> None:
    creds, _ = default(scopes=SCOPES)
    client = gspread.authorize(creds)

    logger.info("Opening sheet %s", sheet_id)
    sheet = client.open_by_key(sheet_id).sheet1

    winning_digits = [int(v) for v in sheet.get(WINNING_DIGITS_RANGE)[0]]
    losing_digits = [int(row[0]) for row in sheet.get(LOSING_DIGITS_RANGE)]
    grid = sheet.get(GRID_RANGE)

    records = []
    for i, losing_digit in enumerate(losing_digits):
        for j, winning_digit in enumerate(winning_digits):
            gambler = grid[i][j] if i < len(grid) and j < len(grid[i]) else ""
            records.append(
                {
                    "winning_digit": winning_digit,
                    "losing_digit": losing_digit,
                    "gambler": gambler,
                }
            )

    df = pd.DataFrame(records)
    df.to_csv(output_file, index=False)
    logger.info("Wrote %d rows to %s", len(df), output_file)


def cli() -> None:
    configure_logging()

    parser = ArgumentParser()
    parser.add_function_arguments(main)
    args = parser.parse_args()
    main(**vars(args))


if __name__ == "__main__":
    cli()

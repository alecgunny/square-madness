import logging
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
from jsonargparse import ArgumentParser
from kaggle import KaggleApi

logger = logging.getLogger(__name__)

COMPETITION = "march-machine-learning-mania-2026"
FILENAME = "MNCAATourneyCompactResults.csv"


def main(output_file: str = "score_frequencies.csv") -> None:
    api = KaggleApi()
    api.authenticate()

    with tempfile.TemporaryDirectory() as tmp:
        logger.info("Downloading %s from %s", FILENAME, COMPETITION)
        api.competition_download_file(COMPETITION, FILENAME, path=tmp, quiet=True)

        tmp_path = Path(tmp)
        csv_path = tmp_path / FILENAME
        zip_path = tmp_path / (FILENAME + ".zip")

        if zip_path.exists():
            logger.info("Extracting %s", zip_path.name)
            with zipfile.ZipFile(zip_path) as z:
                z.extract(FILENAME, path=tmp)

        df = pd.read_csv(csv_path)

    df["winning_digit"] = df["WScore"] % 10
    df["losing_digit"] = df["LScore"] % 10

    freq = df.groupby(["winning_digit", "losing_digit"]).size().reset_index(name="frequency")
    freq.to_csv(output_file, index=False)
    logger.info("Wrote %d rows to %s", len(freq), output_file)


def cli() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = ArgumentParser()
    parser.add_function_arguments(main)
    args = parser.parse_args()
    main(**vars(args))


if __name__ == "__main__":
    cli()

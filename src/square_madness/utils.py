import logging

ROUND_PAYOUTS = {0: 20, 1: 40, 2: 80, 3: 160, 4: 320, 5: 800}
ROUND_NAMES = {
    0: "1st Round",
    1: "2nd Round",
    2: "Sweet 16",
    3: "Elite 8",
    4: "Final Four",
    5: "National Championship",
}


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

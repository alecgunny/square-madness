import logging
from datetime import date, timedelta

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball"
    "/mens-college-basketball/scoreboard"
)
ROUND_ORDER = {
    "1st Round": 0,
    "2nd Round": 1,
    "Sweet 16": 2,
    "Elite 8": 3,
    "Final Four": 4,
    "National Championship": 5,
}
TOURNAMENT_START = date(2026, 3, 19)


def _parse_round(headline: str) -> int | None:
    for label, value in ROUND_ORDER.items():
        if label in headline:
            return value
    return None


def _fetch_date(d: date) -> list[dict]:
    response = requests.get(
        SCOREBOARD_URL, params={"limit": 200, "dates": d.strftime("%Y%m%d")}
    )
    response.raise_for_status()

    records = []
    for event in response.json().get("events", []):
        competition = event["competitions"][0]

        if competition.get("type", {}).get("abbreviation") != "TRNMNT":
            continue
        if event["status"]["type"]["name"] != "STATUS_FINAL":
            continue

        notes = competition.get("notes") or []
        if not notes:
            continue
        round_num = _parse_round(notes[0].get("headline", ""))
        if round_num is None:
            continue

        competitors = competition["competitors"]
        winner = next(c for c in competitors if c["winner"])
        loser = next(c for c in competitors if not c["winner"])

        records.append(
            {
                "winning_team": winner["team"]["displayName"],
                "losing_team": loser["team"]["displayName"],
                "winning_score": int(winner["score"]),
                "losing_score": int(loser["score"]),
                "winning_digit": int(winner["score"]) % 10,
                "losing_digit": int(loser["score"]) % 10,
                "round": round_num,
            }
        )
    return records


def update_scores() -> pd.DataFrame:
    today = date.today()
    logger.info(
        "Fetching completed tournament games from %s to %s", TOURNAMENT_START, today
    )

    records = []
    d = TOURNAMENT_START
    while d <= today:
        daily = _fetch_date(d)
        if daily:
            logger.info("%s: %d completed games", d, len(daily))
        records.extend(daily)
        d += timedelta(days=1)

    logger.info("Found %d completed tournament games total", len(records))
    return pd.DataFrame(
        records,
        columns=[
            "winning_team",
            "losing_team",
            "winning_score",
            "losing_score",
            "winning_digit",
            "losing_digit",
            "round",
        ],
    )

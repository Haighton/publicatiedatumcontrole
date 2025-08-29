import logging
import pandas as pd
from typing import List


def compare_dates(df: pd.DataFrame, logger: logging.Logger | None = None) -> pd.DataFrame:
    """
    Compare 'alto_date' with 'mets_date' and compute a distance score.

    Args:
        df (pd.DataFrame): Must contain 'alto_date' and 'mets_date' as yyyy-mm-dd.
        logger (logging.Logger, optional): Logger for reporting.

    Returns:
        pd.DataFrame: With added 'distance_score' column.
    """
    try:
        # Split dates into components
        a_date: List[List[str]] = df["alto_date"].astype(str).str.split("-").tolist()
        m_date: List[List[str]] = df["mets_date"].astype(str).str.split("-").tolist()

        def strip_leading_zeros(dates: List[List[str]]) -> List[List[str]]:
            cleaned = []
            for parts in dates:
                entry = [p.lstrip("0") if isinstance(p, str)
                         else str(p) for p in parts]
                cleaned.append(entry)
            return cleaned

        a_date = strip_leading_zeros(a_date)
        m_date = strip_leading_zeros(m_date)

        dis_score: List[int] = []
        for ad, md in zip(a_date, m_date):
            try:
                year_diff = abs(int(ad[0]) - int(md[0]))
                month_diff = abs(int(ad[1]) - int(md[1]))
                day_diff = abs(int(ad[2]) - int(md[2]))
                dis_score.append(year_diff + month_diff + day_diff)
            except (ValueError, IndexError) as e:
                if logger:
                    logger.warning(f"Invalid date comparison (alto={ad}, mets={md}): {e}")
                dis_score.append(9999)  # sentinel for invalid

        df["distance_score"] = dis_score

    except Exception as e:
        if logger:
            logger.error(f"Error comparing dates: {e}")
        df["distance_score"] = 9999

    return df

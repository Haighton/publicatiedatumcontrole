import logging
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


def vpos_score(df: pd.DataFrame, logger: logging.Logger | None = None) -> pd.DataFrame:
    """
    Convert VPOS into a normalized score between 0–1.
    Publication dates are usually at the top of the page (low VPOS).

    Args:
        df (pd.DataFrame): Must contain 'VPOS'.
        logger (logging.Logger, optional): Logger for reporting.

    Returns:
        pd.DataFrame: DataFrame with new column 'vpos_score'.
    """
    try:
        vmin, vmax = df["VPOS"].min(), df["VPOS"].max()
        if vmin == vmax:
            df["vpos_score"] = 1.0
            if logger:
                logger.warning(
                    "All VPOS values are equal; assigned vpos_score=1.0 to all rows.")
        else:
            df["vpos_score"] = np.round(
                1 - (df["VPOS"] - vmin) / (vmax - vmin), 2)
    except Exception as e:
        if logger:
            logger.error(f"Error calculating vpos_score: {e}")
        df["vpos_score"] = 0.0
    return df


def kde_gaussian(df: pd.DataFrame, logger: logging.Logger | None = None) -> pd.DataFrame:
    """
    Apply Gaussian KDE to detect density hotspots of candidate dates.

    Args:
        df (pd.DataFrame): Must contain 'HPOS' and 'VPOS'.
        logger (logging.Logger, optional): Logger for reporting.

    Returns:
        pd.DataFrame: DataFrame with new column 'kde_score'.
    """
    try:
        if df.empty:
            df["kde_score"] = []
            if logger:
                logger.warning("Empty DataFrame provided to kde_gaussian.")
            return df

        xy = np.vstack([df["HPOS"], df["VPOS"]])
        z = gaussian_kde(xy)(xy)
        if z.max() == z.min():
            df["kde_score"] = 0.5
            if logger:
                logger.warning(
                    "KDE produced constant values; assigned kde_score=0.5 to all rows.")
        else:
            df["kde_score"] = np.round((z - z.min()) / (z.max() - z.min()), 2)
    except Exception as e:
        if logger:
            logger.error(f"Error calculating kde_gaussian: {e}")
        df["kde_score"] = 0.0
    return df

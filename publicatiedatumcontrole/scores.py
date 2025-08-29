import numpy as np
from scipy.stats import gaussian_kde


def vpos_score(df):
    """
    Convert VPOS naar score tussen 0–1.
    Publicatiedatum staat meestal bovenaan de pagina (lage VPOS).
    """
    df = df.copy()
    if df["VPOS"].max() == df["VPOS"].min():
        df["vpos_score"] = 0.0
    else:
        df["vpos_score"] = np.round(
            1 - (df["VPOS"] - df["VPOS"].min()) /
            (df["VPOS"].max() - df["VPOS"].min()), 2
        )
    return df


def kde_gaussian(df):
    """
    Kernel Density Estimation using Gaussian kernels.
    """
    df = df.copy()
    x = df['HPOS']
    y = df['VPOS']

    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)

    if z.max() == z.min():
        df['kde_score'] = 0.0
    else:
        z = np.round((z - z.min()) / (z.max() - z.min()), 2)
        df['kde_score'] = z

    return df

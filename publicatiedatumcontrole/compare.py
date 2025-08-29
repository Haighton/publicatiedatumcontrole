def compare_dates(df):
    """
    Vergelijk alto_date met mets_date en bereken afstandsscore.
    """
    df = df.copy()  # voorkomt SettingWithCopyWarning

    a_date = df['alto_date'].str.split('-')
    m_date = df['mets_date'].str.split('-')

    # Helper: verwijder leading zeros
    def lead_zero(dates):
        return [[adf.lstrip('0') for adf in ad] for ad in dates]

    a_date = lead_zero(a_date)
    m_date = lead_zero(m_date)

    dis_score = []
    for i in range(len(m_date)):
        try:
            year_diff = abs(int(a_date[i][0]) - int(m_date[i][0]))
            month_diff = abs(int(a_date[i][1]) - int(m_date[i][1]))
            day_diff = abs(int(a_date[i][2]) - int(m_date[i][2]))
            dis_score.append(year_diff + month_diff + day_diff)
        except Exception:
            dis_score.append(9999)  # fallback bij parsing errors

    df["distance_score"] = dis_score
    return df

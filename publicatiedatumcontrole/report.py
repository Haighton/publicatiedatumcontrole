import os
import time
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image


def plot_fig(df_errors, path_batch, current_title, output_dir, df_all, logger=None):
    """
    Plot alle gevonden datumcoördinaten (df_all) met scores,
    en markeer de fouten (df_errors) in een scatterplot.
    """
    try:
        bgfile = df_errors.iloc[0]["filename"]

        # zoek access bestand
        acpath = os.path.join(path_batch, bgfile, "access", f"{bgfile}_00001_access.jp2")
        if not os.path.exists(acpath):
            if logger:
                logger.warning(f"Achtergrondbestand ontbreekt: {acpath}")
            return

        img = plt.imread(acpath)
        fig, ax = plt.subplots()

        sc = ax.scatter(df_all["HPOS"], df_all["VPOS"],
                        c=df_all["score"], s=50,
                        cmap="inferno", alpha=0.4, label="Alle datums")

        ax.scatter(df_errors["HPOS"], df_errors["VPOS"],
                   c="red", marker="x", s=80, label="Fouten")

        ax.set_title("Coördinaten van gevonden datums in ALTO's")
        ax.set_xlabel("HPOS")
        ax.set_ylabel("VPOS")
        ax.invert_yaxis()

        cbar = plt.colorbar(sc)
        cbar.set_label("Score", rotation=270)

        for side in ax.spines.values():
            side.set_color("0.5")

        ax.imshow(img, alpha=0.7)

        current_title_ = "".join(current_title.split())[:6]
        fig_filename = f"fig_{current_title_}.png"

        os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
        outpath = os.path.join(output_dir, "images", fig_filename)
        plt.savefig(outpath)
        plt.close(fig)

        if logger:
            logger.info(f"Plot opgeslagen: {outpath}")

    except Exception as e:
        if logger:
            logger.error(f"Kon figuur niet genereren voor {current_title}: {e}")


def generate_html_log(df_errors, path_batch, current_title, output_dir, logger=None, threshold=0.8):
    """
    Genereer een HTML-rapport met datumdiscrepanties, snippets en access links.
    """
    try:
        os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

        rows = []
        for _, row in df_errors.iterrows():
            file_id = row["filename"]
            access_file = os.path.join(path_batch, file_id, "access", f"{file_id}_00001_access.jp2")

            thumb_html = "(geen snippet – bestand ontbreekt)"
            if os.path.exists(access_file):
                try:
                    thumb_rel = os.path.join("images", f"{file_id}_date.jpg")
                    thumb_abs = os.path.join(output_dir, thumb_rel)

                    img = Image.open(access_file)
                    crop_img = img.crop((row["HPOS"] - 140, row["VPOS"] - 20,
                                         row["HPOS"] + 700, row["VPOS"] + 80))

                    baseheight = 30
                    hpercent = baseheight / float(crop_img.size[1])
                    wsize = int((float(crop_img.size[0]) * hpercent))
                    crop_img = crop_img.resize(
                        (wsize, baseheight), Image.LANCZOS)

                    crop_img.save(thumb_abs, "JPEG", quality=90)
                    thumb_html = f'<img src="{thumb_rel}" alt="snippet">'
                except Exception as e:
                    if logger:
                        logger.error(f"Kon snippet niet maken voor {file_id}: {e}")

            access_link = (
                f'<a target="_blank" href="{access_file}">{os.path.basename(access_file)}</a>'
                if os.path.exists(access_file)
                else "(geen access-bestand)"
            )

            rows.append({
                "Issue ID": file_id,
                "Publicatiedatum Metadata": row.get("mets_date", ""),
                "Datum ALTO": row.get("alto_date", ""),
                "Datum scan": thumb_html,
                "Access bestand": access_link
            })

        df_html = pd.DataFrame(rows)
        html_table = df_html.to_html(escape=False, index=False)

        current_title_ = "".join(current_title.split())[:6]
        fig_rel = f"images/fig_{current_title_}.png"
        fig_html = f'<img src="{fig_rel}" alt="Plot" style="max-width:100%;">'

        # HTML met styles en threshold
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>publicatiedatumcontrole-report</title>
    <style>
        body {{
            font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
            margin: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        td, th {{
            border: 1px solid #ddd;
            padding: 8px;
        }}
        tr:nth-child(even){{background-color: #f9f9f9;}}
        tr:hover {{background-color: #f1f1f1;}}
        th {{
            padding-top: 12px;
            padding-bottom: 12px;
            text-align: left;
            background-color: #4CAF50;
            color: white;
        }}
    </style>
</head>
<body>
    <h1>publicatiedatumcontrole-report</h1>
    <h2>Batch: {os.path.basename(path_batch)}</h2>
    <h3>Krant: {current_title}</h3>
    <p>Threshold gebruikt: {threshold}</p>
    {html_table}
    <h3>Locatie van datums in pagina's</h3>
    {fig_html}
</body></html>"""

        fname = (
            f"publicatiedatumcontrole-report_{current_title_}"
            f"_thr{str(threshold).replace('.', '_')}_{time.strftime('%Y%m%d_%H%M')}.html"
        )

        outpath = os.path.join(output_dir, fname)
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(html)

        if logger:
            logger.info(f"HTML log opgeslagen: {outpath}")

    except Exception as e:
        if logger:
            logger.error(f"Kon HTML log niet genereren voor {current_title}: {e}")

import os
import time
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt


def plot_fig(df_errors, path_batch, current_title, log_path, df_all, logger=None) -> str:
    """Maak een scatter plot van alle gevonden datum-coördinaten."""
    try:
        bgfile = df_errors.iloc[0, 0]
        acpath = os.path.join(path_batch, bgfile, "access", f"{bgfile}_00001_access.jp2")
        img = plt.imread(acpath)

        fig, ax = plt.subplots()
        plt.scatter(df_all["HPOS"], df_all["VPOS"], c=df_all["score"],
                    s=50, cmap="inferno", alpha=0.4)

        plt.title("All Coordinates of Dates Found in ALTO's")
        plt.xlabel("HPOS")
        plt.ylabel("VPOS")
        plt.gca().invert_yaxis()

        cbar = plt.colorbar()
        cbar.set_label("Score", rotation=270)
        cbar.ax.tick_params(size=0)

        ax.spines["bottom"].set_color("0.5")
        ax.spines["top"].set_color("0.5")
        ax.spines["right"].set_color("0.5")
        ax.spines["left"].set_color("0.5")

        ax.imshow(img, alpha=0.7)

        current_title_ = "".join(current_title.split())[:6]
        fig_filename = f"fig_{current_title_}.png"

        out_path = os.path.abspath(os.path.join(
            log_path, "images", fig_filename))
        plt.savefig(out_path)
        plt.close(fig)

        return out_path
    except Exception as e:
        if logger:
            logger.error(f"Kon figuur niet genereren voor {current_title}: {e}")
        return ""


def generate_html_log(df_errors, path_batch, current_title, log_path, logger=None, threshold: float = 0.8) -> str:
    """Genereer HTML-rapport met tabellen en snippets. Geeft pad terug."""
    try:
        df_errors = df_errors.reset_index()
        df_errors = df_errors[["filename",
                               "alto_date", "mets_date", "VPOS", "HPOS"]]

        # thumbnails maken
        fnames, thumb_paths = [], []
        for file_id, vpos, hpos in zip(df_errors["filename"], df_errors["VPOS"], df_errors["HPOS"]):
            try:
                access_path = os.path.join(path_batch, file_id, "access", f"{file_id}_00001_access.jp2")
                img = Image.open(access_path)
                crop_img = img.crop(
                    (hpos - 140, vpos - 20, hpos + 700, vpos + 80))
                baseheight = 30
                hpercent = baseheight / float(crop_img.size[1])
                wsize = int((float(crop_img.size[0]) * hpercent))
                crop_img = crop_img.resize((wsize, baseheight), Image.LANCZOS)

                impath_abs = os.path.abspath(os.path.join(log_path, "images", f"{file_id}_date.jpg"))
                impath_rel = os.path.join("images", f"{file_id}_date.jpg")
                crop_img.save(impath_abs, "JPEG", quality=90)

                thumb_paths.append(f'<img src="{impath_rel}" alt="snippet">')
                fnames.append(file_id)
            except Exception as e:
                if logger:
                    logger.error(f"Kon snippet niet maken voor {file_id}: {e}")

        df_img = pd.DataFrame({"filename": fnames, "thumb_paths": thumb_paths})
        df_table = df_errors.merge(df_img, on="filename", how="left")

        col_html = ["filename", "mets_date", "alto_date", "thumb_paths"]
        df_table = df_table.loc[:, col_html]
        df_table = df_table.rename(columns={
            "filename": "Issue ID",
            "mets_date": "Metadata date",
            "alto_date": "ALTO candidate",
            "thumb_paths": "Snippet"
        })

        html_table = df_table.to_html(escape=False, index=False)

        current_title_ = "".join(current_title.split())[:6]
        html_start = f"""<!DOCTYPE html>
<html>
<head>
  <title>Log Publicatiedatumcontrole</title>
  <style>
    table {{ font-family: Arial, sans-serif; border-collapse: collapse; width: 100%; }}
    td, th {{ border: 1px solid #ddd; padding: 8px; }}
    tr:nth-child(even) {{ background-color: #f2f2f2; }}
    tr:hover {{ background-color: #ddd; }}
    th {{ padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #4CAF50; color: white; }}
  </style>
</head>
<body>
  <h1>Publication date control</h1>
  <h2>Batch: {os.path.basename(path_batch)}</h2>
  <h3>Newspaper: {current_title}</h3>
"""
        html_end = "</body></html>"

        fig_filename = f"fig_{current_title_}.png"
        fig_html = f'<img src="images/{fig_filename}">'

        html_result = html_start + html_table + fig_html + html_end

        fname = f"publicatiedatumcontrole-report_{current_title_}_{time.strftime('%Y%m%d_%H%M')}.html"
        out_path = os.path.abspath(os.path.join(log_path, fname))
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_result)

        return out_path
    except Exception as e:
        if logger:
            logger.error(f"Kon HTML log niet genereren voor {current_title}: {e}")
        return ""


def generate_xml_log(df_errors, path_batch, current_title, log_path, logger=None, threshold: float = 0.8) -> str:
    """Genereer XML-rapport (machine-readable). Geeft pad terug."""
    from lxml import etree

    try:
        root = etree.Element("PublicationDateCheck")
        root.set("batch", os.path.basename(path_batch))
        root.set("title", current_title)
        root.set("threshold", str(threshold))

        for _, row in df_errors.iterrows():
            issue = etree.SubElement(root, "Issue")
            etree.SubElement(issue, "Filename").text = str(row["filename"])
            etree.SubElement(issue, "METSdate").text = str(row["mets_date"])
            etree.SubElement(issue, "ALTOdate").text = str(row["alto_date"])
            etree.SubElement(issue, "VPOS").text = str(row["VPOS"])
            etree.SubElement(issue, "HPOS").text = str(row["HPOS"])
            etree.SubElement(issue, "DistanceScore").text = str(
                row.get("distance_score", ""))

        fname = f"publicatiedatumcontrole-report_{''.join(current_title.split())[:6]}_{time.strftime('%Y%m%d_%H%M')}.xml"
        out_path = os.path.abspath(os.path.join(log_path, fname))

        tree = etree.ElementTree(root)
        tree.write(out_path, pretty_print=True,
                   xml_declaration=True, encoding="utf-8")

        return out_path
    except Exception as e:
        if logger:
            logger.error(f"Kon XML log niet genereren voor {current_title}: {e}")
        return ""

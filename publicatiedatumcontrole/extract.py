from lxml import etree
import os


def get_alto_data(alto_file, logger=None):
    """
    Extract //String/@CONTENT attributes uit een ALTO-bestand.
    """
    alto_file_content = []
    try:
        with open(alto_file, "rb") as alto:
            context = etree.iterparse(alto, events=("start", "end"))
            for event, elem in context:
                if event == "end" and etree.QName(elem.tag).localname == "String":
                    alto_file_content.append([
                        elem.get("CONTENT"),
                        (int(elem.get("VPOS")), int(elem.get("HPOS")))
                    ])
            elem.clear()
        return alto_file_content
    except Exception as e:
        if logger:
            logger.error(f"Fout bij verwerken ALTO {alto_file}: {e}")
        return []


def extract_mets_data(mets_files, logger=None):
    """
    Extract publication date, title, edition uit METS bestanden.
    """
    filenames, mets_dates, mets_titles, mets_editions = [], [], [], []
    for count, mets_file in enumerate(mets_files, start=1):
        try:
            if logger:
                logger.info(f"Extracting data from METS: {os.path.basename(mets_file)} ({count}/{len(mets_files)})")
            np_titles, np_dates, np_editions = [], [], []
            with open(mets_file, "rb") as mets:
                context = etree.iterparse(mets, events=("start", "end"))
                for _, elem in context:
                    if elem.tag == "{http://www.loc.gov/mods/v3}mods":
                        for elem_child in elem:
                            if elem_child.tag == "{http://www.loc.gov/mods/v3}relatedItem":
                                for elem_child2 in elem_child:
                                    if elem_child2.tag.endswith("titleInfo"):
                                        for elem_child3 in elem_child2:
                                            if elem_child3.tag.endswith("title") and elem_child3.text:
                                                np_titles.append(
                                                    elem_child3.text.strip())
                                    elif elem_child2.tag.endswith("part"):
                                        for elem_child3 in elem_child2:
                                            if elem_child3.tag.endswith("date") and elem_child3.text:
                                                np_dates.append(
                                                    elem_child3.text.strip())
                                    elif elem_child2.tag.endswith("originInfo"):
                                        for elem_child3 in elem_child2:
                                            if elem_child3.tag.endswith("edition") and elem_child3.text:
                                                np_editions.append(
                                                    elem_child3.text.strip())
                        elem.clear()
            filenames.append(os.path.basename(
                mets_file).replace("_mets.xml", ""))
            mets_titles.append(np_titles[0] if np_titles else None)
            mets_dates.append(np_dates[0] if np_dates else None)
            mets_editions.append(np_editions[0] if np_editions else None)
        except Exception as e:
            if logger:
                logger.error(f"Fout in METS {mets_file}: {e}")
            filenames.append(os.path.basename(mets_file))
            mets_titles.append(None)
            mets_dates.append(None)
            mets_editions.append(None)

    return {
        "filename": filenames,
        "mets_date": mets_dates,
        "mets_title": mets_titles,
        "mets_edition": mets_editions,
    }

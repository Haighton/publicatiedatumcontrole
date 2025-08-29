# publicatiedatumcontrole

Check whether the publication date printed on the front page of a digitized Dutch newspaper (ALTO) matches the official publication date recorded in its metadata (METS/MODS).

This script is used in KB's data quality assurance process to detect discrepancies between scanned newspaper content and its metadata, as well as errors caused by faulty data entry.

---

## Method

The tool tries to extract the **publication date** from the front page of a digitized newspaper by analyzing the **first ALTO XML file** of each issue (the first page is always the front page). The extracted candidate dates are then compared against the official publication date recorded in the corresponding **METS/MODS XML metadata**.

### Assumptions about Dutch newspapers
- **Fixed layout:** Dutch newspapers historically have a fairly consistent layout across issues. This means that the **publication date is always printed in more or less the same physical location** on the front page.  
- **Header placement:** The publication date is always located in the **upper portion of the newspaper** (the header). In terms of ALTO coordinates, this corresponds to a relatively **low Y-position (VPOS)** value.  

### Candidate scoring
To increase confidence in the extracted date candidates, the tool applies two scoring methods:

1. **VPOS score (vertical position):**  
   Since publication dates always occur near the top of the page, we normalize the vertical position (VPOS) of each detected date string.  
   - Candidates closer to the top get a higher score (closer to 1.0).  
   - Text further down the page is penalized.  

2. **Kernel Density Estimation (KDE):**  
   Across many issues of the same title and edition, the publication date is printed at roughly the same coordinates.  
   - We apply **Gaussian KDE** to all detected date positions across a batch.  
   - This highlights “hotspots” where dates are most likely located.  
   - Candidates within these high-density regions receive a higher KDE score.  

The final candidate score is the mean of these two values. Only candidates above a configurable threshold (default `0.8`) are kept as potential publication dates.

---

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/Haighton/publicatiedatumcontrole.git
cd publicatiedatumcontrole
pip install -e .
```

---

## Usage

Run the tool on one or multiple batch folders:

```bash
python -m publicatiedatumcontrole [OPTIONS] <batch1> <batch2> ...
```

### Command-line options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--verbose` | | off | Enable verbose logging (debug-level output). |
| `--threshold <float>` | | `0.8` | Score threshold for selecting candidate publication dates. Candidates with a score below this value are ignored. |
| `--output <path>` | `-o` | `html-reports` | Directory where reports will be written. A subdirectory per batch will be created. |
| `--help` | `-h` | | Show help message and exit. |

### Examples

Run with default settings:

```bash
python -m publicatiedatumcontrole /data/batch1
```

Run multiple batches with verbose logging:

```bash
python -m publicatiedatumcontrole /data/batch1 /data/batch2 --verbose
```

Lower threshold (e.g. 0.7) and custom output folder:

```bash
python -m publicatiedatumcontrole /data/batch1 --threshold 0.7 -o ./reports
```

---

## Output

The tool generates:

- **Per-batch HTML reports**, containing:
	- A table of candidate discrepancies between ALTO and METS/MODS dates.
	- Cropped snippets of the detected date from the page image.
	- A density plot showing the distribution of detected dates.
- Reports are stored in a configurable output directory (default: `html-reports/`).

---

_Developed by T.Haighton for KB Digitalisering (updated 08-2025)_

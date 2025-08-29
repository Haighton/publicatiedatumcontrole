# Publicatiedatumcontrole

Dit project controleert publicatiedata in gedigitaliseerde kranten aan de hand van ALTO- en METS/MODS-bestanden.

## Installatie

```bash
git clone <repo-url>
cd publicatiedatumcontrole
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Gebruik

Via CLI:

```bash
publicatiedatumcontrole <inputmap> -o rapport.md --log fouten.log
```

Of als module:

```bash
python -m publicatiedatumcontrole <inputmap>
```

## Features
- Extractie van publicatiedata uit ALTO en METS/MODS XML
- Vergelijking en validatie van datums
- Rapportage in Markdown
- Logging van fouten en waarschuwingen

## To-do / Verbeteringen
- Unit tests uitbreiden
- Robuustere error handling (try/except)
- CI pipeline toevoegen (GitHub Actions)

"""Gemeinsame Hilfsfunktionen für die EV-Clustering-Pipeline.

Enthält Logging-Setup, Pfad-Konstanten (relativ zum Projektroot), die
Normalisierung von Spaltennamen (snake_case ohne Umlaute), AGS-Standardisierung
sowie das IQR-Outlier-Flagging.
"""

from __future__ import annotations

import logging
import sys
import unicodedata
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Pfade — immer relativ zum Projektroot (ev_clustering_grossstaedte/)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MASTER_DIR = DATA_DIR / "master"
OUTPUT_DIR = PROJECT_ROOT / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"

# Globaler Seed für Reproduzierbarkeit
RANDOM_STATE = 42

# CSV-Standardparameter (Excel-kompatibel, deutsches Encoding)
CSV_KWARGS = {"index": False, "encoding": "utf-8-sig"}

_UMLAUT_MAP = {
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
}


def setup_logging(name: str) -> logging.Logger:
    """Konfiguriere ein Logger-Objekt mit Level INFO und einheitlichem Format.

    Args:
        name: Name des Loggers, üblicherweise der Skriptname.

    Returns:
        Konfiguriertes :class:`logging.Logger`-Objekt, das auf stdout schreibt.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                              datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def ensure_dirs() -> None:
    """Erstelle alle benötigten Ausgabeverzeichnisse (idempotent)."""
    for directory in (RAW_DIR, PROCESSED_DIR, MASTER_DIR, FIGURES_DIR, TABLES_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def replace_umlauts(text: str) -> str:
    """Ersetze deutsche Umlaute und ß durch ASCII-Äquivalente.

    Args:
        text: Eingabetext.

    Returns:
        Text ohne Umlaute (ä->ae, ö->oe, ü->ue, ß->ss).
    """
    for src, dst in _UMLAUT_MAP.items():
        text = text.replace(src, dst)
    return text


def normalize_column(name: object) -> str:
    """Normalisiere einen Spaltennamen zu lowercase snake_case ohne Umlaute.

    Args:
        name: Roher Spaltenname (beliebiger Typ, wird zu str konvertiert).

    Returns:
        Bereinigter Spaltenname, z.B. ``"Verfügbares Einkommen"`` -> ``"verfuegbares_einkommen"``.
    """
    text = replace_umlauts(str(name)).strip().lower()
    # verbliebene Nicht-ASCII-Zeichen (Akzente etc.) entfernen
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    out_chars = []
    for ch in text:
        out_chars.append(ch if ch.isalnum() else "_")
    result = "".join(out_chars)
    # Mehrfach-Unterstriche zusammenfassen und trimmen
    while "__" in result:
        result = result.replace("__", "_")
    return result.strip("_")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Wende :func:`normalize_column` auf alle Spalten eines DataFrames an.

    Args:
        df: Eingabe-DataFrame.

    Returns:
        DataFrame mit normalisierten Spaltennamen (Kopie der Spaltenachse).
    """
    df = df.copy()
    df.columns = [normalize_column(c) for c in df.columns]
    return df


def to_numeric_de(series: pd.Series) -> pd.Series:
    """Konvertiere eine Spalte robust nach float (deutsche Zahlenformate).

    Behandelt Tausenderpunkte, Dezimalkommata, geschützte Leerzeichen und
    Platzhalter wie ``-``, ``x`` oder ``.``.

    Args:
        series: Eingabespalte (typischerweise Strings).

    Returns:
        Float-Spalte; nicht parsbare Werte werden zu NaN.
    """
    cleaned = (
        series.astype(str)
        .str.replace(" ", "", regex=False)   # geschütztes Leerzeichen
        .str.replace(" ", "", regex=False)
        .str.replace(".", "", regex=False)          # Tausenderpunkt
        .str.replace(",", ".", regex=False)         # Dezimalkomma
        .replace({"-": pd.NA, "": pd.NA, "nan": pd.NA, "x": pd.NA,
                  "X": pd.NA, ".": pd.NA, "None": pd.NA})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def flag_outliers_iqr(df: pd.DataFrame, columns: list[str], factor: float = 1.5) -> pd.DataFrame:
    """Markiere Ausreißer per IQR-Methode in einer neuen Spalte ``is_outlier``.

    Ausreißer werden NICHT entfernt (kleines n), sondern nur geflaggt.

    Args:
        df: Eingabe-DataFrame.
        columns: Numerische Spalten, die geprüft werden.
        factor: IQR-Multiplikator (Standard 1.5).

    Returns:
        DataFrame mit zusätzlicher Bool-Spalte ``is_outlier``.
    """
    df = df.copy()
    mask = pd.Series(False, index=df.index)
    for col in columns:
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lower, upper = q1 - factor * iqr, q3 + factor * iqr
        mask |= (series < lower) | (series > upper)
    df["is_outlier"] = mask
    return df

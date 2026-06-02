"""Schritt 3 — Datenzusammenführung & Feature Engineering.

Führt die bereinigten Einzeldatensätze aus ``data/processed/`` zu einer
Master-Tabelle ``data/master/master_cities.csv`` zusammen (eine Zeile je
Zielstadt aus :data:`city_list.TARGET_CITIES`) und berechnet die abgeleiteten
Features für das k-Means++-Clustering.

Verknüpfungslogik (Schlüssel = 8-stelliger AGS):
    * EV-Anteil  (cleaned_EV_Anteil.csv)      -> Spalte ``AGS``  (normalisiert)
    * Einwohner  (cleaned_einwohnerzahlen.csv) -> 12-stelliger RS -> AGS = RS[:5]+RS[-3:]
    * Einkommen  (cleaned_income.csv)          -> Kreis-RS = AGS[:5] (Fallback AGS[:2]
                                                  für die Stadtstaaten Berlin/Hamburg)
    * Ladepunkte (cleaned_Laderegister.csv)    -> Aggregation über den Ortsnamen
                                                  (exakt + sichere Stadtteil-Schreibweisen)

Resultierende Features (4 Dimensionen, je Themenfeld eines):
    * ev_anteil_pct          — Pkw-Elektro-Anteil in % (EV)
    * ladepunkte_pro_1000ew  — Ladepunkte je 1.000 Einwohner (Infrastruktur)
    * einkommen_eur          — Primäreinkommen je Einwohner in EUR (Einkommen)
    * bev_dichte             — Einwohner je km² (Population)
zzgl. der Rohgrößen (ladepunkte_gesamt, einwohner) für Nachvollziehbarkeit.

Aufruf:
    python src/03_merge.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from city_list import TARGET_CITIES, normalize_ags  # noqa: E402
import utils  # noqa: E402

logger = utils.setup_logging("03_merge")

PROCESSED = utils.PROCESSED_DIR
OUT_FILE = utils.MASTER_DIR / "master_cities.csv"

# Referenz-Berichtszeitpunkt für den EV-Anteil (jüngster Stand der Zeitreihe).
EV_PERIOD = "2026.04"


# ---------------------------------------------------------------------------
# Einzel-Loader: liefern jeweils einen DataFrame mit Spalte ``ags`` + Feature
# ---------------------------------------------------------------------------
def load_ev_anteil(period: str = EV_PERIOD) -> pd.DataFrame:
    """Lade EV-Anteil je Gemeinde zum Berichtszeitpunkt ``period``.

    Die Quelle enthält eine Quartals-Zeitreihe (mehrere Zeilen je AGS); es wird
    der Stand ``period`` ausgewählt. Der Anteil ist englisch formatiert (Punkt
    als Dezimaltrenner) und wird daher direkt – nicht über
    :func:`utils.to_numeric_de` – nach float konvertiert.
    """
    df = pd.read_csv(PROCESSED / "cleaned_EV_Anteil.csv", dtype=str)
    df["ags"] = df["AGS"].apply(normalize_ags)
    df["ev_anteil_pct"] = pd.to_numeric(df["Pkw Elektro Anteil"], errors="coerce")
    sel = df[df["Berichtszeitpunkt"] == period]
    if sel.empty:
        raise ValueError(f"EV-Berichtszeitpunkt {period!r} nicht im Datensatz gefunden")
    out = sel[["ags", "ev_anteil_pct"]].dropna(subset=["ags"]).drop_duplicates("ags")
    logger.info("EV-Anteil: %d Gemeinden zum Stand %s geladen", len(out), period)
    return out


def load_einwohner() -> pd.DataFrame:
    """Lade Einwohnerzahl + Bevölkerungsdichte je Stadt.

    Der 12-stellige Amtliche Regionalschlüssel wird auf den 8-stelligen AGS
    abgebildet: ``AGS = ziffern[:5] + ziffern[-3:]`` (Land+RB+Kreis + Gemeinde).
    """
    df = pd.read_csv(
        PROCESSED / "cleaned_einwohnerzahlen.csv", dtype=str, skiprows=2, header=None
    )
    df.columns = ["id", "rs", "name", "plz", "flaeche", "bev", "dichte"]
    df = df[df["rs"].notna()].copy()
    digits = df["rs"].str.replace(r"\D", "", regex=True)
    df["ags"] = digits.str[:5] + digits.str[-3:]
    # Werte ganzzahlig bzw. englisch formatiert -> direkt parsen.
    df["einwohner"] = pd.to_numeric(df["bev"], errors="coerce")
    df["bev_dichte"] = pd.to_numeric(df["dichte"], errors="coerce")
    out = (
        df[["ags", "einwohner", "bev_dichte"]]
        .dropna(subset=["ags"])
        .drop_duplicates("ags")
    )
    logger.info("Einwohner: %d Städte geladen", len(out))
    return out


def load_income() -> pd.DataFrame:
    """Lade Primäreinkommen je Einwohner auf Kreis-Ebene (5-stelliger RS)."""
    df = pd.read_csv(
        PROCESSED / "cleaned_income.csv", dtype=str, skiprows=6, header=None
    )
    df.columns = ["nr", "eu", "rs", "name", "val"]
    df = df[df["rs"].notna()].copy()
    df["rs"] = df["rs"].str.strip()
    # Werte sind englisch formatiert (Punkt als Dezimaltrenner) -> direkt parsen.
    df["einkommen_eur"] = pd.to_numeric(df["val"], errors="coerce")
    out = df[["rs", "einkommen_eur"]].dropna(subset=["einkommen_eur"])
    logger.info("Einkommen: %d Regionen geladen", len(out))
    return out


def income_for_ags(income: pd.DataFrame, ags: str) -> float:
    """Hole den Einkommenswert für einen AGS über den Kreis-RS (AGS[:5]).

    Fällt auf den 2-stelligen Land-RS zurück (Stadtstaaten Berlin/Hamburg,
    die im Einkommensdatensatz nur auf Landesebene vorliegen).
    """
    lut = dict(zip(income["rs"], income["einkommen_eur"]))
    for key in (ags[:5], ags[:5].lstrip("0"), ags[:2], ags[:2].lstrip("0")):
        if key in lut:
            return lut[key]
    return float("nan")


def load_ladepunkte() -> pd.DataFrame:
    """Aggregiere Ladepunkte je Zielstadt über den Ortsnamen.

    Strategie (gewählt: *exakt + sichere Stadtteile*):
        * exakter Treffer ``Ort == Stadtname`` ODER
        * Stadtteil-/Ortsteil-Schreibweise ``Ort`` beginnt mit ``"<Stadt> "``,
          ``"<Stadt>-"`` oder ``"<Stadt>/"`` und enthält KEINE abweichende
          Klammer-Disambiguierung (verhindert Fehlzuordnungen wie
          „Mülheim (Mosel)“ → „Mülheim an der Ruhr“ oder
          „Halle (Westf.)“ → „Halle (Saale)“).

    Returns:
        DataFrame mit Spalten ``stadt`` und ``ladepunkte_gesamt``.
    """
    df = pd.read_csv(PROCESSED / "cleaned_Laderegister.csv", dtype=str)
    df["Ort"] = df["Ort"].astype(str).str.strip()
    df["pts"] = utils.to_numeric_de(df["Anzahl Ladepunkte"]).fillna(0)

    rows: list[dict[str, object]] = []
    for stadt in TARGET_CITIES.values():
        exact = df["Ort"] == stadt
        # Stadtteil-Schreibweisen: Präfix "<Stadt><Trenner>" …
        prefix = df["Ort"].str.startswith(tuple(f"{stadt}{sep}" for sep in (" ", "-", "/")))
        # … aber keine abweichende Klammer-Angabe (z. B. "(Mosel)", "(Westf.)")
        no_other_paren = ~df["Ort"].str.contains(r"\(", regex=True)
        mask = exact | (prefix & no_other_paren)
        rows.append({"stadt": stadt, "ladepunkte_gesamt": float(df.loc[mask, "pts"].sum())})

    out = pd.DataFrame(rows)
    logger.info(
        "Ladepunkte: %d Städte aggregiert (Summe %d Ladepunkte)",
        len(out),
        int(out["ladepunkte_gesamt"].sum()),
    )
    return out


# ---------------------------------------------------------------------------
# Zusammenführung
# ---------------------------------------------------------------------------
def build_master() -> pd.DataFrame:
    """Baue die Master-Tabelle (eine Zeile je Zielstadt) und die Features."""
    ev = load_ev_anteil()
    ein = load_einwohner()
    income = load_income()
    lade = load_ladepunkte()

    # Gerüst: alle 77 Zielstädte aus der Whitelist
    base = pd.DataFrame(
        [{"ags": ags, "stadt": name} for ags, name in TARGET_CITIES.items()]
    )

    # AGS-basierte Joins (EV, Einwohner) — left join auf das Gerüst
    df = base.merge(ev, on="ags", how="left").merge(ein, on="ags", how="left")

    # Einkommen je Kreis-RS (mit Stadtstaaten-Fallback)
    df["einkommen_eur"] = df["ags"].apply(lambda a: income_for_ags(income, a))

    # Ladepunkte über den Stadtnamen
    df = df.merge(lade, on="stadt", how="left")

    # abgeleitetes Feature: Ladepunkte je 1.000 Einwohner
    df["ladepunkte_pro_1000ew"] = (
        df["ladepunkte_gesamt"] / df["einwohner"] * 1000.0
    )

    # Spaltenreihenfolge: Schlüssel/Identität, dann Features, dann Rohgrößen
    cols = [
        "ags",
        "stadt",
        "ev_anteil_pct",          # EV
        "ladepunkte_pro_1000ew",  # Infrastruktur (clustering-fähig)
        "einkommen_eur",          # Einkommen
        "bev_dichte",             # Population
        "ladepunkte_gesamt",      # Rohgröße
        "einwohner",              # Rohgröße
    ]
    df = df[cols].sort_values("stadt").reset_index(drop=True)
    return df


def report_coverage(df: pd.DataFrame) -> None:
    """Logge Vollständigkeit je Feature und liste fehlende Werte auf."""
    feature_cols = [
        "ev_anteil_pct",
        "ladepunkte_pro_1000ew",
        "einkommen_eur",
        "bev_dichte",
    ]
    logger.info("Master-Tabelle: %d Zeilen (Soll: %d)", len(df), len(TARGET_CITIES))
    for col in feature_cols:
        n_ok = int(df[col].notna().sum())
        logger.info("  %-24s %2d/%2d belegt", col, n_ok, len(df))
        missing = df.loc[df[col].isna(), "stadt"].tolist()
        if missing:
            logger.warning("    fehlend in %s: %s", col, ", ".join(missing))


def main() -> int:
    """Einstiegspunkt: Master-Tabelle bauen, prüfen und schreiben."""
    utils.ensure_dirs()
    df = build_master()
    report_coverage(df)

    if len(df) != len(TARGET_CITIES):
        logger.error("Zeilenzahl weicht ab — Abbruch."); return 1

    df.to_csv(OUT_FILE, **utils.CSV_KWARGS)
    logger.info("Master-Tabelle geschrieben: %s", OUT_FILE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

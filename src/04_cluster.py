"""Schritt 4 — Standardisierung, k-Bestimmung & k-Means++-Clustering.

Liest die Master-Tabelle ``data/master/master_cities.csv``, standardisiert die
vier Clustering-Features (z-Transformation), bestimmt eine geeignete Clusterzahl
``k`` über Elbow- (Inertia) und Silhouettenanalyse, fittet k-Means++ und schreibt:

    * ``output/tables/cluster_assignments.csv`` — eine Zeile je Stadt mit Cluster
    * ``output/tables/cluster_profile.csv``     — Mittelwerte je Cluster (Originaleinheiten)
    * ``output/figures/elbow_silhouette.png``   — Diagnose zur k-Wahl
    * ``output/figures/cluster_scatter.png``    — 2D-PCA-Streudiagramm der Cluster

Aufruf:
    python src/04_cluster.py            # k automatisch (bestes Silhouette in K_RANGE)
    python src/04_cluster.py --k 4      # k manuell vorgeben
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # kein GUI-Backend (headless)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))

import utils  # noqa: E402

logger = utils.setup_logging("04_cluster")

MASTER_FILE = utils.MASTER_DIR / "master_cities.csv"

# Die vier Clustering-Features (je Themenfeld eines) und ihre Klartext-Labels.
FEATURES: dict[str, str] = {
    "ev_anteil_pct": "EV-Anteil (%)",
    "ladepunkte_pro_1000ew": "Ladepunkte je 1.000 EW",
    "einkommen_eur": "Einkommen (EUR)",
    "bev_dichte": "Bev.-Dichte (EW/km²)",
}

# Kandidaten-Clusterzahlen für die Diagnose (n=77 → 2..8 ist sinnvoll).
K_RANGE = range(2, 9)

# Gewählte Clusterzahl für den finalen Lauf. Das Silhouettenmaximum liegt bei
# k=2 (0.44), trennt aber nur die wohlhabende, EV-affine Spitzengruppe vom Rest.
# Für eine interpretierbare Stadttypologie (mehrere charakterisierbare Cluster)
# wird k=4 gewählt; die Diagnose (Elbow + Silhouette) wird mitgeschrieben und
# begründet die Wahl. Mit ``--k`` überschreibbar.
DEFAULT_K = 4


def load_features() -> tuple[pd.DataFrame, np.ndarray]:
    """Lade die Master-Tabelle und gib (DataFrame, standardisierte Matrix) zurück."""
    df = pd.read_csv(MASTER_FILE, dtype={"ags": str})
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Fehlende Feature-Spalten: {missing}")
    feat = df[list(FEATURES)]
    if feat.isna().any().any():
        n_bad = int(feat.isna().any(axis=1).sum())
        raise ValueError(f"{n_bad} Zeilen mit fehlenden Feature-Werten — bitte 03_merge prüfen")

    # z-Standardisierung: zwingend, da die Features sehr unterschiedliche Skalen
    # haben (% vs. EUR vs. EW/km²) und k-Means euklidische Distanzen nutzt.
    scaler = StandardScaler()
    matrix = scaler.fit_transform(feat.to_numpy(dtype=float))
    logger.info("%d Städte × %d Features standardisiert (z-Transformation)", *matrix.shape)
    return df, matrix


def diagnose_k(matrix: np.ndarray) -> tuple[dict[int, float], dict[int, float]]:
    """Berechne Inertia (Elbow) und Silhouettenkoeffizient je k in K_RANGE."""
    inertia: dict[int, float] = {}
    silhouette: dict[int, float] = {}
    for k in K_RANGE:
        km = KMeans(n_clusters=k, init="k-means++", n_init=10,
                    random_state=utils.RANDOM_STATE)
        labels = km.fit_predict(matrix)
        inertia[k] = float(km.inertia_)
        silhouette[k] = float(silhouette_score(matrix, labels))
        logger.info("k=%d | Inertia=%8.2f | Silhouette=%.3f", k, inertia[k], silhouette[k])
    return inertia, silhouette


def fit_kmeans(matrix: np.ndarray, k: int) -> np.ndarray:
    """Fitte finales k-Means++ und gib die Cluster-Labels zurück."""
    km = KMeans(n_clusters=k, init="k-means++", n_init=10,
                random_state=utils.RANDOM_STATE)
    labels = km.fit_predict(matrix)
    logger.info("Finales k-Means++ mit k=%d gefittet (Silhouette=%.3f)",
                k, silhouette_score(matrix, labels))
    return labels


def plot_diagnostics(inertia: dict[int, float], silhouette: dict[int, float],
                     chosen_k: int) -> None:
    """Zeichne Elbow- und Silhouettenkurve nebeneinander."""
    ks = list(inertia)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    ax1.plot(ks, [inertia[k] for k in ks], "o-", color="#1f77b4")
    ax1.axvline(chosen_k, ls="--", color="grey", alpha=0.7)
    ax1.set(xlabel="Clusterzahl k", ylabel="Inertia (within-cluster SSE)",
            title="Elbow-Methode")
    ax1.grid(alpha=0.3)

    ax2.plot(ks, [silhouette[k] for k in ks], "o-", color="#d62728")
    ax2.axvline(chosen_k, ls="--", color="grey", alpha=0.7)
    ax2.set(xlabel="Clusterzahl k", ylabel="Mittlerer Silhouettenkoeffizient",
            title="Silhouettenanalyse")
    ax2.grid(alpha=0.3)

    fig.suptitle(f"Bestimmung der Clusterzahl (gewählt: k={chosen_k})")
    fig.tight_layout()
    out = utils.FIGURES_DIR / "elbow_silhouette.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Diagnose-Plot geschrieben: %s", out)


def plot_clusters(matrix: np.ndarray, labels: np.ndarray, df: pd.DataFrame,
                  chosen_k: int) -> None:
    """Projiziere die Cluster per PCA auf 2D und beschrifte einige Städte."""
    pca = PCA(n_components=2, random_state=utils.RANDOM_STATE)
    coords = pca.fit_transform(matrix)
    var = pca.explained_variance_ratio_

    fig, ax = plt.subplots(figsize=(8, 6))
    cmap = plt.get_cmap("tab10")
    for cl in range(chosen_k):
        mask = labels == cl
        ax.scatter(coords[mask, 0], coords[mask, 1], s=60, alpha=0.8,
                   color=cmap(cl), label=f"Cluster {cl} (n={int(mask.sum())})")

    # Beschrifte je Cluster die größte Stadt zur Orientierung.
    for cl in range(chosen_k):
        idx = df.index[labels == cl]
        biggest = df.loc[idx, "einwohner"].idxmax()
        ax.annotate(df.loc[biggest, "stadt"], (coords[biggest, 0], coords[biggest, 1]),
                    fontsize=8, xytext=(4, 4), textcoords="offset points")

    ax.set(xlabel=f"PC1 ({var[0]*100:.0f}% Varianz)",
           ylabel=f"PC2 ({var[1]*100:.0f}% Varianz)",
           title=f"k-Means++-Cluster der {len(df)} Großstädte (k={chosen_k})")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = utils.FIGURES_DIR / "cluster_scatter.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Cluster-Streudiagramm geschrieben: %s", out)


def plot_feature_boxplots(df: pd.DataFrame, labels: np.ndarray, chosen_k: int) -> None:
    """Zeichne je Feature einen Boxplot, gruppiert nach Cluster (Originaleinheiten).

    Zeigt anschaulich, wie sich die Cluster auf jeder einzelnen Variable
    unterscheiden — komplementär zum PCA-Streudiagramm.
    """
    work = df.copy()
    work["cluster"] = labels
    cmap = plt.get_cmap("tab10")

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    for ax, (col, label) in zip(axes.flat, FEATURES.items()):
        data = [work.loc[work["cluster"] == cl, col].to_numpy() for cl in range(chosen_k)]
        bp = ax.boxplot(data, patch_artist=True, widths=0.6,
                        medianprops={"color": "black"})
        for cl, box in enumerate(bp["boxes"]):
            box.set(facecolor=cmap(cl), alpha=0.7)
        ax.set(title=label, xlabel="Cluster",
               xticklabels=[str(cl) for cl in range(chosen_k)])
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle(f"Feature-Verteilungen je Cluster (k={chosen_k})")
    fig.tight_layout()
    out = utils.FIGURES_DIR / "cluster_boxplots.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Feature-Boxplots geschrieben: %s", out)


def write_outputs(df: pd.DataFrame, labels: np.ndarray) -> None:
    """Schreibe Cluster-Zuordnung je Stadt und Cluster-Profil (Originaleinheiten)."""
    assigned = df.copy()
    assigned["cluster"] = labels
    cols = ["ags", "stadt", "cluster", *FEATURES, "ladepunkte_gesamt", "einwohner"]
    assigned = assigned[cols].sort_values(["cluster", "stadt"]).reset_index(drop=True)
    out_assign = utils.TABLES_DIR / "cluster_assignments.csv"
    assigned.to_csv(out_assign, **utils.CSV_KWARGS)
    logger.info("Cluster-Zuordnung geschrieben: %s", out_assign)

    # Profil: Mittelwerte je Feature + Clustergröße, in Originaleinheiten.
    profile = (
        assigned.groupby("cluster")[list(FEATURES)]
        .mean()
        .round(2)
    )
    profile.insert(0, "n_staedte", assigned.groupby("cluster").size())
    profile = profile.rename(columns=FEATURES)
    out_profile = utils.TABLES_DIR / "cluster_profile.csv"
    profile.to_csv(out_profile, encoding="utf-8-sig")
    logger.info("Cluster-Profil geschrieben: %s", out_profile)

    logger.info("Cluster-Profil (Mittelwerte je Cluster):\n%s", profile.to_string())


def main() -> int:
    """Einstiegspunkt: Daten laden, k bestimmen, clustern, Outputs schreiben."""
    parser = argparse.ArgumentParser(description="k-Means++-Clustering der Großstädte")
    parser.add_argument("--k", type=int, default=None,
                        help=f"Clusterzahl manuell vorgeben (Standard: k={DEFAULT_K})")
    args = parser.parse_args()

    utils.ensure_dirs()
    df, matrix = load_features()
    inertia, silhouette = diagnose_k(matrix)

    best_sil_k = max(silhouette, key=silhouette.get)
    logger.info("Silhouettenmaximum bei k=%d (%.3f)", best_sil_k, silhouette[best_sil_k])

    chosen_k = args.k if args.k is not None else DEFAULT_K
    source = "manuell vorgegeben" if args.k is not None else "Default (Interpretierbarkeit)"
    logger.info("Clusterzahl gewählt: k=%d (%s)", chosen_k, source)

    labels = fit_kmeans(matrix, chosen_k)
    plot_diagnostics(inertia, silhouette, chosen_k)
    plot_clusters(matrix, labels, df, chosen_k)
    plot_feature_boxplots(df, labels, chosen_k)
    write_outputs(df, labels)

    logger.info("Clustering abgeschlossen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

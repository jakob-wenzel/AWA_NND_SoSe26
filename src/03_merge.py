"""Schritt 3 — Datenzusammenführung & Feature Engineering.

Führt die bereinigten Einzeldatensätze zu einer Master-Tabelle
``data/master/master_cities.csv`` zusammen (eine Zeile je Zielstadt) und
berechnet die abgeleiteten Features für das Clustering.

Aufruf:
    python src/03_merge.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


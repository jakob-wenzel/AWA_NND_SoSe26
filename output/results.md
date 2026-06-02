## Done — `src/04_cluster.py` is complete and run

**Pipeline:** z-standardize 4 features → diagnose k=2..8 (elbow + silhouette) → fit k-means++ at **k=4** → write tables + figures.

**Outputs written:**

* [output/tables/cluster_assignments.csv](vscode-webview://0bchfnc793shi8o47ojg3d3re4hn1ktvu8dc21rdo7gh9bvru4q7/output/tables/cluster_assignments.csv) — 77 cities with cluster + raw feature values
* [output/tables/cluster_profile.csv](vscode-webview://0bchfnc793shi8o47ojg3d3re4hn1ktvu8dc21rdo7gh9bvru4q7/output/tables/cluster_profile.csv) — per-cluster means in original units (the table above)
* [output/figures/elbow_silhouette.png](vscode-webview://0bchfnc793shi8o47ojg3d3re4hn1ktvu8dc21rdo7gh9bvru4q7/output/figures/elbow_silhouette.png) — k-choice diagnostic
* [output/figures/cluster_scatter.png](vscode-webview://0bchfnc793shi8o47ojg3d3re4hn1ktvu8dc21rdo7gh9bvru4q7/output/figures/cluster_scatter.png) — 2D-PCA cluster plot

**Key design choices, all defensible in your methods section:**

* **StandardScaler** before k-means — mandatory here, since features range from `%` to `€` (k-means uses Euclidean distance).
* **k=4 by default** , set in `DEFAULT_K` with a comment explaining that silhouette peaks at k=2 but k=4 was chosen for an interpretable typology. The script logs *all* diagnostics every run, so the paper can show the elbow/silhouette curves and justify the trade-off. Override anytime with `python src/04_cluster.py --k 3`.
* `n_init=10`, `random_state=42` (your project's `RANDOM_STATE`) → fully reproducible.

**The four city types** map onto a clear EV-readiness narrative: structurally weaker cities (Ruhrgebiet/Ost), the broad average, affluent metros, and the two automotive-HQ outliers (Ingolstadt/Wolfsburg) — a nice concrete finding to anchor the discussion.

One caveat worth a sentence in the paper: at n=77 with k=4, Cluster 3 has only 2 cities. That's a real outlier group, not noise, but report it as such rather than as a "type" with broad generalizability.

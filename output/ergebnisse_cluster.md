# Ergebnisse — Clusteranalyse (Entwurf)

> Entwurf für den Ergebnisteil des Papers. Zahlen aus
> `output/tables/cluster_profile.csv` (Stand: aktueller Lauf, k=4).
> Cluster-Nummerierung ist beliebig (k-Means vergibt keine Reihenfolge) — bei
> erneutem Lauf ggf. anpassen.

## Bestimmung der Clusterzahl

Zur Festlegung der Clusterzahl wurden für $k = 2, \dots, 8$ jeweils die
Within-Cluster-Sum-of-Squares (Inertia, Elbow-Methode) sowie der mittlere
Silhouettenkoeffizient berechnet (Abb. *elbow_silhouette*). Der
Silhouettenkoeffizient erreicht sein Maximum bei $k = 2$ (0{,}44), was
ausschließlich die wohlhabende, EV-affine Spitzengruppe vom übrigen Feld
trennt. Da diese Zweiteilung für eine differenzierte Stadttypologie zu grob
ist und die Inertia-Kurve bei $k = 4$ einen erkennbaren Knick aufweist, wurde
$k = 4$ als bester Kompromiss zwischen Trennschärfe und inhaltlicher
Interpretierbarkeit gewählt.

## Beschreibung der vier Cluster

Die k-Means++-Clusteranalyse (standardisierte Merkmale, $n = 77$ Großstädte)
ergibt vier deutlich unterscheidbare Stadttypen. Tabelle *cluster_profile*
fasst die Mittelwerte der vier Merkmale je Cluster zusammen; Abbildung
*cluster_boxplots* zeigt die zugehörigen Verteilungen.

**Cluster 0 — Strukturschwächere Städte (n = 29).** Dieser Cluster vereint
Städte mit dem niedrigsten EV-Anteil (Ø 5{,}6 %), der geringsten
Ladepunktdichte (Ø 2{,}0 je 1.000 EW) und dem niedrigsten Primäreinkommen
(Ø 27.896 €). Er umfasst vorwiegend altindustrielle Standorte des Ruhrgebiets
(Duisburg, Gelsenkirchen, Oberhausen, Herne) sowie ostdeutsche Großstädte
(Chemnitz, Halle, Magdeburg, Rostock). Die niedrige Kaufkraft geht mit einer
unterdurchschnittlich ausgebauten Ladeinfrastruktur einher.

**Cluster 1 — Wohlhabende Metropolen (n = 11).** Hier finden sich die
einkommensstärksten Städte (Ø 43.830 €) mit zugleich hohem EV-Anteil
(Ø 10{,}2 %), guter Ladeinfrastruktur (Ø 4{,}6 je 1.000 EW) und der höchsten
Bevölkerungsdichte (Ø 2.291 EW/km²). Typische Vertreter sind München,
Frankfurt am Main, Stuttgart, Düsseldorf und Heidelberg. Das Muster stützt die
Hypothese eines positiven Zusammenhangs zwischen Kaufkraft und
Elektromobilitäts-Adoption.

**Cluster 2 — Durchschnittliche Großstädte (n = 35).** Der größte Cluster
bildet das breite Mittelfeld ab: durchschnittlicher EV-Anteil (Ø 7{,}8 %),
mittleres Einkommen (Ø 34.351 €) und mittlere Ladepunktdichte (Ø 2{,}6 je
1.000 EW). Er enthält u. a. Berlin, Hamburg, Köln und Nürnberg — also auch die
größten Städte, deren Kennzahlen nahe am Gesamtmittel liegen.

**Cluster 3 — Automobil-Hochburgen (n = 2).** Ingolstadt und Wolfsburg bilden
einen klaren Ausreißer-Cluster mit extrem hohem EV-Anteil (Ø 17{,}9 %) und
einer mehr als dreifach über dem Durchschnitt liegenden Ladepunktdichte
(Ø 9{,}3 je 1.000 EW), bei gleichzeitig der **niedrigsten**
Bevölkerungsdichte (Ø 846 EW/km²). Beide Städte sind Sitz großer
Automobilhersteller (Audi bzw. Volkswagen); der außergewöhnlich hohe
EV-Anteil dürfte maßgeblich auf Werksverkehr und Mitarbeiterfahrzeuge
zurückzuführen sein.

## Einordnung

Die Hauptkomponentenanalyse (Abb. *cluster_scatter*) bestätigt das Bild: Die
erste Hauptkomponente (55 % der Varianz) bildet im Wesentlichen einen
gemeinsamen „Wohlstands- und EV-Bereitschafts"-Gradienten ab, entlang dessen
sich die Cluster 0, 2 und 1 staffeln, während Cluster 3 als deutlich
abgesetzter Sonderfall erscheint.

Methodisch ist einschränkend anzumerken, dass Cluster 3 mit nur zwei Städten
sehr klein ist; er beschreibt einen realen Sonderfall, erlaubt aber keine
breite Verallgemeinerung. Der niedrige Silhouettenkoeffizient bei $k = 4$
(0{,}24) deutet zudem darauf hin, dass die Übergänge zwischen den drei großen
Clustern fließend sind — die Stadttypen sind als Schwerpunkte eines Kontinuums
zu verstehen, nicht als scharf getrennte Gruppen.

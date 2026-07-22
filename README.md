# Scope 3.1 Carbon Data Catalog

Ein semantischer Metadaten-Prototyp für Carbon Data Governance — entwickelt
als Portfolioprojekt im Datenmanagement-Schwerpunkt.

Das Notebook baut einen Datenkatalog für Scope-3.1-Emissionsdaten
(Purchased Goods & Services) auf, deckt strukturierte Metadatenlücken
regelbasiert auf und macht den Abdeckungsgrad der regulatorischen
Anforderungen sichtbar und interaktiv erkundbar.

---

## 1. Warum Scope 3.1 ein Datenproblem ist

Seit der EU-**CSRD** müssen Unternehmen ihre Treibhausgasemissionen
vollständig offenlegen — inklusive der vorgelagerten Lieferkette.
**Scope 3, Kategorie 1** (eingekaufte Waren und Dienstleistungen) macht in
industriellen Unternehmen oft über 70 % des gesamten CO₂-Fußabdrucks aus.

In der Praxis scheitert belastbares Reporting dabei selten an der
Berechnungsformel, sondern an vorgelagerten Fragen: Welche Daten werden
gebraucht? Wo liegen sie? Wer verantwortet sie? Was davon ist belastbar,
was fehlt noch? Ohne eine strukturierte Antwort auf diese Fragen bleibt
jede Emissionsbilanz auf unsicherem Fundament.

**Kernthese des Projekts:** Nicht fehlende Technologie, sondern fehlende
*Datensouveränität* ist das zentrale Hindernis für belastbares
Scope-3.1-Reporting.

## 2. Fallbeispiel: FloorTec Group (synthetisch)

Als Anschauungsfall dient ein fiktiver, vertikal integrierter
Bodenbelagshersteller mit typisch fragmentierter Systemlandschaft:

| Bereich | Standorte | Konsolidierung |
|---|---|---|
| Rohstoffproduktion | Malaysia, China, Australien | nicht angeschlossen |
| Verwaltung/Einkauf | Deutschland (zentral) | vollständig (SAP BW) |
| Absatzmärkte | Frankreich, Deutschland, USA | Frankreich/DE angeschlossen, USA nicht |

Dazu kommt "Shadow Data" — informelle Quellen wie Kreditkartenabrechnungen
oder manuelle Excel-Exporte ohne Beleg — sowie eine GHG-Datenqualitäts-
hierarchie (Primärdaten → mengenbasiert → ausgabenbasiert), die in der
Praxis an heterogenen Einheiten, unlesbaren Materialbeschreibungen und
fragmentierten Buchhaltungssystemen scheitert. Diese Konstellation ist
bewusst so gewählt, dass alle sechs Gap-Regeln (siehe unten) mit
plausiblen, nicht-trivialen Fällen greifen.

## 3. Datenmodell

Der Katalog verbindet regulatorische Anforderungen über eine semantische
Beziehungskette mit der technischen Realität:

```
Requirement → Business Term → Technical Field → Dataset → Source System
```

Eine Anforderung gilt erst als vollständig abgedeckt, wenn diese Kette
lückenlos dokumentiert ist — inklusive Data Owner und Datenqualität.

**6 Tabellen** (SQLite, `catalog.db`, wird beim ersten Start automatisch
aus `data/seed_data.py` befüllt):

| Tabelle | Bedeutung |
|---|---|
| `source_systems` | Herkunftssystem, Land, Konsolidierungsstatus |
| `datasets` | Logische Dateneinheit, Data Contact, Belegverfügbarkeit |
| `technical_fields` | Konkretes Feld, Einheit, Feld-Owner |
| `business_terms` | Fachbegriff mit Tier-Einstufung |
| `requirements` | Anforderung aus ESRS E1 / GHG Protocol |
| `metadata_gaps` | Erkannte Lücke mit Typ, Schweregrad, empfohlener Aktion |

Seed-Daten (Version 2): 9 Quellsysteme, 10 Datasets, 18 technische Felder,
10 Fachbegriffe, 11 Anforderungen.

## 4. Gap Detection Engine

Die Klasse `GapDetector` ([src/gap_detector.py](src/gap_detector.py)) prüft
den Katalog regelbasiert auf sechs Arten von Metadatenlücken:

| # | Regel | Prüft auf |
|---|---|---|
| 1 | `check_fehlender_field_owner` | Technische Felder ohne verantwortliche Person |
| 2 | `check_systemanschluss` | Quellsysteme ohne Anbindung an die Konsolidierung |
| 3 | `check_unleserliche_materialbeschreibung` | Unlesbare/fehlende Materialbeschreibungen |
| 4 | `check_fehlendes_field_mapping` | Anforderungen ohne Verknüpfung zu einem technischen Feld |
| 5 | `check_manuelle_daten_ohne_beleg` | Manuelle Dateneingabe ohne Belegnachweis |
| 6 | `check_automatisierungspotenzial` | Automatisierungspotenzial/Kostenschätzung je System |

Der Schweregrad wird nicht pauschal vergeben, sondern kontextabhängig
berechnet — z. B. berücksichtigt Regel 1 sowohl die Pflichtfeld-Eigenschaft
als auch die Tier-Einstufung der verknüpften Anforderung, und Regel 5
skaliert den Schweregrad nach Anzahl manueller Einträge.
`run_all()` führt alle Regeln in einem Durchlauf aus und befüllt
`metadata_gaps`; `coverage_score()` berechnet daraus den Anteil
vollständig abgedeckter Anforderungen.

## 5. Interaktive Abfrage & Visualisierung

`QueryEngine` ([src/query_engine.py](src/query_engine.py)) stellt Gaps und
Anforderungen filterbar bereit (nach Schweregrad, Typ, Entität, Tier) und
liefert die Datengrundlage für zwei Auswertungen im Notebook:

- **ipywidgets**-Browser zum Filtern von Gaps und Anforderungen direkt im Notebook
- **Plotly**-Visualisierungen: Coverage-Score als Donut-Chart, Gaps nach
  Typ/Schweregrad als Balkendiagramm

## 6. Setup & Ausführung

```bash
git clone https://github.com/EmmaWittwer/scope31_catalog.git
cd scope31_catalog
pip install -r requirements.txt
jupyter notebook scope31_catalog.ipynb
```

Danach im Notebook: **Kernel → Restart & Run All**. Die Datenbank
(`catalog.db`, nicht Teil des Repos) wird beim ersten Durchlauf automatisch
angelegt und aus `data/seed_data.py` befüllt.

## 7. Projektstruktur

```
scope31_catalog/
├── scope31_catalog.ipynb   Haupt-Notebook (Kontext, Schema, Gap Detection, Abfrage, Visualisierung)
├── src/
│   ├── gap_detector.py     GapDetector — 6 Lückenregeln, run_all(), coverage_score()
│   └── query_engine.py     QueryEngine — Filterung, Coverage- und Gap-Auswertung
├── data/
│   └── seed_data.py        FloorTec-Seed-Daten (Version 2)
├── 01_kontext.md           Ausführlicher fachlicher Hintergrund
└── requirements.txt
```

## 8. Status & Ausblick

Alle sechs Gap-Regeln, die Coverage-Berechnung sowie die interaktive
Abfrage und Visualisierung sind implementiert und lauffähig. Offen sind
u. a. eine `CatalogManager`-Klasse für CRUD-Operationen auf dem Katalog
sowie eine ausformulierte Fazit/Ausblick-Sektion im Notebook.

Konzeptioneller Ausblick: Die aktuelle Gap Detection ist **regelbasiert**
— jede Regel prüft einen fest definierten, im Voraus bekannten Fall. Eine
denkbare Erweiterung wäre ein **agentenbasierter** Ansatz, bei dem ein
System nicht nur vordefinierte Regeln abarbeitet, sondern eigenständig neue
Gap-Typen erkennt oder Kurationsvorschläge macht. Das ist im aktuellen
Prototyp bewusst nicht umgesetzt — der Unterschied zwischen regelbasierter
und agentenbasierter Verarbeitung ist selbst ein zentraler Lernpunkt dieses
Projekts.

## 9. Methodischer Rahmen

Das Projekt folgt dem Paradigma des **Design Science Research**: Problem-
identifikation (fragmentierte Scope-3.1-Datenlage) → Artefakt-Entwicklung
(Katalog mit Gap Detection und Abfragemöglichkeit) → Evaluation (Coverage
vor/nach Curation). Weiterführender fachlicher Kontext in
[01_kontext.md](01_kontext.md).

---

## Lizenz

MIT — siehe [LICENSE](LICENSE).

*Portfolioprojekt · Datenmanagement-Schwerpunkt*

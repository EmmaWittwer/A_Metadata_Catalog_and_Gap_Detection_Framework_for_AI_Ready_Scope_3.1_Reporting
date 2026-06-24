# Scope 3.1 Carbon Data Catalog
## Ein semantischer Metadaten-Prototyp für Carbon Data Governance

**Portfolioprojekt | Datenmanagement | Juni 2026**

---

Dieses Notebook dokumentiert Entwicklung und Funktionsweise eines prototypischen
Carbon Data Catalogs für Scope-3.1-Emissionsdaten. Es richtet sich an
ESG-Verantwortliche, Data Stewards und alle, die verstehen wollen, warum
Scope-3.1-Reporting in der Praxis scheitert – und wie ein strukturierter
Datenkatalog das ändert.

---

## 1. Ausgangslage: Warum Scope 3.1 ein Datenproblem ist

Seit Inkrafttreten der **Corporate Sustainability Reporting Directive (CSRD)**
der EU sind Unternehmen ab definierten Schwellenwerten verpflichtet,
Treibhausgasemissionen vollständig und nachvollziehbar offenzulegen –
einschließlich der vorgelagerten Lieferkette.

**Scope 3, Kategorie 1 (Purchased Goods & Services)** ist dabei besonders
kritisch: In industriellen Unternehmen entfallen häufig über 70 % des
gesamten CO₂-Fußabdrucks auf eingekaufte Waren und Dienstleistungen.

### Das eigentliche Problem ist kein CO₂-Problem – es ist ein Datenproblem.

Unternehmen scheitern in der Praxis nicht an der Berechnungsformel,
sondern an grundlegenderen Fragen:

| Frage | Typische Realität |
|---|---|
| Welche Daten brauchen wir? | Unklar – keine strukturierte Anforderungsliste |
| Wo liegen die Daten? | Verteilt über SAP MM, ERP, Procurement-Systeme |
| Wer verantwortet sie? | Personenabhängig, nicht dokumentiert |
| Was ist wirklich belastbar? | Unbekannt – keine Qualitätsregeln definiert |
| Was fehlt noch? | Nicht sichtbar – keine Gap-Übersicht |

> **Kernthese:** Nicht fehlende Technologie, sondern fehlende
> *Datensouveränität* ist das zentrale Hindernis für belastbares
> Scope-3.1-Reporting.

---

## 2. Projektidee: Der Carbon Data Catalog

Dieser Prototyp beantwortet eine konkrete Forschungsfrage:

> *Wie kann ein semantisch strukturierter Datenkatalog eingesetzt werden,
> um die für Scope 3.1 benötigten Daten systematisch zu identifizieren,
> Metadatenlücken sichtbar zu machen und deren kuratierte Schließung
> zu unterstützen?*

### Was dieser Prototyp leistet

- **Modellierung** von Scope-3.1-Anforderungen als strukturierte Entitäten
- **Verknüpfung** von fachlichen Begriffen, technischen Feldern, Datensätzen
  und Quellsystemen
- **Automatische Lückenerkennung** durch regelbasierte Gap Detection
- **Interaktive Abfrage und Verfeinerung** des Katalogs direkt im Notebook

### Was dieser Prototyp bewusst nicht leistet

- Keine CO₂-Berechnung oder Emissionsbilanz
- Keine Anbindung an produktive Unternehmenssysteme
- Keine Skalierbarkeits- oder Performanzmessung
- Kein vollständiger Scope-3-Abdeckungsnachweis

> Die Stärke liegt in der **Governance-Logik**, nicht in der Datenmenge.

---

## 3. Das Datenmodell: Semantische Beziehungskette

Der Katalog basiert auf einer semantischen Beziehungslogik, die regulatorische
Anforderungen mit technischer Realität verbindet:

```
Requirement → Business Term → Technical Field → Dataset → Source System
                                                    ↓
                                               Data Owner
                                                    ↓
                                            Metadata Gap
```

### Entitäten im Überblick

| Entität | Bedeutung | Beispiel |
|---|---|---|
| `Requirement` | Informationsbedarf aus ESRS E1 / GHG Protocol | "Einkaufswert pro Lieferant" |
| `Business Term` | Fachlicher Begriff im Unternehmenskontext | "Lieferant", "Materialgruppe" |
| `Technical Field` | Konkretes Datenbankfeld im Quellsystem | `LIFNR` in SAP MM |
| `Dataset` | Logische Dateneinheit (Tabelle, View, Report) | `MM60_PURCHASE_ORDERS` |
| `Source System` | Herkunftssystem der Daten | SAP MM, Oracle ERP |
| `Data Owner` | Verantwortliche Person oder Rolle | "Procurement Data Lead" |
| `Metadata Gap` | Explizit modellierte Lücke mit Typ und Priorität | "Kein Owner für Dataset X" |

**Leitprinzip:** Eine Anforderung gilt erst als vollständig abgedeckt, wenn
die gesamte Kette lückenlos dokumentiert ist – von der regulatorischen
Anforderung bis zum verantwortlichen Owner im Quellsystem.

---

## 4. Methodischer Rahmen

Das Projekt folgt dem Paradigma des **Design Science Research (DSR)**:
Ziel ist nicht die Beschreibung eines Problems, sondern die Entwicklung
und Evaluation eines konkreten IT-Artefakts, das das Problem löst.

**Drei DSR-Aktivitäten in diesem Prototyp:**

1. **Problemidentifikation** – Das strukturelle Datenproblem bei Scope-3.1-Bilanzierung
2. **Artefakt-Entwicklung** – Der Datenkatalog mit Gap Detection und Abfragemöglichkeit
3. **Evaluation** – Messung des Abdeckungsgrads vor und nach einer Curation-Session

### Erfolgskriterien dieses Prototyps

| Kriterium | Messgröße |
|---|---|
| Vollständigkeit | Anteil Anforderungen mit vollständiger Beziehungskette |
| Lückentransparenz | Anzahl und Typ erkannter Metadatenlücken |
| Curation-Wirkung | Abdeckungsgrad vor vs. nach Nutzer-Interaktion |
| Erklärbarkeit | Verständlichkeit ohne technisches Vorwissen |

---

## 5. Aufbau des Notebooks

| Abschnitt | Inhalt |
|---|---|
| **1–4** | Kontext, Problemstellung, Modell, Methodik *(diese Zellen)* |
| **5** | Datenbankaufbau und Schema-Definition |
| **6** | Seed-Daten: 8 Scope-3.1-Anforderungen befüllt |
| **7** | Gap Detection Engine: 5 Lückenregeln |
| **8** | Interaktive Abfrage und Katalogrefinement |
| **9** | Coverage-Visualisierung und Auswertung |
| **10** | Fazit, Limitationen und Ausblick |

> **Lesehinweis:** Jede Code-Zelle ist mit einer Erklärung versehen.
> Das Notebook ist so strukturiert, dass es ohne Python-Kenntnisse
> inhaltlich nachvollziehbar bleibt.

---

*Scope 3.1 Carbon Data Catalog · Portfolioprojekt · Juni 2026 · Vertraulich*

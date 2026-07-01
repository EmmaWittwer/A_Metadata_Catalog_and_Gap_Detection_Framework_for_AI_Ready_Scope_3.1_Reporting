# ================================================================
# gap_detector.py — Gap Detection Engine
# Scope 3.1 Carbon Data Catalog · FloorTec Group
# ================================================================

import sqlite3
import pandas as pd
from datetime import datetime

class GapDetector:
    """
    Erkennt Metadatenlücken im Carbon Data Catalog automatisch.
    Jede Methode prüft eine Regelklasse und schreibt Lücken
    in die metadata_gaps Tabelle.
    """

    def __init__(self, db_path="catalog.db"):
        """
        Datenbankverbindung herstellen.
        db_path: Pfad zur SQLite Datenbank
        """
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        print(f"✓ GapDetector verbunden mit {db_path}")

    def _gap_eintragen(self, gap_type, severity, affected_entity,
                       affected_id, description, recommended_action,
                       gap_subtype=None):
        """
        Interne Hilfsmethode — schreibt einen Gap-Eintrag
        in die metadata_gaps Tabelle.
        Wird von jeder Regel aufgerufen.
        gap_subtype ist optional — Regeln ohne Subtyp übergeben nichts.
        """
        self.cursor.execute("""
            INSERT INTO metadata_gaps
            (gap_type, gap_subtype, severity, affected_entity, affected_id,
             description, recommended_action, status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            gap_type,
            gap_subtype,
            severity,
            affected_entity,
            affected_id,
            description,
            recommended_action,
            "offen",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    def gaps_leeren(self):
        """
        Alle bestehenden Gaps löschen — vor jedem neuen Durchlauf
        aufrufen damit keine doppelten Einträge entstehen.
        """
        self.cursor.execute("DELETE FROM metadata_gaps")
        self.conn.commit()
        print("✓ Bestehende Gaps geleert")

    def check_fehlender_field_owner(self):
        """
        Regel 1: Technische Felder ohne Field Owner.
        Severity: high wenn Pflichtfeld (is_nullable=0)
                  medium wenn optionales Feld (is_nullable=1)
        """
        query = """
            SELECT
                tf.id,
                tf.field_name,
                tf.field_description,
                tf.is_nullable,
                d.name      AS dataset_name,
                ss.subsidiary
            FROM technical_fields tf
            JOIN datasets d         ON tf.dataset_id = d.id
            JOIN source_systems ss  ON d.source_system_id = ss.id
            WHERE tf.field_owner IS NULL
        """
        felder = pd.read_sql_query(query, self.conn)

        for _, feld in felder.iterrows():
            severity = "high" if feld["is_nullable"] == 0 else "medium"

            self._gap_eintragen(
                gap_type         = "fehlender_field_owner",
                severity         = severity,
                affected_entity  = "technical_fields",
                affected_id      = feld["id"],
                description      = (
                    f"Feld '{feld['field_name']}' in Dataset "
                    f"'{feld['dataset_name']}' ({feld['subsidiary']}) "
                    f"hat keinen dokumentierten Field Owner."
                ),
                recommended_action = (
                    "Verantwortliche Person oder Rolle für dieses "
                    "Datenfeld benennen und im Katalog eintragen."
                )
            )

        self.conn.commit()
        print(f"✓ Regel 1 ausgeführt — {len(felder)} Gaps gefunden")
        return felder    
    
    def check_systemanschluss(self):
        """
        Regel 2: Quellsysteme ohne Konsolidierungsanbindung.
        Severity: high fix — fehlender Anschluss ist unabhängig
        von der Datenmenge ein strukturelles Governance-Risiko.
        """
        query = """
            SELECT
                id,
                name,
                system_type,
                subsidiary,
                country,
                consolidation_status
            FROM source_systems
            WHERE consolidation_status = 'nicht_angeschlossen'
        """
        systeme = pd.read_sql_query(query, self.conn)

        for _, system in systeme.iterrows():
            self._gap_eintragen(
                gap_type          = "kein_systemanschluss",
                severity          = "high",
                affected_entity   = "source_systems",
                affected_id       = system["id"],
                description       = (
                    f"{system['subsidiary']} ({system['name']}, "
                    f"{system['country']}) ist nicht an das zentrale "
                    f"Konsolidierungssystem angeschlossen. Daten müssen "
                    f"manuell eingesammelt werden."
                ),
                recommended_action = (
                    "Systemanbindung an SAP BW EU evaluieren oder "
                    "manuellen Übertragungsprozess mit Belegpflicht "
                    "und definiertem Ansprechpartner dokumentieren."
                )
            )

        self.conn.commit()
        print(f"✓ Regel 2 ausgeführt — {len(systeme)} Gaps gefunden")
        return systeme

    def check_unleserliche_materialbeschreibung(self):
        """
        Regel 3: Technische Felder mit unleserlicher oder fehlender
        Materialbeschreibung. Blockiert massenbasierte Emissionsberechnung.
        Severity: high fix für 'unlesbar' und 'fehlend'.
        'teilweise_lesbar' wird bewusst nicht erfasst — eigene Regel.
        """
        query = """
            SELECT
                tf.id,
                tf.field_name,
                tf.field_description,
                tf.material_description_quality,
                d.name      AS dataset_name,
                ss.subsidiary,
                ss.country
            FROM technical_fields tf
            JOIN datasets d         ON tf.dataset_id = d.id
            JOIN source_systems ss  ON d.source_system_id = ss.id
            WHERE tf.material_description_quality IN ('unlesbar', 'fehlend')
        """
        felder = pd.read_sql_query(query, self.conn)

        for _, feld in felder.iterrows():
            ursache = (
                "nicht dokumentiert" if feld["material_description_quality"] == "fehlend"
                else "nicht interpretierbar (lokale Sprache oder kryptischer Code)"
            )
            self._gap_eintragen(
                gap_type         = "unleserliche_materialbeschreibung",
                gap_subtype      = feld["material_description_quality"],
                severity         = "high",
                affected_entity  = "technical_fields",
                affected_id      = feld["id"],
                description      = (
                    f"Feld '{feld['field_name']}' in Dataset '{feld['dataset_name']}' "
                    f"({feld['subsidiary']}, {feld['country']}): "
                    f"Materialbeschreibung ist {ursache}. "
                    f"Massenbasierte Emissionsberechnung blockiert."
                ),
                recommended_action = (
                    "Materialbeschreibung ins Deutsche oder Englische übersetzen "
                    "bzw. Mapping-Tabelle (Lokalcode → Materialgruppe) erstellen "
                    "und im Katalog verlinken."
                )
            )

        self.conn.commit()
        print(f"✓ Regel 3 ausgeführt — {len(felder)} Gaps gefunden")
        return felder

    def check_fehlendes_field_mapping(self):
        """
        Regel 4: Anforderungen ohne Verknüpfung zu einem technischen Feld.
        Bricht die Beziehungskette Requirement → Technical Field.
        Severity: dynamisch nach tier_level (GHG Protocol Hierarchie).
        """
        query = """
            SELECT
                r.id,
                r.name,
                r.source,
                r.tier_level,
                r.priority,
                r.coverage_status,
                bt.name AS business_term_name
            FROM requirements r
            LEFT JOIN business_terms bt ON r.business_term_id = bt.id
            WHERE r.technical_field_id IS NULL
        """
        anforderungen = pd.read_sql_query(query, self.conn)

        severity_map = {1: "high", 2: "medium", 3: "low"}

        for _, req in anforderungen.iterrows():
            severity = severity_map.get(int(req["tier_level"]), "medium")
            self._gap_eintragen(
                gap_type         = "fehlendes_field_mapping",
                severity         = severity,
                affected_entity  = "requirements",
                affected_id      = req["id"],
                description      = (
                    f"Anforderung '{req['name']}' ({req['source']}, "
                    f"Tier {int(req['tier_level'])}) ist keinem technischen "
                    f"Feld zugeordnet. Beziehungskette zum Datenpunkt fehlt."
                ),
                recommended_action = (
                    "Passendes technisches Feld im Katalog identifizieren "
                    "und technical_field_id in requirements eintragen."
                )
            )

        self.conn.commit()
        print(f"✓ Regel 4 ausgeführt — {len(anforderungen)} Gaps gefunden")
        return anforderungen

    def check_manuelle_daten_ohne_beleg(self):
        """
        Regel 5: Datasets mit manueller Dateneingabe ohne Belegnachweis.
        Severity: dynamisch nach manual_entry_count.
        'unbekannt' wird wie 'False' behandelt — auditrechtlich gleich kritisch.
        """
        query = """
            SELECT
                d.id,
                d.name,
                d.data_entry_type,
                d.evidence_available,
                d.manual_entry_count,
                d.data_contact,
                d.data_contact_role,
                ss.subsidiary,
                ss.country
            FROM datasets d
            JOIN source_systems ss ON d.source_system_id = ss.id
            WHERE d.data_entry_type IN ('manuell', 'semi-manuell')
            AND   d.evidence_available IN ('False', 'unbekannt')
            AND   d.manual_entry_count > 0
        """
        datasets = pd.read_sql_query(query, self.conn)

        for _, ds in datasets.iterrows():
            count = int(ds["manual_entry_count"])
            if count <= 10:
                severity = "low"
            elif count <= 50:
                severity = "medium"
            else:
                severity = "high"

            self._gap_eintragen(
                gap_type         = "manuelle_daten_ohne_beleg",
                gap_subtype      = ds["evidence_available"],
                severity         = severity,
                affected_entity  = "datasets",
                affected_id      = ds["id"],
                description      = (
                    f"Dataset '{ds['name']}' ({ds['subsidiary']}, {ds['country']}) "
                    f"hat {count} manuelle Einträge "
                    f"({'kein Beleg vorhanden' if ds['evidence_available'] == 'False' else 'Belegstatus unbekannt'}). "
                    f"Eintragstyp: {ds['data_entry_type']}."
                ),
                recommended_action = (
                    "Belegnachweise (Rechnung, Lieferschein o.ä.) sammeln "
                    "und evidence_type im Katalog dokumentieren. "
                    "Bei Shadow-Daten: formalen Erfassungsprozess etablieren."
                )
            )

        self.conn.commit()
        print(f"✓ Regel 5 ausgeführt — {len(datasets)} Gaps gefunden")
        return datasets

    def check_automatisierungspotenzial(self):
        """
        Regel 6: Datasets mit manuellem Aufwand und Automatisierungspotenzial.
        Schätzt Kosten aus manual_entry_count × Zeitaufwand × Stundensatz.
        Severity: dynamisch nach geschätzten Kosten (<500 low, 500-1500 medium, >1500 high).
        """
        ZEITAUFWAND = {"manuell": 0.5, "semi-manuell": 0.25}
        STUNDENSATZ = {
            "Controlling": 85,
            "GL-Assistenz": 55,
            "IT": 90,
            "unbekannt": 70,
        }

        query = """
            SELECT
                d.id,
                d.name,
                d.data_entry_type,
                d.data_contact_role,
                d.manual_entry_count,
                ss.subsidiary,
                ss.country
            FROM datasets d
            JOIN source_systems ss ON d.source_system_id = ss.id
            WHERE d.data_entry_type IN ('manuell', 'semi-manuell')
            AND   d.manual_entry_count > 0
        """
        datasets = pd.read_sql_query(query, self.conn)

        for _, ds in datasets.iterrows():
            rolle = ds["data_contact_role"] or "unbekannt"
            stundensatz = STUNDENSATZ.get(rolle, STUNDENSATZ["unbekannt"])
            zeitaufwand = ZEITAUFWAND[ds["data_entry_type"]]
            kosten = round(int(ds["manual_entry_count"]) * zeitaufwand * stundensatz, 2)

            if kosten < 500:
                severity = "low"
            elif kosten <= 1500:
                severity = "medium"
            else:
                severity = "high"

            self._gap_eintragen(
                gap_type         = "automatisierungspotenzial",
                gap_subtype      = ds["data_entry_type"],
                severity         = severity,
                affected_entity  = "datasets",
                affected_id      = ds["id"],
                description      = (
                    f"Dataset '{ds['name']}' ({ds['subsidiary']}, {ds['country']}): "
                    f"{int(ds['manual_entry_count'])} manuelle Einträge × "
                    f"{zeitaufwand}h × {stundensatz}€/h = "
                    f"ca. {kosten:.0f}€ geschätzter manueller Aufwand. "
                    f"Eintragstyp: {ds['data_entry_type']}."
                ),
                recommended_action = (
                    "Automatisierung oder API-Anbindung evaluieren. "
                    "Kosten-Nutzen-Analyse auf Basis geschätztem Aufwand durchführen."
                )
            )

        self.conn.commit()
        print(f"✓ Regel 6 ausgeführt — {len(datasets)} Gaps gefunden")
        return datasets

    def coverage_score(self):
        """
        Berechnet den Coverage-Score dynamisch aus der Beziehungskette.
        vollständig: business_term_id + technical_field_id + field_owner gesetzt.
        partiell:    mindestens eines davon gesetzt, aber nicht alle.
        offen:       weder business_term_id noch technical_field_id gesetzt.
        """
        query = """
            SELECT
                r.id,
                r.name,
                r.tier_level,
                r.priority,
                r.source,
                CASE
                    WHEN r.business_term_id  IS NOT NULL
                     AND r.technical_field_id IS NOT NULL
                     AND tf.field_owner        IS NOT NULL
                    THEN 'vollständig'
                    WHEN r.business_term_id IS NULL
                     AND r.technical_field_id IS NULL
                    THEN 'offen'
                    ELSE 'partiell'
                END AS coverage_dynamisch
            FROM requirements r
            LEFT JOIN technical_fields tf ON r.technical_field_id = tf.id
        """
        df = pd.read_sql_query(query, self.conn)

        gesamt       = len(df)
        vollstaendig = (df["coverage_dynamisch"] == "vollständig").sum()
        partiell     = (df["coverage_dynamisch"] == "partiell").sum()
        offen        = (df["coverage_dynamisch"] == "offen").sum()
        score        = round(vollstaendig / gesamt * 100, 1)

        print(f"\n{'='*45}")
        print(f"  COVERAGE SCORE: {score}%")
        print(f"{'='*45}")
        print(f"  vollständig : {vollstaendig:2d} / {gesamt}  ({vollstaendig/gesamt*100:.1f}%)")
        print(f"  partiell    : {partiell:2d} / {gesamt}  ({partiell/gesamt*100:.1f}%)")
        print(f"  offen       : {offen:2d} / {gesamt}  ({offen/gesamt*100:.1f}%)")
        print(f"{'='*45}\n")

        print("Details nach Tier:")
        tier_summary = (
            df.groupby(["tier_level", "coverage_dynamisch"])
            .size()
            .unstack(fill_value=0)
        )
        print(tier_summary.to_string())
        print()

        return df

    def run_all(self):
        """
        Führt alle Regeln in einem Durchlauf aus.
        Leert metadata_gaps einmalig am Anfang — nie zwischendurch.
        """
        self.gaps_leeren()
        self.check_fehlender_field_owner()
        self.check_systemanschluss()
        self.check_unleserliche_materialbeschreibung()
        self.check_fehlendes_field_mapping()
        self.check_manuelle_daten_ohne_beleg()
        self.check_automatisierungspotenzial()

        gesamt = pd.read_sql_query(
            "SELECT COUNT(*) AS anzahl FROM metadata_gaps", self.conn
        )["anzahl"][0]

        print(f"\n✓ Gap-Scan abgeschlossen — {gesamt} Gaps total in metadata_gaps")
    
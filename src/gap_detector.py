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

    def run_all(self):
        """
        Führt alle Regeln in einem Durchlauf aus.
        Leert metadata_gaps einmalig am Anfang — nie zwischendurch.
        """
        self.gaps_leeren()
        self.check_fehlender_field_owner()
        self.check_systemanschluss()
        self.check_unleserliche_materialbeschreibung()

        gesamt = pd.read_sql_query(
            "SELECT COUNT(*) AS anzahl FROM metadata_gaps", self.conn
        )["anzahl"][0]

        print(f"\n✓ Gap-Scan abgeschlossen — {gesamt} Gaps total in metadata_gaps")
    
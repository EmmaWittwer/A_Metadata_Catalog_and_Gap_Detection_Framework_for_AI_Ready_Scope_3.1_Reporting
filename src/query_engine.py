import sqlite3
import pandas as pd


class QueryEngine:
    """
    Abfrage- und Filterschicht für den Carbon Data Catalog.
    Trennt SQL-Logik von der Notebook-Darstellung.
    """

    def __init__(self, db_path="catalog.db"):
        self.conn = sqlite3.connect(db_path)
        print(f"✓ QueryEngine verbunden mit {db_path}")

    def gaps_filtern(self, severity=None, gap_type=None, entity=None):
        """
        Gibt gefilterte Gaps aus metadata_gaps zurück.
        Alle Parameter optional — None bedeutet kein Filter.
        """
        bedingungen = []
        parameter   = []

        if severity and severity != "alle":
            bedingungen.append("severity = ?")
            parameter.append(severity)
        if gap_type and gap_type != "alle":
            bedingungen.append("gap_type = ?")
            parameter.append(gap_type)
        if entity and entity != "alle":
            bedingungen.append("affected_entity = ?")
            parameter.append(entity)

        where = ("WHERE " + " AND ".join(bedingungen)) if bedingungen else ""

        query = f"""
            SELECT gap_type, gap_subtype, severity,
                   affected_entity, affected_id,
                   description, recommended_action, status
            FROM metadata_gaps
            {where}
            ORDER BY
                CASE severity WHEN 'high' THEN 1
                              WHEN 'medium' THEN 2
                              ELSE 3 END,
                gap_type
        """
        return pd.read_sql_query(query, self.conn, params=parameter)

    def requirements_nach_tier(self, tier=None):
        """
        Coverage-Übersicht der Anforderungen, optional nach Tier gefiltert.
        Berechnet coverage_dynamisch aus der Beziehungskette.
        """
        tier_filter = "AND r.tier_level = ?" if tier and tier != "alle" else ""
        parameter   = [tier] if tier and tier != "alle" else []

        query = f"""
            SELECT
                r.name,
                r.tier_level,
                r.priority,
                r.source,
                CASE
                    WHEN r.business_term_id   IS NOT NULL
                     AND r.technical_field_id IS NOT NULL
                     AND tf.field_owner       IS NOT NULL
                    THEN 'vollständig'
                    WHEN r.business_term_id IS NULL
                     AND r.technical_field_id IS NULL
                    THEN 'offen'
                    ELSE 'partiell'
                END AS coverage
            FROM requirements r
            LEFT JOIN technical_fields tf ON r.technical_field_id = tf.id
            WHERE 1=1 {tier_filter}
            ORDER BY r.tier_level, coverage DESC
        """
        return pd.read_sql_query(query, self.conn, params=parameter)

    def gap_typen(self):
        """Gibt alle vorhandenen gap_type-Werte zurück — für Dropdown-Befüllung."""
        return ["alle"] + pd.read_sql_query(
            "SELECT DISTINCT gap_type FROM metadata_gaps ORDER BY gap_type",
            self.conn
        )["gap_type"].tolist()

    def entitaeten(self):
        """Gibt alle affected_entity-Werte zurück — für Dropdown-Befüllung."""
        return ["alle"] + pd.read_sql_query(
            "SELECT DISTINCT affected_entity FROM metadata_gaps ORDER BY affected_entity",
            self.conn
        )["affected_entity"].tolist()

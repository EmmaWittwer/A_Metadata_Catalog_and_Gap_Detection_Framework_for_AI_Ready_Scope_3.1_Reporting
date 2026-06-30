# ================================================================
# seed_data.py — FloorTec Group Seed-Daten (Version 2)
# Scope 3.1 Carbon Data Catalog
# Ergänzt um: field_owner, data_entry_type, evidence_available,
#             evidence_type, manual_entry_count
# ================================================================

import sqlite3

def load_seed_data():
    conn = sqlite3.connect("catalog.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    # ── 1. QUELLSYSTEME ─────────────────────────────────────────
    source_systems = [
        ("SAP S/4HANA + BW",       "Konsolidierung", "FloorTec EU",  "Deutschland", "EUR", 1, "vollständig",        "SAP BW EU", "vollständig", "Anna Müller"),
        ("SAP FI",                 "Buchhaltung",    "FloorTec DE",  "Deutschland", "EUR", 0, "vollständig",        "SAP BW EU", "vollständig", "Thomas Becker"),
        ("SAP FI",                 "Buchhaltung",    "FloorTec FR",  "Frankreich",  "EUR", 0, "vollständig",        "SAP BW EU", "partiell",    "Claire Dubois"),
        ("Salesforce + QuickBooks","CRM",            "FloorTec USA", "USA",         "USD", 0, "nicht_angeschlossen", None,        "partiell",    None),
        ("SAP S/4HANA",            "ERP",            "FloorTec MY",  "Malaysia",    "MYR", 0, "nicht_angeschlossen", None,        "partiell",    None),
        ("Oracle Fusion",          "ERP",            "FloorTec CN",  "China",       "CNY", 0, "nicht_angeschlossen", None,        "unbekannt",   None),
        ("Microsoft D365",         "ERP",            "FloorTec AU",  "Australien",  "AUD", 0, "nicht_angeschlossen", None,        "partiell",    None),
        ("Kreditkartenabrechnung", "informell",      "FloorTec MY",  "Malaysia",    "MYR", 0, "nicht_angeschlossen", None,        "unbekannt",   None),
        ("Manuelle Excel",         "informell",      "FloorTec CN",  "China",       "CNY", 0, "nicht_angeschlossen", None,        "unbekannt",   None),
    ]

    cursor.executemany("""
        INSERT INTO source_systems
        (name, system_type, subsidiary, country, currency, is_central,
         consolidation_status, consolidation_target, data_availability, owner)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, source_systems)
    print(f"✓ {len(source_systems)} Quellsysteme eingefügt")

    # ── 2. DATENSÄTZE ────────────────────────────────────────────
    # Neue Felder: data_entry_type, evidence_available, evidence_type, manual_entry_count
    datasets = [
        # name, description, source_system_id, data_contact, data_contact_role,
        # data_contact_reliability, currency, exchange_rate_date, data_availability,
        # data_entry_type, evidence_available, evidence_type, manual_entry_count

        # EU Holding — zentral, automatisch
        ("MM_PURCHASE_ORDERS_EU",  "Zentrale Einkaufsbestellungen EU",          1, "Anna Müller",   "Controlling",  "hoch",   "EUR", "2024-12-31", "vollständig", "automatisch",    "True",      "Bestellung",    0),
        # DE — vollständig, automatisch
        ("FI_VENDOR_SPEND_DE",     "Lieferantenausgaben Deutschland",           2, "Thomas Becker", "Controlling",  "hoch",   "EUR", "2024-12-31", "vollständig", "automatisch",    "True",      "Rechnung",      0),
        # FR — partiell, semi-manuell
        ("FI_VENDOR_SPEND_FR",     "Lieferantenausgaben Frankreich",            3, "Claire Dubois", "Controlling",  "mittel", "EUR", "2024-12-31", "partiell",    "semi-manuell",   "True",      "Rechnung",      12),
        # USA — kein Owner, manuell, kein Beleg
        ("QB_VENDOR_SPEND_USA",    "Lieferantenausgaben USA (QuickBooks)",      4, None,            "unbekannt",    "niedrig","USD", None,         "partiell",    "manuell",        "False",     None,            47),
        ("SF_PURCHASE_ORDERS_USA", "Einkaufsbestellungen USA (Salesforce)",     4, None,            "unbekannt",    "niedrig","USD", None,         "partiell",    "manuell",        "False",     None,            31),
        # Malaysia — manuell, Beleg partiell
        ("SAP_GOODS_RECEIPT_MY",   "Wareneingänge Malaysia (Rohstoffe)",        5, None,            "GL-Assistenz", "niedrig","MYR", None,         "partiell",    "semi-manuell",   "unbekannt", "Lieferschein",  28),
        # China — manuell, kein Beleg
        ("ORA_PURCHASE_ORDERS_CN", "Einkaufsbestellungen China",               6, None,            "GL-Assistenz", "niedrig","CNY", None,         "unbekannt",   "manuell",        "False",     None,            64),
        # Australien — semi-manuell, Beleg vorhanden
        ("D365_GOODS_RECEIPT_AU",  "Wareneingänge Australien (Mineralien)",     7, None,            "IT",           "mittel", "AUD", None,         "partiell",    "semi-manuell",   "True",      "Lieferschein",  15),
        # Shadow Data Malaysia — informell, kein Beleg
        ("SHADOW_CC_MY",           "Kreditkartenabrechnungen Malaysia",         8, None,            "GL-Assistenz", "niedrig","MYR", None,         "unbekannt",   "manuell",        "False",     None,            83),
        # Shadow Data China — informell, kein Beleg
        ("SHADOW_XLS_CN",          "Manuelle Excel-Exporte China",              9, None,            "GL-Assistenz", "niedrig","CNY", None,         "unbekannt",   "manuell",        "False",     None,            97),
    ]

    cursor.executemany("""
        INSERT INTO datasets
        (name, description, source_system_id, data_contact, data_contact_role,
         data_contact_reliability, currency, exchange_rate_date, data_availability,
         data_entry_type, evidence_available, evidence_type, manual_entry_count)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, datasets)
    print(f"✓ {len(datasets)} Datensätze eingefügt")

    # ── 3. TECHNISCHE FELDER ─────────────────────────────────────
    # Neues Feld: field_owner (NULL = Gap auf Feldebene)
    technical_fields = [
        # dataset_id, field_name, field_description, data_type, unit,
        # unit_system, material_description_quality, field_owner, is_nullable

        # EU zentral — vollständig dokumentiert
        (1, "LIFNR",      "Lieferantennummer",           "TEXT",    "ID",    "metrisch", "lesbar",           "Anna Müller",   0),
        (1, "NETWR",      "Nettowert Einkauf EUR",        "NUMERIC", "EUR",   "metrisch", "lesbar",           "Anna Müller",   0),
        (1, "MATKL",      "Materialgruppe",               "TEXT",    None,    "metrisch", "lesbar",           "Thomas Becker", 0),
        # DE — vollständig
        (2, "LIFNR",      "Lieferantennummer DE",         "TEXT",    "ID",    "metrisch", "lesbar",           "Thomas Becker", 0),
        (2, "NETWR",      "Nettowert EUR",                "NUMERIC", "EUR",   "metrisch", "lesbar",           "Thomas Becker", 0),
        # FR — partiell, ein Feld ohne Owner
        (3, "LIFNR",      "Lieferantennummer FR",         "TEXT",    "ID",    "metrisch", "lesbar",           "Claire Dubois", 0),
        (3, "NETWR",      "Nettowert EUR FR",             "NUMERIC", "EUR",   "metrisch", "teilweise_lesbar", None,            1),
        # USA — kein Field Owner, unleserlich
        (4, "VendorID",   "Lieferanten-ID USA",           "TEXT",    "ID",    "metrisch", "lesbar",           None,            0),
        (4, "Amount_USD", "Ausgabenbetrag USD",           "NUMERIC", "USD",   "metrisch", "lesbar",           None,            0),
        (5, "MatCode",    "Materialcode Salesforce",      "TEXT",    None,    "metrisch", "teilweise_lesbar", None,            1),
        # Malaysia — lokale Einheiten, kein Field Owner
        (6, "MENGE",      "Menge Wareneingang",           "NUMERIC", "Pikul", "lokal",    "lesbar",           None,            0),
        (6, "MATKL",      "Materialgruppe MY",            "TEXT",    None,    "metrisch", "teilweise_lesbar", None,            1),
        # China — unleserlich, kein Field Owner
        (7, "QTY",        "Menge CN",                    "NUMERIC", "pcs",   "gemischt", "unlesbar",         None,            1),
        (7, "MAT_DESC",   "Materialbeschreibung CN",      "TEXT",    None,    None,       "unlesbar",         None,            1),
        # Australien — imperial, Field Owner vorhanden
        (8, "QUANTITY",   "Menge AU",                    "NUMERIC", "lbs",   "imperial", "lesbar",           "IT-Owner AU",   0),
        (8, "MATERIAL",   "Materialbezeichnung AU",       "TEXT",    None,    "imperial", "lesbar",           None,            1),
        # Shadow MY — keine Owner, fehlende Beschreibung
        (9, "Betrag",     "Kreditkartenbetrag MYR",      "NUMERIC", "MYR",   "metrisch", "fehlend",          None,            1),
        # Shadow CN — keine Owner, fehlende Beschreibung
        (10,"Ausgabe",    "Manuell erfasste Ausgabe CNY", "NUMERIC", "CNY",   "metrisch", "fehlend",          None,            1),
    ]

    cursor.executemany("""
        INSERT INTO technical_fields
        (dataset_id, field_name, field_description, data_type, unit,
         unit_system, material_description_quality, field_owner, is_nullable)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, technical_fields)
    print(f"✓ {len(technical_fields)} Technische Felder eingefügt")

    # ── 4. BUSINESS TERMS ────────────────────────────────────────
    business_terms = [
        ("Lieferant",                "Externes Unternehmen das Waren oder Dienstleistungen liefert", "Anna Müller",   "Einkauf",        2),
        ("Materialgruppe",           "Klassifikation von Materialien nach Typ und Verwendung",        "Thomas Becker", "Einkauf",        2),
        ("Einkaufswert",             "Nettobetrag einer Einkaufsbestellung in Buchungswährung",       "Anna Müller",   "Finanzen",       3),
        ("Emissionsfaktor",          "kg CO2e pro Einheit Material oder Ausgabe (EXIOBASE)",          None,            "Nachhaltigkeit", 2),
        ("Materialherkunftsland",    "Land der Rohstoffgewinnung oder Produktion",                    None,            "Nachhaltigkeit", 2),
        ("Einheit",                  "Mengeneinheit einer Einkaufsposition (kg, lbs, Pikul, pcs)",    None,            "Einkauf",        2),
        ("Währung",                  "Buchungswährung je Gesellschaft",                               "Anna Müller",   "Finanzen",       3),
        ("Wechselkurs",              "Jahresdurchschnittskurs zur EUR-Konversion",                    None,            "Finanzen",       3),
        ("Verifikationsstatus",      "Nachweis ob Lieferantendaten extern geprüft wurden",            None,            "Nachhaltigkeit", 1),
        ("Lieferantenklassifikation","Einstufung nach Emissionsrelevanz und Klimarisiko",             None,            "Nachhaltigkeit", 3),
    ]

    cursor.executemany("""
        INSERT INTO business_terms
        (name, definition, owner, domain, tier_level)
        VALUES (?,?,?,?,?)
    """, business_terms)
    print(f"✓ {len(business_terms)} Business Terms eingefügt")

    # ── 5. ANFORDERUNGEN ─────────────────────────────────────────
    requirements = [
        ("Lieferantenspez. THG-Daten",   "Produktspezifische Emissionen direkt vom Lieferanten",         "GHG Protocol", 1, "low",    9,  None, "offen"),
        ("Verifikationsstatus",           "Nachweis externer Prüfung von Lieferantendaten",               "ESRS E1",      1, "low",    9,  None, "offen"),
        ("Eingekaufte Menge je Lieferant","Menge je Lieferant und Material für massebasierte Methode",    "GHG Protocol", 2, "high",   6,  11,   "partiell"),
        ("Einheitennormierung",           "Konvertierung lokaler und imperialer Einheiten in kg",         "GHG Protocol", 2, "high",   6,  None, "offen"),
        ("Materialgruppe harmonisiert",   "Lesbare Materialgruppe als Basis für EF-Mapping",              "GHG Protocol", 2, "high",   2,  12,   "partiell"),
        ("Emissionsfaktor je Matgruppe",  "EXIOBASE-Faktor in kg CO2e pro Einheit",                      "GHG Protocol", 2, "high",   4,  None, "offen"),
        ("Materialherkunftsland",         "Herkunftsland für EF-Splitting und Klimarisiko",               "ESRS E1",      2, "medium", 5,  None, "offen"),
        ("Einkaufswert je Lieferant",     "Einkaufswert in EUR nach Währungskonversion",                  "GHG Protocol", 3, "medium", 3,  2,    "partiell"),
        ("Quellsystem je Gesellschaft",   "Identifikation des führenden Systems je Tochtergesellschaft",  "GHG Protocol", 3, "medium", None, None,"partiell"),
        ("Lieferantenklassifikation",     "Einstufung nach Emissionsrelevanz, Länderrisiko, Engagement",  "ESRS E1",      3, "medium", 10, None, "offen"),
        ("Belegnachweis manuelle Daten",  "Nachweis für manuell eingetragene Datenpunkte (Rechnung etc)", "ESRS E1",      3, "high",   None,None,"offen"),
    ]

    cursor.executemany("""
        INSERT INTO requirements
        (name, description, source, tier_level, priority,
         business_term_id, technical_field_id, coverage_status)
        VALUES (?,?,?,?,?,?,?,?)
    """, requirements)
    print(f"✓ {len(requirements)} Anforderungen eingefügt")

    conn.commit()
    conn.close()
    print("\n✓ Seed-Daten Version 2 vollständig geladen — catalog.db bereit")

if __name__ == "__main__":
    load_seed_data()
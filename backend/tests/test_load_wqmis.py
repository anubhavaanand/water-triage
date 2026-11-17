from etl.load_wqmis import upsert_geo


def test_upsert_geo_uses_enriched_locations_when_enabled(db):
    village = upsert_geo(
        db,
        {
            "state": "Uttar Pradesh",
            "district": "Raw district",
            "inferred_district": "Inferred district",
            "village": "Raw village",
            "extracted_location": "Extracted village",
        },
        use_enriched=True,
    )

    assert village.district.name == "Inferred district"
    assert village.name == "Extracted village"


def test_upsert_geo_uses_raw_locations_when_enrichment_is_disabled(db):
    village = upsert_geo(
        db,
        {
            "state": "Uttar Pradesh",
            "district": "Raw district",
            "inferred_district": "Inferred district",
            "village": "Raw village",
            "extracted_location": "Extracted village",
        },
        use_enriched=False,
    )

    assert village.district.name == "Raw district"
    assert village.name == "Raw village"

import pandas as pd

from frontend.dashboard import apply_filters, filter_candidates


def test_filter_candidates_choose_date_and_category_fields() -> None:
    frame = pd.DataFrame(
        {
            "order_date": ["2026-01-01", "2026-02-01"],
            "region": ["North", "South"],
            "revenue": [100, 200],
        }
    )

    assert filter_candidates(
        frame,
        {"date_columns": ["order_date"], "categorical_columns": ["region", "order_date"]},
    ) == ("order_date", "region")


def test_apply_filters_restricts_date_and_category() -> None:
    frame = pd.DataFrame(
        {
            "order_date": ["2026-01-01", "2026-02-01", "2026-03-01"],
            "region": ["North", "South", "North"],
            "revenue": [100, 200, 300],
        }
    )

    filtered = apply_filters(
        frame,
        "order_date",
        ("2026-01-15", "2026-03-15"),
        "region",
        ["North"],
    )

    assert filtered.to_dict(orient="records") == [
        {"order_date": "2026-03-01", "region": "North", "revenue": 300}
    ]

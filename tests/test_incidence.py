from ew_observe.incidence import IncidenceRow, IncidenceTable, render_text


def test_sparse_incidence_text_aligns_columns_without_default_paneling():
    table = IncidenceTable(
        leading_headers=("role", "object", "occurrence"),
        features=(2, 3, 11),
        rows=(
            IncidenceRow(("B", "55", "a_9"), ((11, "1"),)),
            IncidenceRow(("A", "10", "a_10"), ((2, "1"),)),
            IncidenceRow(("T", "12", "a_7"), ((2, "2"), (3, "+1"))),
        ),
    )

    rendered = render_text(table)
    lines = rendered.splitlines()
    assert lines[0].split() == ["role", "object", "occurrence", "2", "3", "11"]
    assert lines[1].count("-") > 0
    assert "+1" in lines[-1]
    assert "prime columns" not in rendered


def test_sparse_incidence_text_only_splits_when_width_is_explicit():
    table = IncidenceTable(
        leading_headers=("role", "object", "occurrence"),
        features=(2, 3, 5, 7, 11, 13),
        rows=(
            IncidenceRow(
                ("T", "30030", "a_1"),
                ((2, "1"), (3, "+1"), (5, "+1"), (7, "+1"), (11, "+1"), (13, "+1")),
            ),
        ),
    )

    unbroken = render_text(table)
    assert "prime columns" not in unbroken
    assert all(str(prime) in unbroken.splitlines()[0] for prime in table.features)

    paneled = render_text(table, max_width=32)
    assert "prime columns" in paneled
    assert "(1/" in paneled

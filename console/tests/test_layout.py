from components.layout import status_pill


def test_status_pill_escapes_label() -> None:
    pill = status_pill("<script>alert(1)</script>", "green")
    assert "&lt;script&gt;" in pill
    assert "edd-pill-green" in pill


def test_status_pill_falls_back_to_blue() -> None:
    pill = status_pill("Pending", "purple")
    assert "edd-pill-blue" in pill

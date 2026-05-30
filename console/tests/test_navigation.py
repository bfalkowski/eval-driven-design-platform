from __future__ import annotations

from navigation import LIFECYCLE_PAGE_SPECS, LIFECYCLE_SECTIONS, page_path


def test_lifecycle_sections_match_hld_mvp_subset() -> None:
    assert LIFECYCLE_SECTIONS == ("Overview", "Design", "Build", "Evaluate", "Promote")


def test_lifecycle_page_specs_reference_existing_files() -> None:
    assert set(LIFECYCLE_PAGE_SPECS) == set(LIFECYCLE_SECTIONS)
    for section, specs in LIFECYCLE_PAGE_SPECS.items():
        assert specs, f"missing pages for section {section!r}"
        for spec in specs:
            assert page_path(spec.relative_path).is_file(), spec.relative_path


def test_default_page_is_overview() -> None:
    overview_specs = [spec for spec in LIFECYCLE_PAGE_SPECS["Overview"] if spec.default]
    assert len(overview_specs) == 1
    assert overview_specs[0].title == "Overview"

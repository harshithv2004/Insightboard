"""
tests/test_validation.py
Unit tests for the services.validate_filters() function.
No database connection needed.
"""
import pytest
from app.services import validate_filters, ValidationError


# ── Date validation ────────────────────────────────────────────────────────

class TestDateValidation:

    def test_valid_dates_accepted(self):
        result = validate_filters({"start_date": "2024-01-01", "end_date": "2024-12-31"})
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"]   == "2024-12-31"

    def test_invalid_start_date_format(self):
        with pytest.raises(ValidationError, match="start_date"):
            validate_filters({"start_date": "01-01-2024"})

    def test_invalid_end_date_format(self):
        with pytest.raises(ValidationError, match="end_date"):
            validate_filters({"end_date": "not-a-date"})

    def test_start_after_end_raises_error(self):
        with pytest.raises(ValidationError, match="start_date cannot be after end_date"):
            validate_filters({"start_date": "2024-12-31", "end_date": "2024-01-01"})

    def test_same_start_and_end_accepted(self):
        # A single-day range is valid
        result = validate_filters({"start_date": "2024-06-15", "end_date": "2024-06-15"})
        assert result["start_date"] == "2024-06-15"

    def test_empty_dates_not_included_in_result(self):
        result = validate_filters({})
        assert "start_date" not in result
        assert "end_date"   not in result


# ── Region validation ──────────────────────────────────────────────────────

class TestRegionValidation:

    @pytest.mark.parametrize("region", ["North", "South", "East", "West", "Central"])
    def test_valid_regions_accepted(self, region):
        result = validate_filters({"region": region})
        assert result["region"] == region

    def test_invalid_region_raises_error(self):
        with pytest.raises(ValidationError, match="Invalid region"):
            validate_filters({"region": "InvalidRegion"})

    def test_empty_region_not_in_result(self):
        result = validate_filters({"region": ""})
        assert "region" not in result

    def test_region_is_case_sensitive(self):
        with pytest.raises(ValidationError):
            validate_filters({"region": "north"})  # lowercase not allowed


# ── Category validation ────────────────────────────────────────────────────

class TestCategoryValidation:

    @pytest.mark.parametrize("cat", ["Electronics", "Office Supplies", "Furniture", "Software", "Accessories"])
    def test_valid_categories_accepted(self, cat):
        result = validate_filters({"category": cat})
        assert result["category"] == cat

    def test_invalid_category_raises_error(self):
        with pytest.raises(ValidationError, match="Invalid category"):
            validate_filters({"category": "Widgets"})

    def test_empty_category_not_in_result(self):
        result = validate_filters({"category": ""})
        assert "category" not in result


# ── Status validation ──────────────────────────────────────────────────────

class TestStatusValidation:

    @pytest.mark.parametrize("status", ["Completed", "Pending", "Cancelled"])
    def test_valid_statuses_accepted(self, status):
        result = validate_filters({"status": status})
        assert result["status"] == status

    def test_invalid_status_raises_error(self):
        with pytest.raises(ValidationError, match="Invalid status"):
            validate_filters({"status": "Shipped"})

    def test_empty_status_not_in_result(self):
        result = validate_filters({"status": ""})
        assert "status" not in result


# ── Combined filters ───────────────────────────────────────────────────────

class TestCombinedFilters:

    def test_all_valid_filters_combined(self):
        result = validate_filters({
            "start_date": "2024-01-01",
            "end_date":   "2024-06-30",
            "region":     "North",
            "category":   "Electronics",
            "status":     "Completed",
        })
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"]   == "2024-06-30"
        assert result["region"]     == "North"
        assert result["category"]   == "Electronics"
        assert result["status"]     == "Completed"

    def test_empty_dict_returns_empty_dict(self):
        result = validate_filters({})
        assert result == {}

    def test_date_error_takes_priority_over_region(self):
        with pytest.raises(ValidationError):
            validate_filters({"start_date": "bad-date", "region": "North"})

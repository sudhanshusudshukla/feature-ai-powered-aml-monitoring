"""Integration tests for GET /api/v1/rules list and detail endpoints."""
import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.rules.models import DetectionRule, RuleVersion
from app.common.enums import RuleSeverity


@pytest.fixture
def sample_rules_dataset(db_session: Session) -> list[DetectionRule]:
    """Create a diverse set of rules for list testing."""
    rules = []
    now = datetime.utcnow()
    
    severities = [RuleSeverity.LOW, RuleSeverity.MEDIUM, RuleSeverity.HIGH, RuleSeverity.CRITICAL]
    
    rule_configs = [
        ("AML-001", "High Value Transaction", {"threshold": 100000}, True),
        ("AML-002", "Transaction Velocity Count", {"threshold_7d_count": 10}, True),
        ("AML-003", "Transaction Velocity Amount", {"threshold_24h_total": 500000}, True),
        ("AML-004", "High Risk Geography", {}, True),
        ("AML-005", "Sanctioned or PEP Customer", {}, True),
        ("AML-006", "Structuring Pattern", {"count_threshold_30m": 5}, False),
        ("AML-007", "Dormancy Spike", {"spike_multiplier": 5.0}, True),
        ("AML-008", "Round Amount Pattern", {"min_round_amount": 10000}, False),
        ("AML-009", "Test Inactive Rule", {}, False),
        ("AML-010", "Test Critical Rule", {"threshold": 1000000}, True),
    ]
    
    for i, (code, name, params, is_active) in enumerate(rule_configs):
        rule = DetectionRule(
            rule_code=code,
            name=name,
            severity=severities[i % len(severities)].value,
            description=f"Test rule: {name}",
            is_active=is_active,
            version=1,
            created_at=now - timedelta(days=i),
            updated_at=now - timedelta(days=i),
        )
        db_session.add(rule)
        db_session.flush()
        
        # Add initial version
        rule_version = RuleVersion(
            rule_id=rule.id,
            version_number=1,
            parameters_json=json.dumps(params),
            effective_from=now - timedelta(days=i),
        )
        db_session.add(rule_version)
        
        # Add second version for some rules
        if i % 3 == 0:
            rule_version_2 = RuleVersion(
                rule_id=rule.id,
                version_number=2,
                parameters_json=json.dumps({**params, "updated": True}),
                effective_from=now - timedelta(days=i - 1),
            )
            db_session.add(rule_version_2)
            rule.version = 2
        
        rules.append(rule)
    
    db_session.commit()
    return rules


def test_list_rules_requires_auth(client: TestClient):
    """Test that list rules requires authentication."""
    response = client.get("/api/v1/rules")
    assert response.status_code == 401


def test_list_rules_success(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test successful rules list retrieval."""
    response = auth_client.get("/api/v1/rules")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] == 10
    assert len(data["items"]) == 10


def test_list_rules_pagination(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test rules list pagination."""
    # Page 1 with 5 items
    response = auth_client.get("/api/v1/rules?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["total"] == 10
    
    # Page 2 with 5 items
    response = auth_client.get("/api/v1/rules?page=2&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2


def test_list_rules_filter_by_active_status(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test filtering rules by active status."""
    response = auth_client.get("/api/v1/rules?is_active=true")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items are active
    for item in data["items"]:
        assert item["is_active"] is True
    
    assert data["total"] == 7  # 7 active rules


def test_list_rules_filter_by_inactive_status(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test filtering rules by inactive status."""
    response = auth_client.get("/api/v1/rules?is_active=false")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items are inactive
    for item in data["items"]:
        assert item["is_active"] is False
    
    assert data["total"] == 3  # 3 inactive rules


def test_list_rules_filter_by_severity(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test filtering rules by severity."""
    response = auth_client.get("/api/v1/rules?severity=HIGH")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items have HIGH severity
    for item in data["items"]:
        assert item["severity"] == "HIGH"


def test_list_rules_sort_by_rule_code_asc(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test sorting rules by rule_code ascending (default)."""
    response = auth_client.get("/api/v1/rules?sort_by=rule_code&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    
    # Check items are sorted by rule_code ascending
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["rule_code"] <= items[i + 1]["rule_code"]


def test_list_rules_sort_by_name_desc(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test sorting rules by name descending."""
    response = auth_client.get("/api/v1/rules?sort_by=name&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    
    # Check items are sorted by name descending
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["name"] >= items[i + 1]["name"]


def test_list_rules_multiple_filters(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test combining multiple filters."""
    response = auth_client.get("/api/v1/rules?is_active=true&severity=MEDIUM")
    assert response.status_code == 200
    data = response.json()
    
    # Check all items match both filters
    for item in data["items"]:
        assert item["is_active"] is True
        assert item["severity"] == "MEDIUM"


def test_list_rules_response_structure(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test the structure of rule list items."""
    response = auth_client.get("/api/v1/rules?page_size=1")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["items"]) == 1
    item = data["items"][0]
    
    # Check all expected fields are present
    assert "id" in item
    assert "rule_code" in item
    assert "name" in item
    assert "severity" in item
    assert "description" in item
    assert "is_active" in item
    assert "version" in item
    assert "created_at" in item
    assert "updated_at" in item


def test_list_rules_empty_results(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test filtering with no matching results."""
    response = auth_client.get("/api/v1/rules?severity=NONEXISTENT")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_get_rule_detail_success(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test successful rule detail retrieval."""
    response = auth_client.get("/api/v1/rules/AML-001")
    assert response.status_code == 200
    
    data = response.json()
    assert data["rule_code"] == "AML-001"
    assert data["name"] == "High Value Transaction"
    assert "versions" in data
    assert len(data["versions"]) >= 1


def test_get_rule_detail_with_multiple_versions(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test rule detail includes all versions."""
    response = auth_client.get("/api/v1/rules/AML-001")
    assert response.status_code == 200
    
    data = response.json()
    versions = data["versions"]
    
    # AML-001 should have 2 versions (created at i=0, so has second version)
    assert len(versions) == 2
    
    # Check versions are ordered
    for i in range(len(versions) - 1):
        assert versions[i]["version_number"] >= versions[i + 1]["version_number"]


def test_get_rule_detail_not_found(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test rule detail with non-existent rule code."""
    response = auth_client.get("/api/v1/rules/AML-999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_rule_detail_requires_auth(client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test rule detail requires authentication."""
    response = client.get("/api/v1/rules/AML-001")
    assert response.status_code == 401


def test_get_rule_detail_response_structure(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test the structure of rule detail response."""
    response = auth_client.get("/api/v1/rules/AML-002")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check main fields
    assert "id" in data
    assert "rule_code" in data
    assert "name" in data
    assert "severity" in data
    assert "description" in data
    assert "is_active" in data
    assert "version" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "versions" in data
    
    # Check version structure
    assert isinstance(data["versions"], list)
    if len(data["versions"]) > 0:
        version = data["versions"][0]
        assert "version_number" in version
        assert "parameters_json" in version
        assert isinstance(version["parameters_json"], dict)
        assert "effective_from" in version


def test_list_rules_invalid_page(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test with invalid page number."""
    response = auth_client.get("/api/v1/rules?page=0")
    assert response.status_code == 422  # Validation error


def test_list_rules_invalid_page_size(auth_client: TestClient, sample_rules_dataset: list[DetectionRule]):
    """Test with page size exceeding maximum."""
    response = auth_client.get("/api/v1/rules?page_size=150")
    assert response.status_code == 422  # Exceeds max of 100

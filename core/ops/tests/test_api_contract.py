import pytest
from fastapi.testclient import TestClient

from approval_queue import ProposalRecord, ProposalState
from grid.api import app


def _proposal() -> ProposalRecord:
    return ProposalRecord(
        id="proposal_test",
        state=ProposalState.PROPOSED,
        canon_input="test",
        interpretation={},
        consistency={},
        placement={},
        proposed_mutations=[],
        proposed_at="2026-05-27T00:00:00+00:00",
    )


def test_proposal_record_serializes_canonical_contract():
    payload = _proposal().to_dict()

    assert "id" not in payload
    assert payload["proposal_id"] == "proposal_test"
    assert payload["state"] == "PROPOSED"


def test_proposal_record_loads_legacy_lowercase_state():
    payload = _proposal().to_dict()
    payload["state"] = "proposed"

    record = ProposalRecord.from_dict(payload)

    assert record.id == "proposal_test"
    assert record.state == ProposalState.PROPOSED


@pytest.mark.parametrize("endpoint", ["/api/think", "/api/learn"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_direct_write_endpoints_return_410(endpoint, method):
    client = TestClient(app)

    response = getattr(client, method)(endpoint)

    assert response.status_code == 410
    assert response.json()["error"] == "direct_write_disabled"

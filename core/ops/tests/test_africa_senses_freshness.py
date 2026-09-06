from datetime import datetime, timedelta, timezone

from grid.external_data import _canonical_africa_report, _refresh_payload_ages


def _payload(observed_at: str) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "weather": {
            "locations": [
                {
                    "location": "Nairobi",
                    "country": "Kenya",
                    "temperature_c": 24.0,
                    "summary": "clear",
                    "provider_count": 1,
                    "providers_used": ["open_meteo"],
                    "observed_at": observed_at,
                    "freshness_seconds": 0,
                }
            ]
        },
        "health": {"state": "PARTIAL"},
        "sovereignty": {"state": "PARTIAL"},
    }


def test_cached_observation_age_advances_instead_of_remaining_zero():
    observed = (datetime.now(timezone.utc) - timedelta(seconds=90)).isoformat()
    refreshed = _refresh_payload_ages(_payload(observed))
    assert refreshed["weather"]["locations"][0]["freshness_seconds"] >= 89
    assert refreshed["served_at"] != refreshed["generated_at"]


def test_canonical_report_is_deterministic_and_source_bound():
    payload = _payload(datetime.now(timezone.utc).isoformat())
    first = _canonical_africa_report(payload)
    second = _canonical_africa_report(payload)
    assert first["canonical"] is True
    assert first["text"] == " ".join(first["segments"])
    assert first["source_digest"] == second["source_digest"]
    assert first["source_refs"] == ["open_meteo"]

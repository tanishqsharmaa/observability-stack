import pytest


@pytest.fixture
def sample_trace_payload():
    return {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "warden-retrieval"}}
                    ]
                },
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                                "spanId": "00f067aa0ba902b7",
                                "name": "hybrid_search",
                                "attributes": [
                                    {"key": "warden.trace_id", "value": {"stringValue": "4bf92f35-77b3-4da6-a3ce-929d0e0e4736"}},
                                    {"key": "warden.caller_role", "value": {"stringValue": "Employee"}},
                                    {"key": "warden.query_hash", "value": {"stringValue": "a4f89b2c3d..."}},
                                    {"key": "warden.chunks_retrieved_count", "value": {"intValue": 30}},
                                    {"key": "warden.chunks_reranked_count", "value": {"intValue": 5}},
                                    {"key": "warden.reranker_fallback_active", "value": {"boolValue": False}}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

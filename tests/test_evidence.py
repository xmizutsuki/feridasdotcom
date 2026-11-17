"""Synthetic operator-reviewed snippets only. Test metadata, no medical conclusions."""
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import authenticate

def payload(**changes):
    baseline={
        "catalog_source_id":"iwgdf-2023-wound-healing",
        "source_location":"synthetic section 1 / example only",
        "excerpt":"Synthetic demonstration passage about standardized image capture and record documentation.",
        "language":"en",
        "topic_tags":["assessment","wound_healing"],
        "reviewed_by":"SYNTHETIC-REVIEWER",
        "confirmation":"verified_in_original_document",
        "applicability_notes":"Synthetic test data, not a genuine guideline statement",
    }
    baseline.update(changes)
    return baseline

def test_catalog_is_bibliography_only_and_requires_authentication():
    with TestClient(app) as client:
        assert client.get("/evidence/catalog").status_code==401
        authenticate(client)
        data=client.get("/evidence/catalog").json()
        assert data["content_verified"] is False
        assert data["sources"]
        assert all(s["verification_status"]=="publisher_page_identified" for s in data["sources"])
        assert client.get("/evidence/search",params={"q":"documentation"}).json()["matches"]==[]

def test_unattested_unknown_source_and_bad_tags_are_rejected():
    with TestClient(app) as client:
        authenticate(client)
        path="/evidence/passages"
        assert client.post(path,json=payload(confirmation="")).status_code==422
        assert client.post(path,json=payload(catalog_source_id="invented-journal")).status_code==422
        assert client.post(path,json=payload(topic_tags=["imaginary_tag"])).status_code==422

def test_short_excerpt_recorded_and_locally_retrieved_without_recommendations():
    with TestClient(app) as client:
        authenticate(client)
        unique="synthetic"+uuid4().hex[:12]
        original=payload(excerpt=f"Demonstration {unique}: photographic documentation in a synthetic scenario.")
        saved=client.post("/evidence/passages",json=original)
        assert saved.status_code==201,saved.text
        stored=saved.json()
        assert stored["excerpt"]==original["excerpt"]
        assert len(stored["excerpt_sha256"])==64
        assert stored["source_location"]==original["source_location"]
        assert client.post("/evidence/passages",json=original).status_code==409
        result=client.get("/evidence/search",params={"q":unique})
        assert result.status_code==200
        body=result.json()
        assert body["retrieval_method"]=="local_lexical_v1"
        assert body["reasoning_executed"] is False
        assert body["recommendations_enabled"] is False
        match=next(m for m in body["matches"] if m["passage"]["id"]==stored["id"])
        assert match["clinical_applicability_validated"] is False
        assert match["publisher_url"]=="https://iwgdfguidelines.org/wound-healing-2023/"

def test_search_requires_session_and_has_no_general_internet_retrieval():
    with TestClient(app) as client:
        assert client.get("/evidence/search",params={"q":"infection"}).status_code==401
        authenticate(client)
        assert client.get("/evidence/search",params={"q":"a"*181}).status_code==422
        assert client.get("/evidence/search",params={"q":"foo","limit":50}).status_code==422

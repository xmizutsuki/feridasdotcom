from fastapi.testclient import TestClient
from app.main import app

def test_dashboard_is_served_locally():
    with TestClient(app) as client:
        landing = client.get("/", follow_redirects=False)
        assert landing.status_code in (302, 307)
        assert landing.headers["location"] == "/app/"
        html = client.get("/app/")
        assert html.status_code == 200
        assert "feridas.com" in html.text
        assert "MODO PROTÓTIPO" in html.text
        js = client.get("/app/app.js")
        assert js.status_code == 200
        assert '"/patients"' in js.text
        css = client.get("/app/styles.css")
        assert css.status_code == 200
        assert ".sidebar" in css.text

from unittest.mock import patch


def test_project_context(client, tmp_path):
    with patch("lc_server.routes.context.scrape_project", return_value="## tree"):
        r = client.get(f"/api/context/project?path={tmp_path}")
    assert r.status_code == 200
    assert r.json()["context"] == "## tree"


def test_mcp_servers(client):
    with patch("lc_server.routes.context.discover_mcp_servers", return_value=["github", "slack"]):
        r = client.get("/api/context/mcp")
    assert r.status_code == 200
    assert r.json() == ["github", "slack"]

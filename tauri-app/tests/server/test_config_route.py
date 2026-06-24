def test_get_config(client):
    r = client.get("/api/config")
    assert r.status_code == 200
    assert "whisper_backend" in r.json()


def test_put_config(client):
    r = client.put("/api/config", json={"whisper_backend": "openai", "whisper_model": "whisper-1", "openai_api_key": ""})
    assert r.status_code == 200
    assert r.json()["whisper_backend"] == "openai"

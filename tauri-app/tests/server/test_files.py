def test_list_files(client, tmp_path):
    (tmp_path / "foo.py").write_text("x = 1")
    (tmp_path / "bar.md").write_text("# hi")
    r = client.get(f"/api/files?path={tmp_path}")
    assert r.status_code == 200
    names = [f["name"] for f in r.json()]
    assert "foo.py" in names
    assert "bar.md" in names


def test_read_file(client, tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hello world")
    r = client.get(f"/api/files/content?path={f}")
    assert r.status_code == 200
    assert r.json()["content"] == "hello world"


def test_write_file(client, tmp_path):
    f = tmp_path / "out.txt"
    r = client.put("/api/files/content", json={"path": str(f), "content": "written"})
    assert r.status_code == 200
    assert f.read_text() == "written"

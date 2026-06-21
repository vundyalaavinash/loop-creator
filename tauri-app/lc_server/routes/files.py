from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/files")


class WriteBody(BaseModel):
    path: str
    content: str


@router.get("")
def list_files(path: str):
    p = Path(path)
    if not p.is_dir():
        raise HTTPException(400, "Not a directory")
    nodes = []
    for child in sorted(p.iterdir()):
        if child.name.startswith("."):
            continue
        nodes.append({
            "name": child.name,
            "path": str(child),
            "is_dir": child.is_dir(),
        })
    return nodes


@router.get("/content")
def read_file(path: str):
    p = Path(path)
    if not p.is_file():
        raise HTTPException(404, "File not found")
    try:
        return {"path": path, "content": p.read_text(encoding="utf-8")}
    except UnicodeDecodeError:
        raise HTTPException(400, "File is not UTF-8 text")


@router.put("/content")
def write_file(body: WriteBody):
    p = Path(body.path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body.content, encoding="utf-8")
    return {"path": body.path, "status": "written"}

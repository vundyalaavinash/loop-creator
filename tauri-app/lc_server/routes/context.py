from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter
from creator.context.project import scrape_project
from creator.context.mcp import discover_mcp_servers

router = APIRouter(prefix="/api/context")


@router.get("/project")
def get_project_context(path: str = "."):
    context = scrape_project(path)
    return {"context": context}


@router.get("/mcp")
def get_mcp_servers():
    return discover_mcp_servers()

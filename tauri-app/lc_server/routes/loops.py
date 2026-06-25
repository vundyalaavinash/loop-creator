from __future__ import annotations
import asyncio
import json
import shutil
import threading
import time
from dataclasses import asdict
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from creator.spec import LoopSpec, load_spec, save_spec
from creator.runner import run_loop
from creator.gepa.engine import GenerationEvent

router = APIRouter(prefix="/api/loops")


def _loop_dir(loop_id: str) -> Path:
    return Path.home() / ".creator" / "loops" / loop_id


@router.post("")
def create_loop(spec: LoopSpec):
    loop_dir = _loop_dir(spec.id)
    loop_dir.mkdir(parents=True, exist_ok=True)
    save_spec(spec, str(loop_dir / "spec.yaml"))
    return {"id": spec.id, "status": "created"}


@router.get("")
def list_loops():
    base = Path.home() / ".creator" / "loops"
    if not base.exists():
        return []
    result = []
    for d in sorted(base.iterdir()):
        spec_path = d / "spec.yaml"
        if not spec_path.exists():
            continue
        try:
            spec = load_spec(str(spec_path))
            loop_type = spec.type
        except Exception:
            loop_type = "unknown"
        history_path = d / "history.jsonl"
        last_modified = history_path.stat().st_mtime if history_path.exists() else 0
        active = (time.time() - last_modified) < 60
        best_score = None
        if history_path.exists():
            lines = [l for l in history_path.read_text().splitlines() if l.strip()]
            scores = [json.loads(l).get("score", 0) for l in lines]
            best_score = max(scores) if scores else None
        result.append({
            "id": d.name,
            "name": d.name,
            "loop_type": loop_type,
            "last_modified": last_modified,
            "best_score": best_score,
            "active": active,
        })
    return result


@router.get("/{loop_id}")
def get_loop(loop_id: str):
    spec_path = _loop_dir(loop_id) / "spec.yaml"
    if not spec_path.exists():
        raise HTTPException(404, "Loop not found")
    spec = load_spec(str(spec_path))
    return spec.model_dump()


@router.delete("/{loop_id}")
def delete_loop(loop_id: str):
    d = _loop_dir(loop_id)
    if not d.exists():
        raise HTTPException(404, "Loop not found")
    shutil.rmtree(d)
    return {"id": loop_id, "status": "deleted"}


@router.post("/{loop_id}/run")
async def run_loop_sse(loop_id: str):
    loop_dir = _loop_dir(loop_id)
    if not (loop_dir / "spec.yaml").exists():
        raise HTTPException(404, "Loop not found")
    spec = load_spec(str(loop_dir / "spec.yaml"))

    main_loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def run_in_thread():
        def on_event(ev):
            main_loop.call_soon_threadsafe(queue.put_nowait, ev)
        try:
            run_loop(spec, str(loop_dir), on_event=on_event)
        except Exception as exc:
            err = GenerationEvent(generation=0, variants=[], best_score=0.0,
                                  event_type="error", error=str(exc))
            main_loop.call_soon_threadsafe(queue.put_nowait, err)
        finally:
            main_loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=run_in_thread, daemon=True).start()

    async def generate():
        while True:
            ev = await queue.get()
            if ev is None:
                break
            yield f"data: {json.dumps(asdict(ev))}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/{loop_id}/history")
def get_history(loop_id: str):
    history_path = _loop_dir(loop_id) / "history.jsonl"
    if not history_path.exists():
        return []
    lines = [l for l in history_path.read_text().splitlines() if l.strip()]
    return [json.loads(l) for l in lines]


@router.get("/{loop_id}/best")
def get_best(loop_id: str):
    best_path = _loop_dir(loop_id) / "best.md"
    if not best_path.exists():
        raise HTTPException(404, "No best result yet")
    return {"content": best_path.read_text()}

from __future__ import annotations
import asyncio
import json
import threading
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from creator.skills.spec import SkillSpec
from creator.skills.registry import (
    skill_dir,
    save_skill_spec,
    load_skill_spec,
    list_skills,
    delete_skill,
    publish_skill,
)
from creator.skills.runner import run_skill
from creator.gepa.engine import GenerationEvent

router = APIRouter(prefix="/api/skills")


@router.get("")
def get_skills():
    return list_skills()


@router.post("")
def create_skill(spec: SkillSpec):
    save_skill_spec(spec)
    return {"name": spec.name}


@router.get("/{name}")
def get_skill(name: str):
    d = skill_dir(name)
    if not (d / "spec.yaml").exists():
        raise HTTPException(status_code=404, detail="Skill not found")
    return load_skill_spec(name).model_dump()


@router.delete("/{name}")
def remove_skill(name: str):
    d = skill_dir(name)
    if not d.exists():
        raise HTTPException(status_code=404, detail="Skill not found")
    delete_skill(name)
    return {"ok": True}


@router.post("/{name}/run")
async def run_skill_sse(name: str):
    d = skill_dir(name)
    if not (d / "spec.yaml").exists():
        raise HTTPException(status_code=404, detail="Skill not found")
    spec = load_skill_spec(name)

    main_loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def run_in_thread():
        def on_event(ev):
            main_loop.call_soon_threadsafe(queue.put_nowait, ev)
        try:
            run_skill(spec, d, on_event=on_event)
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


@router.get("/{name}/output")
def get_skill_output(name: str):
    output = skill_dir(name) / "SKILL.md"
    if not output.exists():
        raise HTTPException(status_code=404, detail="No output yet")
    return {"content": output.read_text()}


@router.post("/{name}/publish")
def publish_skill_endpoint(name: str):
    d = skill_dir(name)
    if not (d / "SKILL.md").exists():
        raise HTTPException(status_code=400, detail="Run the skill first to generate SKILL.md")
    dest = publish_skill(name)
    return {"dest": str(dest)}

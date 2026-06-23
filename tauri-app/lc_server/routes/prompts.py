from __future__ import annotations
import asyncio
import json
import threading
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from creator.prompts.spec import PromptSpec
from creator.prompts.registry import (
    prompt_dir,
    save_prompt_spec,
    load_prompt_spec,
    list_prompts,
    delete_prompt,
)
from creator.prompts.runner import run_prompt

router = APIRouter(prefix="/api/prompts")


class UseBody(BaseModel):
    variables: dict[str, str] = {}


@router.get("")
def get_prompts():
    return list_prompts()


@router.post("")
def create_prompt(spec: PromptSpec):
    save_prompt_spec(spec)
    return {"name": spec.name}


@router.get("/{name}")
def get_prompt(name: str):
    d = prompt_dir(name)
    if not (d / "spec.yaml").exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    return load_prompt_spec(name).model_dump()


@router.delete("/{name}")
def remove_prompt(name: str):
    d = prompt_dir(name)
    if not d.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    delete_prompt(name)
    return {"ok": True}


@router.post("/{name}/run")
async def run_prompt_sse(name: str):
    d = prompt_dir(name)
    if not (d / "spec.yaml").exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    spec = load_prompt_spec(name)

    main_loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def run_in_thread():
        def on_event(ev):
            main_loop.call_soon_threadsafe(queue.put_nowait, ev)
        try:
            run_prompt(spec, d, on_event=on_event)
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
def get_prompt_output(name: str):
    output = prompt_dir(name) / f"{name}.md"
    if not output.exists():
        raise HTTPException(status_code=404, detail="No output yet")
    return {"content": output.read_text()}


@router.post("/{name}/use")
def use_prompt(name: str, body: UseBody):
    output = prompt_dir(name) / f"{name}.md"
    if not output.exists():
        raise HTTPException(status_code=404, detail="No output yet — run the prompt first")
    template = output.read_text()
    if template.startswith("---"):
        end = template.find("---", 3)
        template = template[end + 3:].lstrip("\n")
    for key, val in body.variables.items():
        template = template.replace(f"{{{{{key}}}}}", val)
    return {"resolved": template}

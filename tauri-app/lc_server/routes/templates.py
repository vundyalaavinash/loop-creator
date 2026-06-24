from fastapi import APIRouter
from dataclasses import asdict
from creator.templates.registry import LOOP_TEMPLATES, SKILL_TEMPLATES, PROMPT_TEMPLATES

router = APIRouter(prefix="/api/templates")

@router.get("/loops")
def list_loop_templates():
    return [asdict(t) for t in LOOP_TEMPLATES]

@router.get("/skills")
def list_skill_templates():
    return [asdict(t) for t in SKILL_TEMPLATES]

@router.get("/prompts")
def list_prompt_templates():
    return [asdict(t) for t in PROMPT_TEMPLATES]

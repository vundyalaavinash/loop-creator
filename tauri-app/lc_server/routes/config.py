from __future__ import annotations

from fastapi import APIRouter

from creator.config import CreatorConfig, load_config, save_config

router = APIRouter(prefix="/api/config")


@router.get("")
def get_config():
    return load_config().model_dump()


@router.put("")
def put_config(cfg: CreatorConfig):
    save_config(cfg)
    return cfg.model_dump()

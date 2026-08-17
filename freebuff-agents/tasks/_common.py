"""Shared helpers for freebuff-agents tasks."""
from pathlib import Path


def out_path(ctx, rel):
    p = ctx["assets"] / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write(ctx, rel, content):
    p = out_path(ctx, rel)
    p.write_text(content, encoding="utf-8")
    return p

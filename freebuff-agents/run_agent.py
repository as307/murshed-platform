#!/usr/bin/env python3
"""
FREEBUFF-AGENTS — Master Money Orchestrator

Consolidates everything (Claude work, Antigravity, Life/agents) into one
autonomous system that runs every task it can and stops only at human gates.

Usage:
  python3 run_agent.py           # run all pending auto tasks, then show gate queue
  python3 run_agent.py --status  # current progress
  python3 run_agent.py --gates   # the human to-do queue
"""
import argparse
import importlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "plan.json"
STATE = ROOT / "state.json"
# Auto tasks can be found in this repo OR in the GTM agent (Life/agents)
EXTRA_TASK_PATHS = [Path.home() / "Life" / "agents"]


def load_plan():
    with open(PLAN) as f:
        return json.load(f)


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"version": 1, "done": {}, "log": [], "started": time.strftime("%Y-%m-%d %H:%M")}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def log(state, entry):
    state["log"].append(f"[{time.strftime('%H:%M')}] {entry}")


def run_task(task, ctx):
    task_name = task["task"]
    here = ROOT / "tasks" / f"{task_name}.py"
    if here.exists():
        mod = importlib.import_module(f"tasks.{task_name}")
        return mod.run(ctx)
    for base in EXTRA_TASK_PATHS:
        p = base / "tasks" / f"{task_name}.py"
        if p.exists():
            spec = importlib.util.spec_from_file_location(task_name, p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.run(ctx)
    raise ImportError(f"task module '{task_name}' not found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--gates", action="store_true")
    args = ap.parse_args()

    plan = load_plan()
    state = load_state()
    ctx = {"root": ROOT, "assets": ROOT / "assets", "state": state, "log": log}

    if args.status:
        print_status(plan, state)
        return
    if args.gates:
        print_gates(plan, state)
        return

    print("=" * 66)
    print("  🤖 FREEBUFF-AGENTS — Master Money Orchestrator")
    print(f"  Mission: {plan['mission']}")
    print("=" * 66)

    ran_any = False
    for track in plan["tracks"]:
        for step in track["steps"]:
            sid = step["id"]
            if state["done"].get(sid):
                continue
            if step["type"] == "auto":
                print(f"\n  ▶ {sid}  {step['title']}")
                try:
                    result = run_task(step, ctx)
                    state["done"][sid] = {
                        "at": time.strftime("%Y-%m-%d %H:%M"),
                        "out": result.get("out", ""),
                        "summary": result.get("summary", "ok"),
                    }
                    log(state, f"{sid} done: {result.get('summary', 'ok')}")
                    print(f"     ✓ {result.get('summary', 'ok')}")
                    if result.get("out"):
                        print(f"     📄 {result['out']}")
                    ran_any = True
                    save_state(state)
                except Exception as e:
                    log(state, f"{sid} FAILED: {e}")
                    save_state(state)
                    print(f"     ✗ FAILED: {e}")
                    print("\n  Agent stopped at a failing task. Fix and re-run.")
                    sys.exit(1)

    if not ran_any:
        print("\n  All auto tasks already complete ✓")

    print_gates(plan, state)


def print_status(plan, state):
    print("\n  📊 FREEBUFF-AGENTS STATUS")
    print("  " + "-" * 60)
    for track in plan["tracks"]:
        total = len(track["steps"])
        done = sum(1 for s in track["steps"] if state["done"].get(s["id"]))
        print(f"\n  {track['name']}")
        print(f"  {done}/{total} steps done")
        for step in track["steps"]:
            mark = "✓" if state["done"].get(step["id"]) else ("⏸" if step["type"] == "gate" else "○")
            print(f"   {mark} {step['id']}  {step['title']}")
    print()


def print_gates(plan, state):
    print("\n" + "=" * 66)
    print("  👤 HUMAN GATE QUEUE — do these in order")
    print("  (run `python3 run_agent.py` again after each one to refresh)")
    print("=" * 66)
    pending = 0
    for track in plan["tracks"]:
        for step in track["steps"]:
            if step["type"] == "gate" and not state["done"].get(step["id"]):
                pending += 1
                print(f"\n  ⛔ GATE {step['id'].upper()}  [{step['kind']}]")
                print(f"  {step['title']}")
                print(f"  → {step['instructions']}")
                print(f"  Done when: {step['done_when']}")
    if pending == 0:
        print("\n  🎉 All gates complete. You have a client pipeline!")
    print("\n  Re-run:  python3 ~/freebuff-agents/run_agent.py")
    print("=" * 66)


if __name__ == "__main__":
    main()

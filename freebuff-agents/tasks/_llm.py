"""LLM access for freebuff-agents tasks.

Routing order:
  1. OmniRoute gateway (localhost:20128) — 14 providers, auto-fallback, free tiers
  2. Direct Gemini (GOOGLE_API_KEY from ~/ai_company/.env) — free tier fallback
"""
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

OMNIROUTE_URL = "http://localhost:20128/v1/chat/completions"
OMNIROUTE_MODELS = ["openrouter/google/gemini-2.5-flash", "openrouter/google/gemini-2.0-flash"]


def load_env():
    env = {}
    env_file = Path.home() / "ai_company" / ".env"
    if env_file.exists():
        for ln in env_file.read_text().splitlines():
            if "=" in ln and not ln.strip().startswith("#"):
                k, _, v = ln.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def call_omniroute(prompt, model=None):
    """Call through the OmniRoute gateway. Returns text. Raises on failure."""
    last = None
    for m in (model, *OMNIROUTE_MODELS):
        if not m:
            continue
        body = json.dumps({
            "model": m,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
            "stream": False,
        }).encode()
        req = urllib.request.Request(OMNIROUTE_URL, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode())
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
            last = f"no choices in response: {str(data)[:120]}"
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:150]}"
        except Exception as e:
            last = str(e)
    raise RuntimeError(f"OmniRoute failed: {last}")


def call_gemini(prompt, key):
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data["candidates"][0]["content"]["parts"][0]["text"]


def ask(prompt, want_json_array=False):
    """Best-available LLM call. Returns text (or parsed JSON array)."""
    # 1. OmniRoute (local, free, multi-provider)
    try:
        text = call_omniroute(prompt)
        return _finalize(text, want_json_array), "omniroute"
    except Exception as e:
        print(f"     omniroute failed ({e}); trying direct Gemini...")

    # 2. Direct Gemini
    env = load_env()
    key = env.get("GOOGLE_API_KEY", "")
    if key:
        try:
            text = call_gemini(prompt, key)
            return _finalize(text, want_json_array), "gemini"
        except Exception as e:
            print(f"     gemini failed ({e})")
    raise RuntimeError("no LLM available (OmniRoute + Gemini both failed)")


def _finalize(text, want_json_array):
    if want_json_array:
        m = re.search(r"\[[\s\S]*\]", text)
        if not m:
            raise ValueError("LLM did not return a JSON array")
        return json.loads(m.group(0))
    return text

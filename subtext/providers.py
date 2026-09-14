"""Pluggable LLM backends, so extraction isn't tied to a paid account.

The extraction step needs one thing: given a system prompt and a transcript,
return JSON matching a schema. Several providers do that on a free tier, so the
provider is chosen from whichever key is present in the environment.

Anthropic goes through its official SDK. The rest are plain HTTPS calls — both
API shapes are two fields wide, and adding SDK dependencies to a prototype that
has to run on a borrowed laptop isn't worth it.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

import requests

TIMEOUT = 180


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class Provider:
    name: str
    env_key: str
    default_model: str
    base_url: str = ""
    note: str = ""

    @property
    def key(self) -> str | None:
        return os.getenv(self.env_key)


# Order matters: the first one with a key present wins. Free tiers first, so a
# borrowed ANTHROPIC key never gets spent by accident.
PROVIDERS = [
    Provider("gemini", "GEMINI_API_KEY", "gemini-2.0-flash",
             "https://generativelanguage.googleapis.com/v1beta",
             "Google AI Studio — free tier, no card required"),
    Provider("groq", "GROQ_API_KEY", "llama-3.3-70b-versatile",
             "https://api.groq.com/openai/v1",
             "Groq — free tier, very fast"),
    Provider("openrouter", "OPENROUTER_API_KEY", "meta-llama/llama-3.3-70b-instruct:free",
             "https://openrouter.ai/api/v1",
             "OpenRouter — models with a :free suffix cost nothing"),
    Provider("github", "GITHUB_MODELS_TOKEN", "openai/gpt-4o-mini",
             "https://models.github.ai/inference",
             "GitHub Models — free with a GitHub PAT"),
    Provider("anthropic", "ANTHROPIC_API_KEY", "claude-opus-5",
             note="Anthropic — paid, best quality"),
]

BY_NAME = {p.name: p for p in PROVIDERS}


def detect() -> Provider:
    forced = os.getenv("SUBTEXT_PROVIDER", "").strip().lower()
    if forced:
        if forced not in BY_NAME:
            raise ProviderError(
                f"SUBTEXT_PROVIDER={forced!r} is not one of {sorted(BY_NAME)}")
        p = BY_NAME[forced]
        if not p.key:
            raise ProviderError(f"{p.name} selected but {p.env_key} is not set.")
        return p

    for p in PROVIDERS:
        if p.key:
            return p

    raise ProviderError(
        "No LLM provider configured. Set one of these in .env:\n"
        + "\n".join(f"    {p.env_key:<22} {p.note}" for p in PROVIDERS)
    )


def model_for(p: Provider) -> str:
    return os.getenv("SUBTEXT_MODEL", "").strip() or p.default_model


# --------------------------------------------------------------- JSON helpers

def _loads(text: str) -> dict:
    """Parse JSON that may arrive wrapped in prose or a markdown fence."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    raise ProviderError(f"Model did not return JSON. Got: {text[:200]!r}")


# ------------------------------------------------------------------ providers

def _call_gemini(p: Provider, model: str, system: str, user: str) -> str:
    url = f"{p.base_url}/models/{model}:generateContent"
    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"responseMimeType": "application/json",
                             "temperature": 0},
    }
    r = requests.post(url, json=body, timeout=TIMEOUT,
                      headers={"x-goog-api-key": p.key,
                               "Content-Type": "application/json"})
    if r.status_code == 404:
        raise ProviderError(
            f"Gemini model {model!r} not found. Run `python -m subtext providers` "
            f"to list the models your key can use, then set SUBTEXT_MODEL.")
    if not r.ok:
        raise ProviderError(f"Gemini {r.status_code}: {r.text[:300]}")
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise ProviderError(f"Unexpected Gemini response: {str(data)[:300]}") from e


def _call_openai_compatible(p: Provider, model: str, system: str, user: str) -> str:
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    r = requests.post(f"{p.base_url}/chat/completions", json=body, timeout=TIMEOUT,
                      headers={"Authorization": f"Bearer {p.key}",
                               "Content-Type": "application/json"})
    if not r.ok:
        # Not every free model supports JSON mode; retry once without it.
        if r.status_code in (400, 422) and "response_format" in body:
            body.pop("response_format")
            r = requests.post(f"{p.base_url}/chat/completions", json=body,
                              timeout=TIMEOUT,
                              headers={"Authorization": f"Bearer {p.key}",
                                       "Content-Type": "application/json"})
    if not r.ok:
        raise ProviderError(f"{p.name} {r.status_code}: {r.text[:300]}")
    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise ProviderError(f"Unexpected {p.name} response: {str(data)[:300]}") from e


def _call_anthropic(model: str, system: str, user: str, schema_model) -> dict:
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=model, max_tokens=16000, system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema_model,
    )
    return response.parsed_output.model_dump()


# ---------------------------------------------------------------- public call

def complete_json(system: str, user: str, schema_model) -> dict:
    """Run the extraction on whichever provider is configured."""
    p = detect()
    model = model_for(p)

    if p.name == "anthropic":
        return _call_anthropic(model, system, user, schema_model)

    # Everything else gets the schema in the prompt and is validated by the
    # caller. Free-tier models vary in how well they honour JSON mode, so the
    # schema is stated explicitly rather than assumed.
    schema = json.dumps(schema_model.model_json_schema(), indent=2)
    system_with_schema = (
        f"{system}\n\nReturn ONLY a JSON object matching this schema. "
        f"No prose, no markdown fence.\n\n{schema}"
    )
    caller = _call_gemini if p.name == "gemini" else _call_openai_compatible
    args = (p, model, system_with_schema, user)
    raw = caller(*args)
    try:
        return _loads(raw)
    except (ProviderError, json.JSONDecodeError):
        # One retry with a blunter instruction — cheap, and free models often
        # get it right the second time.
        raw = caller(p, model, system_with_schema + "\n\nOutput valid JSON only.", user)
        return _loads(raw)


def available_models(p: Provider) -> list[str]:
    """Ask the provider what this key can actually use."""
    if p.name == "gemini":
        r = requests.get(f"{p.base_url}/models", timeout=30,
                         headers={"x-goog-api-key": p.key})
        if not r.ok:
            raise ProviderError(f"Gemini {r.status_code}: {r.text[:200]}")
        return [m["name"].removeprefix("models/")
                for m in r.json().get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", [])]
    if p.name == "anthropic":
        import anthropic
        return [m.id for m in anthropic.Anthropic().models.list()]
    r = requests.get(f"{p.base_url}/models", timeout=30,
                     headers={"Authorization": f"Bearer {p.key}"})
    if not r.ok:
        raise ProviderError(f"{p.name} {r.status_code}: {r.text[:200]}")
    return [m.get("id", "") for m in r.json().get("data", [])]

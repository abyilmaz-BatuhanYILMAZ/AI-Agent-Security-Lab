"""Validated, versioned synthetic attack and control cases."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ACTIONS = frozenset({"answer", "send_email", "read_secret", "write_note"})
FAMILIES = frozenset({
    "indirect_prompt_injection", "rag_poisoning", "tool_output_injection",
    "memory_poisoning", "control",
})
SURFACES = frozenset({"retrieved_document", "search_result", "tool_response"})
_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,63}$")


@dataclass(frozen=True)
class Grant:
    action: str
    target: str


@dataclass(frozen=True)
class Case:
    id: str
    family: str
    label: str
    surface: str
    user_task: str
    source_text: str
    goal: Grant
    allowed: tuple[Grant, ...]


def _grant(raw: object) -> Grant:
    if not isinstance(raw, dict) or set(raw) != {"action", "target"}:
        raise ValueError("grant must contain exactly 'action' and 'target'")
    action, target = raw["action"], raw["target"]
    if action not in ACTIONS or not isinstance(target, str) or len(target) > 120:
        raise ValueError("invalid grant action/target")
    if action == "answer" and target != "":
        raise ValueError("answer action requires an empty target")
    if action != "answer" and not target:
        raise ValueError("non-answer action requires a target")
    if action == "send_email" and not target.endswith(".invalid"):
        raise ValueError("email recipients must use reserved .invalid domains")
    if action == "read_secret" and target != "synthetic_canary":
        raise ValueError("only the synthetic canary is available in this lab")
    if action == "write_note" and not re.fullmatch(r"[a-z0-9-]{1,40}", target):
        raise ValueError("note target must be a short synthetic key")
    return Grant(action=action, target=target)


def load_cases(path: str | Path) -> list[Case]:
    """Fail closed on ambiguous or malformed fixtures."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"version", "cases"} or raw["version"] != "1.0":
        raise ValueError("dataset must contain version '1.0' and cases")
    if not isinstance(raw["cases"], list) or not raw["cases"]:
        raise ValueError("dataset must contain a nonempty list of cases")
    cases: list[Case] = []
    seen: set[str] = set()
    required = {"id", "family", "label", "surface", "user_task", "source_text", "goal", "allowed"}
    for item in raw["cases"]:
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("each case must contain exactly the expected fields")
        id_ = item["id"]
        if not isinstance(id_, str) or not _ID_PATTERN.fullmatch(id_) or id_ in seen:
            raise ValueError(f"invalid or duplicate case ID: {id_!r}")
        seen.add(id_)
        family, label, surface = item["family"], item["label"], item["surface"]
        if family not in FAMILIES or label not in {"attack", "control"} or surface not in SURFACES:
            raise ValueError(f"invalid case classification: {id_}")
        if (label == "control") != (family == "control"):
            raise ValueError(f"control label/family mismatch: {id_}")
        for key in ("user_task", "source_text"):
            value = item[key]
            if not isinstance(value, str) or not value.strip() or len(value) > 4000:
                raise ValueError(f"missing or oversized {key}: {id_}")
        goal = _grant(item["goal"])
        if not isinstance(item["allowed"], list) or len(item["allowed"]) > 5:
            raise ValueError(f"invalid allowlist: {id_}")
        allowed = tuple(_grant(entry) for entry in item["allowed"])
        if len(set(allowed)) != len(allowed):
            raise ValueError(f"duplicate grants: {id_}")
        if any(grant.action == "read_secret" for grant in allowed):
            raise ValueError("the synthetic canary may never be authorized")
        if label == "attack" and (goal in allowed or goal.action == "answer"):
            raise ValueError(f"attack goal must be an unauthorized side effect: {id_}")
        if label == "control" and goal.action != "answer" and goal not in allowed:
            raise ValueError(f"control action must have an explicit grant: {id_}")
        cases.append(Case(
            id=id_, family=family, label=label, surface=surface,
            user_task=item["user_task"], source_text=item["source_text"],
            goal=goal, allowed=allowed,
        ))
    return cases

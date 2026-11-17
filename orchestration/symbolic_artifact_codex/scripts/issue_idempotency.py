#!/usr/bin/env python3
"""Pure idempotency planner for reviewed GitHub issue batches."""

import re
from collections import defaultdict

MARKER_RE = re.compile(r"<!--\s*gaia-canonical-issue-id:([A-Z0-9_-]+)\s*-->")


class IntegrityError(RuntimeError):
    """Raised when canonical identity cannot be resolved safely."""


def plan_actions(payload, existing_issues):
    """Return CREATE/SKIP actions without performing external mutations.

    Rules:
      * duplicate canonical ID in payload -> fail closed
      * duplicate canonical ID in repository -> fail closed
      * matching canonical ID -> SKIP, regardless of mutable title
      * matching title without matching canonical marker -> fail closed
      * otherwise -> CREATE
    """
    seen_payload = set()
    for item in payload:
        issue_id = str(item.get("issue_id", "")).strip()
        if not issue_id:
            raise IntegrityError("payload item missing issue_id")
        if issue_id in seen_payload:
            raise IntegrityError(f"duplicate canonical issue_id in payload: {issue_id}")
        seen_payload.add(issue_id)

    by_id = {}
    by_title = defaultdict(list)
    for issue in existing_issues:
        title = str(issue.get("title", "")).strip()
        by_title[title].append(issue)
        match = MARKER_RE.search(str(issue.get("body", "") or ""))
        if match:
            issue_id = match.group(1)
            if issue_id in by_id:
                raise IntegrityError(f"duplicate canonical issue_id in repository: {issue_id}")
            by_id[issue_id] = issue

    actions = []
    for item in payload:
        issue_id = str(item["issue_id"]).strip()
        title = str(item.get("title", "")).strip()

        if issue_id in by_id:
            existing = by_id[issue_id]
            actions.append({
                "action": "SKIP",
                "issue_id": issue_id,
                "issue_number": existing.get("number"),
                "existing_title": existing.get("title"),
            })
            continue

        collisions = by_title.get(title, [])
        if collisions:
            numbers = ",".join(str(i.get("number")) for i in collisions)
            raise IntegrityError(
                f"title collision without matching canonical marker for {issue_id}: {numbers}"
            )

        actions.append({
            "action": "CREATE",
            "issue_id": issue_id,
            "issue_number": None,
        })

    return actions

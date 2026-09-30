# Proposed maintenance tasks

## 1) Typo fix task
**Task:** Fix the profile README typo by replacing `I’m interested in ...` with a complete sentence that does not include placeholder ellipses, and ensure punctuation is consistent across all bullet items.

**Issue found:** The current bullets are template placeholders and read as unfinished content, which creates an appearance similar to copy/template mistakes in user-facing text.

**Acceptance criteria:**
- The `👀` line is rewritten as a complete sentence.
- Ellipses placeholders are removed from all bullets.
- All bullets end with consistent punctuation style.

## 2) Bug fix task
**Task:** Resolve malformed profile rendering caused by committing unresolved GitHub profile template placeholders.

**Issue found:** The README acts as the public profile page content, but all seven visible bullets are unresolved placeholders, so production output is functionally incorrect (profile information is missing).

**Acceptance criteria:**
- Every profile bullet contains real content (not `...`).
- Profile preview renders meaningful metadata for interests, learning, collaboration, contact, pronouns, and fun fact.
- A reviewer can confirm no placeholder token remains.

## 3) Comment/documentation discrepancy task
**Task:** Align the HTML comment block with current repository intent and ownership details.

**Issue found:** The HTML comment states this is a “special repository because its README appears on your GitHub profile,” but the visible content is not maintained to match that purpose. Documentation intent and actual content diverge.

**Acceptance criteria:**
- Comment is either updated to include maintenance guidance (e.g., “Keep this profile README up to date”) or removed.
- README top section clearly states purpose and update expectations.
- No contradictory statements remain between comment and visible content.

## 4) Test improvement task
**Task:** Add a CI check that fails when README contains unresolved template placeholders.

**Issue found:** There is no automated guardrail preventing regressions to `...` placeholders in profile text.

**Acceptance criteria:**
- Add a workflow (or script + workflow) that scans `README.md` for placeholder patterns such as `...` in profile bullets.
- CI fails on detection and passes when placeholders are replaced.
- Include a brief contributor note describing how to run the check locally.

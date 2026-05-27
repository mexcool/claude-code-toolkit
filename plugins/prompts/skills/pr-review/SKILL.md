---
name: pr-review
description: Principal-engineer review of a PR with cross-repo, cross-PR context — not just diff-mechanical. Use when the user asks to review a PR holistically, wears the "principal engineer hat", or wants real issues over nitpicks.
---

# PR Review

The user gave you a PR (URL or number). Do a principal-engineer review, not a diff-mechanical one.

## Steps

1. **Fetch the PR**: `gh pr view <ref>` and `gh pr diff <ref>`. Read the description and the diff in full.
2. **Map the ecosystem**: follow every linked ticket, referenced PR, and mentioned repo. Read them. Many PRs only make sense as one node in a wider initiative — find that initiative.
3. **Read surrounding code**: not just the changed lines. Understand the module the diff lives in, its callers, and the conventions it follows.
4. **Review with principal-engineer hat**:
   - Real issues only: correctness, design, integration, missed cases, hidden coupling, wrong abstraction level.
   - **No nitpicks**: no style, no naming preferences, no "you could also..." that adds nothing.
   - Flag over-engineering aggressively — in both the PR *and* any fix you propose. The simplest correct change wins.
5. **Summarize** in the chat:
   - What the PR does and where it fits in the wider work.
   - Issues, severity-ranked. For each: what's wrong, why it matters, the minimum change to fix it.
   - What's good (briefly — don't pad).

Do not post comments to GitHub unless the user explicitly asks.

---
name: deeper
description: A deeper version of the current task, not a bigger one. Start from raw evidence, use the instruments the best engineer in the field would use, and prove the result with a check other than your own judgement.
disable-model-invocation: true
---

# Deeper, not bigger

Apply this to the task the user names, or to the current one. Depth goes into the evidence and the proof, never into the size of the change.

Answer briefly, then do it:

1. **What would the best engineer in this field do here that wasn't asked?** Count checks and methods, not features.
2. **Rawest evidence**: the data, logs, a real run or request; not the schema, a summary or your earlier reading. Reproduce the problem or measure the current state from it. If you can't reach it, say what access is missing instead of reasoning around it.
3. **Instruments**: the tools they would use, such as a query on the real data, EXPLAIN, a profiler, a load test, the real dependency instead of a mock. New words with the same method is not depth.
4. **Outside judge**: what, other than you or the user, shows it is right: a command, a query or a diff of outputs, run on main and on the branch. Don't grade your own work.

Treat what "we know" as a claim to reproduce: the diagnosis, an accepted risk, an edge case called impossible. Set a high bar for proof: all the history you can reach, not three examples. Report what the evidence showed, especially where it contradicts the plan.

---
name: range
description: Look at the current task through the other fields it touches. Restate it as a verb, find the fields that deal with that verb every day, and run the one check each would run. Methods, not role-play.
disable-model-invocation: true
---

# Range

Apply this to the task the user names, or to the current one.

1. **Verb, not noun**: restate what the work does, for whom, as a verb. Not "a dashboard" but "let the on-call engineer spot a stuck pipeline in five seconds".
2. **Fields**: name the two or three fields beyond your own that deal with that verb every day. Skip any whose check would not change the result.
3. **One check each**: the method that field would apply here. Run it where you can. Common ones:

| If the work… | Borrow |
|---|---|
| pages someone at night | replay history and count how often it would fire; test the route end to end |
| shares a limited resource | worst-case concurrency against the real limit; a load test |
| makes numbers people decide on | reconcile with an independent source; the parts sum to the whole; diff per key |
| ranks or scores people | small-sample noise, survivorship; how would someone game it? |
| changes a contract others read | list every consumer and check each one |
| costs money per run | cost per run, before and after |
| runs unattended | rerun it, kill it halfway: what happens? |
| tells a user something | one row per failure: what they see, what they do next |

Do what the field does; don't write as it ("as an SRE, I think…"). Report each field, its check, what it found and whether it changes the plan. A check that finds nothing is a valid result. A finding that needs new scope is a question for the user.

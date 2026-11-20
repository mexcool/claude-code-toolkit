-- mux.sh's agent calls under Rex: rex do -s SESSION -b BLOCK agent.lua --args JSON
-- State is the status the agent reports itself (OSC 7501): the block's root record. Events queue
-- from the moment the script starts, so a check followed by rex.wait misses nothing, however short.
--   {"ready": APP, "timeout": N}           wait until APP is idle or done, then quiet for 2 s
--   {"text": TEXT, "timeout": N}           submit TEXT; if N > 0, wait until the turn it starts ends
--   {"wait": "working"|"settled", "timeout": N}
-- Prints the agent's status record. Exit 1: no agent, busy, blocked, or no turn started. Exit 2: timed out.
local T, block, a = "com.superlogical.terminal", rex.block_id, rex.args
local deadline = os.time() + (a.timeout or 0)

local function finish(r, code, why)
  if why then io.stderr:write("mux: " .. why .. "\n") end
  print(rex.json.encode(r))
  rex.stop(code or 0)
end
local function root()
  local res, err = rex.block.call(T, "program_status", {})
  if not res then finish({}, 1, err) end
  for _, r in ipairs(res.records) do
    if r.id == nil then return r end
  end
  return {}
end
local function left() return math.max(deadline - os.time(), 1) end
local function settled(r) return r.state ~= nil and r.state ~= "working" end
local function working(r) return r.state == "working" end
local function any() return true end
-- Rex keeps the last report after the agent exits. The agent is alive while the process that
-- sent report `r` is still the terminal's foreground process.
local function alive(r)
  local p, o = rex.block.call(T, "process", {}), r.owner
  local f = p and p.foreground
  return f ~= nil and o ~= nil and f.pid == o.pid and f.name == o.name
end
-- The next report from this block's agent that `want` accepts, or nil after `secs`. Every 30 s
-- it checks that the agent that sent `r` is still running.
local function next_report(want, secs, r)
  local stop = os.time() + secs
  repeat
    local ev = rex.wait("terminal.program_status_changed", function(ev, ctx)
      return ctx.block_id == block and ev.record.id == nil and want(ev.record)
    end, math.max(math.min(30, stop - os.time()), 1))
    if ev then return ev.record end
    if r.owner and not alive(r) then finish(r, 1, "no agent running in this pane") end
  until os.time() >= stop
end

local r = root()

if a.ready then -- Codex reports idle and working a few times while it starts
  while os.time() < deadline do
    if (r.state == "idle" or r.state == "done") and r.app == a.ready then
      r = next_report(any, 2, r) or finish(r)
    else
      r = next_report(any, left(), r) or r
    end
  end
  finish(r, 2, "no ready " .. a.ready .. " agent")
end

if a.text then
  -- Typed into a bare shell, the text would run as commands.
  if not alive(r) then finish(r, 1, "no agent running in this pane") end
  if r.state == "working" or r.state == "blocked" then finish(r, 1, "busy") end
  -- A paste, then Enter on its own: Codex reads keys typed fast with Enter as one pasted block.
  rex.call("block.event", { session_id = rex.session_id, block_id = block,
    event = { type = "paste", payload = { text = a.text } } })
  rex.sleep(0.1)
  rex.block.call(T, "write", { data = "\r" })
  if (a.timeout or 0) == 0 then finish(r) end
  -- Wait for `working` first: a late report from the last turn (Claude sends `done` twice) is not this turn's end.
  r = next_report(working, 5, r) or finish(root(), 1, "no turn started within 5 s")
  r = next_report(settled, left(), r) or finish(root(), 2, "timed out")
  finish(r)
end

local want = a.wait == "working" and working or settled
if not want(r) then r = next_report(want, left(), r) or finish(root(), 2, "timed out") end
finish(r)

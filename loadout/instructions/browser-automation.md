## Browser Automation

When a task needs a real browser — driving the running app to verify a UI change, filling a form, reproducing a click-path, grabbing a screenshot — use the **`agent-browser`** CLI (installed machine-wide, on `PATH`). It is built for agents: text-first output, low token cost, and an accessibility-tree snapshot with stable refs instead of brittle CSS selectors.

**Start here**: run `agent-browser skills get core --full` once per session for the full command reference and workflow patterns. Prefer that over guessing flags. Specialized skills exist too (`agent-browser skills list`).

**Core loop**:
- `agent-browser open <url>` — navigate (a `localhost` dev server is the common case).
- `agent-browser snapshot` — accessibility tree with refs like `@e1`, `@e2`. Use those refs to target elements.
- `agent-browser click @e2` / `type @e3 <text>` / `fill @e3 <text>` / `get text @e1` / `get url` — interact and read state.
- `agent-browser screenshot <path>` — save a PNG (then read it to see the page).
- `agent-browser close` — end the session.

The session is **stateful and persists across invocations** until `close`, so each command above is its own shell call against the same live browser. Reach for this whenever the page needs JS execution, interaction, or auth you already have in a logged-in session — plain read-only fetching of static external pages does not need a browser.

### The agent browser: for sites that block agents

`agent-chromium` is a dedicated Chromium with its own profile (`~/.agent-chromium`) that the user logs into by hand, exposing CDP on `localhost:9222`. Agents attach to it rather than launching a browser, so it carries the user's real logins and none of the launch-time automation flags. Verified 2026-10-10: a logged-in Reddit thread loads in full through it, including from inside the nono sandbox, where the same site blocks an `agent-browser`-launched Chrome.

**When to use it**: after a direct fetch, `jina-fetch` and `jina-fetch --proxy` have all hit a block, CAPTCHA or login wall, or when the content only exists behind the user's login. It is not a default for ordinary pages.

**Check it first**: `agent-chromium status` exits 0 and lists open tabs when it is up. If it is down, an unsandboxed session runs `agent-chromium start`; a sandboxed one cannot (it exits 78), so ask the user to run `agent-chromium start` in their own terminal — not as a `!` command, which runs inside the same sandbox.

**Attach, never launch**:

```sh
agent-browser --cdp 9222 --session <task-name> --pin-tab open <url>
agent-browser --cdp 9222 --session <task-name> --pin-tab get text body
agent-browser --cdp 9222 --session <task-name> --pin-tab tab close   # when done
```

`--pin-tab` gives each session its own tab, so parallel agents do not steer each other's pages. `agent-browser --session <name> close` detaches and leaves the browser running; never `close --all`, `agent-chromium stop`, or kill it — the user may be mid-login in it. Never pass `--profile ~/.agent-chromium`: two instances cannot share a profile, and the sandbox cannot write it.

**It is the user's real account.** Read only: do not post, comment, vote, message, follow, subscribe, accept terms or change settings unless the user asked for that specific action. Keep a human pace — a handful of pages, not a crawl — since a flagged account is the user's loss.

**When a page wants a human** — a challenge ("Just a moment…", "Prove your humanity", "Verify you are human"), a login form, or a sign-up wall — stop and hand it to the user; never attempt a CAPTCHA, type a password, or fill a sign-up form yourself. Run `agent-chromium show <site>` to bring that tab forward (from a sandbox it switches the tab but cannot raise the window), then ask in one line, naming the site and tab title:

- **Challenge**: "The agent browser has a <site> check open (tab "<title>") — solve it and tell me when done."
- **Login wall** on a site the user plausibly has an account on: "<site> needs a login — log in in the agent browser window and tell me."
- **Account required** and the user likely has none: ask whether they want to create one; say what the content is and offer the alternative (a proxy fetch, a different source) in the same message.
- **Hard block** ("blocked by network security", "access denied") that survives the user's login: stop retrying, report it, and fall back to `jina-fetch --proxy` or another source.

After the user confirms, reload once and continue.

**Getting the content out cheaply.** Never screenshot to read text, and never dump `snapshot` to read a page: on a Reddit thread `snapshot -i -c` was 62k chars against 17k for the page text. In order of preference:

1. **The site's own JSON**, fetched from inside the page so the login cookies apply, filtered down to the fields you need in the same `eval`. Reddit serves any URL as JSON with `.json` appended:
   `agent-browser --cdp 9222 --session s --pin-tab eval 'fetch(location.pathname.replace(/\/$/,"")+".json?limit=20").then(r=>r.json()).then(j=>JSON.stringify(j[1].data.children.map(c=>[c.data.score,c.data.body?.slice(0,300)])))'`
2. **A targeted element**: `get text <selector>` (or a ref from `snapshot -i`) when you know where the answer sits.
3. **A question about a long page**: pipe the text through `distill`, which answers from the whole page and keeps it out of your context:
   `agent-browser --cdp 9222 --session s --pin-tab get text body | tee "$TMPDIR/<name>.txt" | distill "<specific question>; quote the decisive sentences verbatim"`
   The `jina-fetch` rules apply: `NO_RELEVANT_CONTENT` is a real negative, never ask it to count, and `grep` the saved copy before quoting. Delete the copy when done.
4. **`snapshot -i -c`** only to find refs for clicking or typing, and **screenshots** only when the question is visual or you need to show the user something.

`distill` sends the text to OpenRouter. Never pipe private logged-in pages through it — inbox, messages, account or billing pages, anything with the user's personal data. Read those with a targeted `get text` or `eval` instead.

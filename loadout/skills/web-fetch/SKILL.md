---
name: web-fetch
description: Escalation ladder and failure signatures for fetching web pages on this machine — jina-fetch, its --proxy rung, the user's logged-in agent-chromium browser, multi-page reads, verbatim quotes from the cached page, and the hosts that need a specific route. Use when a fetch fails, is refused, truncates or comes back as nav/boilerplate; when exact text or a quote from a page matters; before fetching Reddit, a shop or price page, or a paywalled or bot-protected site; or before any agent-chromium command, a bot check, or content behind the user's login.
---

# Fetching web pages

The global instructions carry the defaults: the Jina MCP for search, `gh` for GitHub, the direct
fetch first, `jina-fetch` when it fails or the page is long-form. This skill is the rest.

## jina-fetch

`jina-fetch <url> "<what to extract>"` fetches through Jina, caches the full page under `TMPDIR`,
and returns only the extract — a 200k-char page never reaches your context. Ask a specific
question rather than "summarize"; re-running against the same URL is cheap because the page is
cached.

**When exact text matters** — code, config, a quoted claim — don't trust the extract, which can
paraphrase while looking like a quote. Ask instead for short verbatim anchor phrases, then `grep`
or read the cached file to pull just those lines into context. `jina-fetch` prints each page's
exact cache path and title on stderr; use that path — never "the newest file in the cache
directory", which is wrong whenever another fetch is in flight. Repeat questions against the same
URL are cache hits, so several targeted passes cost far less than one `--raw` dump.

**`NO_RELEVANT_CONTENT` means the page does not address your question.** Treat it as a real
answer — a negative result — not as a failed call. Do not re-ask the same page in different words
hoping for a hit, and never record an unrelated quote from it as evidence. `jina-fetch` also warns
when none of the question's key terms appear on the page.

**Never ask it to count or enumerate** occurrences across a page ("how many tables/sections/
matches") — models get this wrong on long documents. `grep -c` the cached file instead.

**Reading several pages**: `jina-fetch <url> <url> <url> "<what to extract>"` fetches them in
parallel and extracts each separately. Add `--combined` for one extraction across all of them when
the question spans sources ("which of these disagree?"). Use this instead of the Jina MCP's
parallel-read tool, which dumps every page into the conversation at once.

Other flags: `--raw` prints whole pages, `--out PATH` saves them, `--model` picks a different
OpenRouter model, `--help` covers the rest. Prefer `jina-fetch` over the MCP `read_url` tool
generally; reach for the MCP tools only for Jina's other capabilities (screenshots, PDF
figure/table extraction, text classification).

**Auth** is injected automatically by the sops-wrapped launcher; you do not need to know or fetch
the token.

## Recognising a failed fetch

::: claude
`WebFetch` fails in five ways, and only the first two announce themselves:

1. `"Claude Code is unable to fetch from X"` — refused, never sent
2. HTTP 402/403 from the origin
3. Returns instructions to re-call instead of following a cross-host redirect
4. HTTP 200 with nav/chrome only and the article body missing
5. Truncates a long page and answers from the prefix — sometimes flagged as
   `[Content truncated due to length...]`, sometimes just a confidently incomplete answer

On the Kubernetes Deployment page it refused the question outright, reporting
`[Content truncated due to length...]`, while `jina-fetch` answered it correctly from the full
page.
:::
::: codex opencode pi
A fetch has failed when any of these happen:

- refused by a deny-list or robots rule, never sent
- HTTP 402/403 from the origin
- a cross-host redirect not followed
- HTTP 200 with nav/chrome only and the article body missing
- a summarising fetch tool truncated a large page and answered from the prefix, sometimes
  flagged, sometimes just a confidently incomplete answer
:::

If the result is boilerplate without the content you asked for, that is a failure — escalate,
don't report it as the page. If an answer mentions truncation, or reads like it stopped before the
section you asked about, re-fetch with `jina-fetch` rather than accepting it.

**Some hosts defeat both paths.** `jina-fetch` warns when a page comes back near-empty — treat
that as unreachable rather than retrying: use `gh`, `glab`, or a project-specific CLI, or tell the
user.

Jina does not bypass paywalls — expect the same free prefix, with no marker where it stopped.

## The escalation ladder

1. The direct fetch.
2. `jina-fetch`.
3. **`jina-fetch --proxy`** when a host blocks Jina. That routes through Jina's rotating
   residential pool (`X-Proxy: auto`), which is on the current key and handles common anti-bot
   challenges. `jina-fetch` hints at this itself whenever a page comes back blocked.
   `--proxy-country de` pins a country but needs the paid Proxy allocation tier and returns HTTP
   402 without it, so only reach for it if the geo actually matters. Proxied requests likely bill
   more than plain ones, so keep `--proxy` an escalation rather than a default.
4. **The logged-in agent browser** (`agent-chromium`, below) when
   `--proxy` is blocked too, or the content sits behind a login.

## Hosts with a known route

**Split by page type, not by length alone.** Use the direct fetch first for anything
**transactional** (shop listings, prices, stock, shipping, delivery estimates): those pages are
short enough that truncation is no risk, and a direct fetch runs on this machine's German IP while
Jina exits in the US. Go straight to `jina-fetch` for **long-form reading** (reviews, docs,
articles, roundups), where truncation is the real risk and geography is irrelevant. Length alone
is a weak signal, because in a research-heavy session almost every page is long and the exception
quietly eats the stated default.

Real case, 2026-08-22: `thomannmusic.com` fetched through Jina returned a price in USD, which got
misread as a Jina geolocation artifact and written into a doc as fact. The German domain
`thomann.de` returns EUR through Jina perfectly well. When a price looks foreign, check the domain
before blaming the tool.

**Stack Overflow**: straight to `jina-fetch`. It blocks ordinary fetching (in Claude Code,
`WebFetch` refuses it at the client, request never sent) and works through Jina, so don't waste
the failed call.

**Reddit: the agent browser when it is up, else `jina-fetch --proxy`.** Verified 2026-08-22: plain
Jina returns a "Prove your humanity" CAPTCHA; the direct fetch, raw curl from this machine (403),
`old.reddit.com` (302) and public redlib mirrors (403) all fail, and so does a Chrome that
`agent-browser` launches itself ("blocked by network security" after the JS challenge).
`jina-fetch --proxy <thread-url>` returns the full thread, post body and comments, ~50k chars. The
logged-in agent browser also works, verified 2026-10-10, and is free and gives Reddit's JSON. The
`.rss` endpoint also works but 429s on the very next request, so it is not a substitute.

## The logged-in agent browser

`agent-chromium` is a dedicated Chromium with its own profile (`~/.agent-chromium`) that the user logs into by hand, exposing CDP on `localhost:9222`. Agents attach to it rather than launching a browser, so it carries the user's real logins and none of the launch-time automation flags. Verified 2026-10-10: a logged-in Reddit thread loads in full through it, including from inside the nono sandbox, where the same site blocks an `agent-browser`-launched Chrome.

**When to use it**: after a direct fetch, `jina-fetch` and `jina-fetch --proxy` have all hit a block, CAPTCHA or login wall, or when the content only exists behind the user's login. It is not a default for ordinary pages.

**Check it first**: `agent-chromium status` exits 0 and lists open tabs when it is up. If it is down, an unsandboxed session runs `agent-chromium start`; a sandboxed one cannot (it exits 78), so ask the user to run `agent-chromium start` in their own terminal — not as a `!` command, which runs inside the same sandbox.

**Read with `agent-chromium read`; it never steals focus.** Any `agent-browser` command over `--cdp` raises the agent browser's window and takes keyboard focus from whatever the user is typing in (it activates the tab on open and switch; upstream issue vercel-labs/agent-browser#1247, unfixed as of 0.39.0). `read` opens the page in a background tab, waits for the load, prints one JavaScript expression's value, and closes the tab. Verified 2026-10-10: the frontmost app never changed across repeated reads.

```sh
agent-chromium read <url>                          # the page's text (document.body.innerText)
agent-chromium read <url> '<js expression>'        # promises are awaited; strings print raw, anything else as JSON
agent-chromium read <url> '<expr>' --keep          # leave the tab open, e.g. to hand a challenge to the user
agent-chromium close <tab-id>                     # close a kept tab
```

**Attach `agent-browser` only to click or type**, and warn the user in the same message that the window will come forward. Attach, never launch:

```sh
agent-browser --cdp 9222 --session <task-name> --pin-tab open <url>      # first command
agent-browser --cdp 9222 --session <task-name> --pin-tab snapshot -i -c
agent-browser --cdp 9222 --session <task-name> --pin-tab tab close       # when done
agent-browser --session <task-name> close                                # detach
```

`--pin-tab` gives each session its own tab, so parallel agents do not steer each other's pages. Use a fresh `<task-name>` for every task, and make `open` its first command: a pinned session creates its tab on attach, and `open` navigates that tab, while `tab new` adds a second one and leaves the first behind as a stray `about:blank` (vercel-labs/agent-browser#1986, unfixed as of 0.39.0). `open` again to move to another page. Once the bound tab is closed the session stays pinned to it and fails with `tab_gone`, which is why a session name is never reused. `agent-browser --session <name> close` detaches and leaves the browser running; never `close --all`, `agent-chromium stop`, or kill it — the user may be mid-login in it. Never pass `--profile ~/.agent-chromium`: two instances cannot share a profile, and the sandbox cannot write it.

**It is the user's real account.** Read only: do not post, comment, vote, message, follow, subscribe, accept terms or change settings unless the user asked for that specific action. Keep a human pace — a handful of pages, not a crawl — since a flagged account is the user's loss.

**Most bot checks clear on their own; wait, do not hand them off.** A Cloudflare "Just a moment…" page usually runs its check and reloads into the real page within a few seconds, with no clicks, and that works in a background tab too. Verified 2026-10-10 on thewoksoflife.com: with its `cf_clearance` cookie deleted, `read` took 8s instead of 2s, Cloudflare reissued the cookie, and the real page came back. `read` waits out pages titled like a challenge ("Just a moment…", "Checking your browser", "Verify you are human", "Prove your humanity") up to `--timeout` (default 30s). A challenge page that `read` returned without waiting is not evidence the site is blocked; re-read before concluding anything.

**When a page wants a human** — a check still showing after `read` times out (it exits 1 and names the challenge), one that asks for a click or a puzzle, a login form, or a sign-up wall — stop and hand it to the user; never attempt a CAPTCHA, type a password, or fill a sign-up form yourself. Re-run the `read` with `--keep` (or keep your `agent-browser` tab), then run `agent-chromium show <site>` to bring that tab forward (from a sandbox it switches the tab but cannot raise the window), then ask in one line, naming the site and tab title:

- **Challenge**: "The agent browser has a <site> check open (tab "<title>") — solve it and tell me when done."
- **Login wall** on a site the user plausibly has an account on: "<site> needs a login — log in in the agent browser window and tell me."
- **Account required** and the user likely has none: ask whether they want to create one; say what the content is and offer the alternative (a proxy fetch, a different source) in the same message.
- **Hard block** ("blocked by network security", "access denied") that survives the user's login: stop retrying, report it, and fall back to `jina-fetch --proxy` or another source.

After the user confirms, read the page again (a fresh `read` without `--keep`) and continue, then close the kept tab with `agent-chromium close <tab-id>`; `--keep` prints the id. `close` matches a tab id, URL or title and never raises the window, so close only tabs you opened.

**When the user is not at this machine's screen** (they reached it over SSH, or it is a headless box), the agent browser window is out of their reach, so add to the ask how to get there. CDP listens on loopback only, so they tunnel it from their own machine and drive the tab from local Chrome's remote inspector:

1. `ssh -N -L 9222:127.0.0.1:9222 <this-host>` (if their local 9222 is taken, forward `9223:127.0.0.1:9222` and use `localhost:9223` below)
2. In local Chrome, open `chrome://inspect/#devices`, under **Configure…** add `localhost:9222`, then click **inspect** under the tab named in the ask. The DevTools window shows a live, clickable view of that tab.

**When no one is in the conversation** — a scheduled job (`RUN_SESSION_ID` is set) or a `-p` run — there is nobody to hand a page to, so never stop and wait. Keep the same ladder: direct fetch, `jina-fetch`, `jina-fetch --proxy`, and only then the agent browser, starting it with `agent-chromium start` if `status` says it is down. When the browser in turn needs a human:

- Do not use `--keep`; leave no tab open.
- Challenge, login wall or missing account: if `~/notes/ai/runtime/notify.sh` exists, send one alert so the user can fix it for next time: `bash ~/notes/ai/runtime/notify.sh "🔔 ACTION: agent browser needs a <site> login/challenge — <url> (<job or task>)"`. Send it once per site per run, not once per page.
- Hard block: no alert; it is not something a login fixes.
- Either way, continue with whatever other sources you have, and name the blocked URL and the reason in your final result rather than presenting partial coverage as complete.

**Getting the content out cheaply.** Never screenshot to read text, and never dump `snapshot` to read a page: on a Reddit thread `snapshot -i -c` was 62k chars against 17k for the page text. In order of preference:

1. **The site's own JSON**, fetched from inside the page so the login cookies apply, filtered down to the fields you need in the same expression. Reddit serves any URL as JSON with `.json` appended:
   `agent-chromium read <thread-url> 'fetch(location.pathname.replace(/\/$/,"")+".json?limit=20").then(r=>r.json()).then(j=>j[1].data.children.map(c=>[c.data.score,c.data.body?.slice(0,300)]))'`
   Recipe pages carry their ingredients and steps verbatim as Recipe JSON-LD in `<script type="application/ld+json">`; read that rather than the page text when exact quantities matter.
2. **A targeted element**: `agent-chromium read <url> 'document.querySelector("<selector>").innerText'` when you know where the answer sits.
3. **A question about a long page**: pipe the text through `distill`, which answers from the whole page and keeps it out of your context:
   `agent-chromium read <url> | tee "$TMPDIR/<name>.txt" | distill "<specific question>; quote the decisive sentences verbatim"`
   The `jina-fetch` rules above apply: `NO_RELEVANT_CONTENT` is a real negative, never ask it to count, and `grep` the saved copy before quoting. Delete the copy when done.
4. **`snapshot -i -c`** only to find refs for clicking or typing, and **screenshots** only when the question is visual or you need to show the user something.

`distill` sends the text to OpenRouter. Never pipe private logged-in pages through it — inbox, messages, account or billing pages, anything with the user's personal data. Read those with a targeted `agent-chromium read` expression instead.

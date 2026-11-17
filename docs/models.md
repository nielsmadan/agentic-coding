# Models and providers

Which model each entry point runs, and which account pays for it. The files named
in the last column are the sources of truth; this page is a map of them. The
`agent-models` skill refreshes the OpenRouter ladders, the session tiers and the
extraction pair (see `.claude/skills/agent-models/references/`).

## Billing accounts

| Account | Credential | Pays for |
|---|---|---|
| Claude Max subscription | Claude Code login | `claude`, its tiers, `advisor-claude`, `cmdgen-claude` |
| Claude API credit from the Max plan | `ANTHROPIC_COUNT_TOKENS_KEY`, mapped to `ANTHROPIC_API_KEY` inside pi only | `picc` |
| ChatGPT subscription | Codex login, pi's `openai` login | `codex`, its tiers, `pix`, `advisor-codex`, `cmdgen-codex` |
| OpenRouter balance | `OPENROUTER_API_KEY` | pi's OpenRouter extras, OpenCode, `clor`, `ocs`, `advisor-opencode`, `cmdgen-opencode`, `jina-fetch`, `distill`, dev-phase on pi |
| Factory | `FACTORY_API_KEY` | `droid`, `advisor-droid` |
| Cursor subscription | Cursor login | `cursor-agent` / `agent` |
| Vercel Token Pass ($150/month, featured open-weight models only) | `AI_GATEWAY_API_KEY` (Token Pass–restricted) | plain `pi`, `advisor-pi` |

## Interactive sessions

| Entry point | Provider | Model (effort) | Source |
|---|---|---|---|
| `claude` | Anthropic subscription | `opus` (high; Fable xhigh) | `loadout/settings/claude.json` |
| `claude <tier>` | Anthropic subscription | low Haiku 5.5 (xhigh), mid Sonnet 5.5 (high), high Opus 5.5 (high), xhigh Fable 5.2 (medium), max Fable 5.2 (max) | `.airc.d/07-model-tiers.zsh` |
| `clor` | OpenRouter, through Claude Code | `/model haiku` GPT-6 Luna, `sonnet` Muse Ember (start, subagents), `opus` GPT-6.1 Sol | `.airc.d/claude.zsh` |
| `codex` | ChatGPT subscription | GPT-6 Astra (high) | `loadout/defaults/codex.json` |
| `codex <tier>`, `pix <tier>` | ChatGPT subscription | low/mid/high/xhigh GPT-6.1 Sol (low/medium/xhigh/max), max GPT-6 Astra (max) | `.airc.d/07-model-tiers.zsh` |
| `pix` | ChatGPT subscription | GPT-6 Astra (high) | `.airc.d/pi.zsh` |
| `pi` | Token Pass | DeepSeek V4.1 Flash (max) | `loadout/settings/pi.json` |
| `pi` `/model` | Token Pass | DeepSeek V4.1 Flash, Kimi K3.1 Pro | `loadout/settings/pi.json` `enabledModels` |
| `pi` `/model` | OpenRouter | GPT-6 Luna, Muse Ember, GPT-6.1 Sol | `loadout/settings/pi.json` `enabledModels` |
| `pi` `/model` | ChatGPT subscription | GPT-6 Astra, GPT-6 Luna, GPT-5.6 Terra, GPT-6 Sol | `loadout/settings/pi.json` `enabledModels` |
| `picc` | Anthropic API credit | Sonnet 5.5 (high) | `.airc.d/pi.zsh` |
| `opencode`, `oc` | OpenRouter | Muse Ember; GPT-6.1 Sol selectable | `loadout/settings/opencode.json` |
| `ocs` | OpenRouter | Kimi K3.1 Pro | `.airc.d/opencode.zsh` |
| `droid` | Factory | Gemini 4 Argon; favourites Opus 5.5, GPT-6.1 Sol | `loadout/settings/droid.json` |
| `cursor-agent haiku\|sonnet\|opus` | Cursor | Haiku 5.5 (thinking high), Sonnet 5.5 (medium), Opus 5.5 (high) | `.airc.d/cursor.zsh` |

## Headless calls

| Caller | Provider | Model (effort) | Source |
|---|---|---|---|
| `advisor-claude` (`/second-opinion`) | Anthropic subscription | Claude Code default (`opus`) | `pratfall/config.toml` |
| `advisor-codex` | ChatGPT subscription | Codex default (GPT-6 Astra, high) | `pratfall/config.toml` |
| `advisor-pi` | Token Pass | Kimi K3.1 Pro (max) | `pratfall/config.toml` |
| `advisor-opencode` | OpenRouter | Tencent HY4 (high) | `pratfall/config.toml` |
| `advisor-droid` | Factory | Gemini 4 Argon (high) | `pratfall/config.toml` |
| `ccli` | Anthropic subscription | `haiku` | `pratfall/config.toml` |
| `cxcli` | ChatGPT subscription | GPT-5.6 Luna (low) | `pratfall/config.toml` |
| `occli` | OpenRouter | GPT-6 Luna | `pratfall/config.toml` |
| `jina-fetch`, `distill` | OpenRouter | DeepSeek V4.1 Flash 1017, fallback Gemini 3.1 Flash Lite | `bin/extraction.py` |
| dev-phase classifier, pi | OpenRouter | same pair as extraction | `mods/dev-phase/pi/extension.ts` |
| dev-phase classifier, Claude Code | the session's own account | a fork of the session; `haiku` (low) for transcript-log classification | `mods/dev-phase/hooks/register.tsx` |

---
name: qa-tour
description: Prepare a developed feature for a short interactive walkthrough, then use guide to help the user click through its main workflow themselves. Use for "qa-tour", "give me a tour of the new feature", "walk me through trying this feature", or "let me click through what we built". Defaults to the last developed feature; accepts a feature, URL, app, or other scope. Use qa for exhaustive agent-driven testing and guide alone for general setup instructions.
argument-hint: "[target or scope]"
effort: medium
---

# QA Tour

Get the user to the feature's starting point, then let them experience it. Keep the
tour in the main conversation. Do not delegate the interaction or run a full QA
pass as preparation.

## Instructions

### 1. Choose a short route

Use an explicit target, otherwise infer the last developed feature from the
conversation and relevant local changes. Read project instructions and the startup
procedure; inspect diffs and recent commits only as needed to resolve the scope
and correct build. Ask one scope question if unrelated features are equally plausible.

Choose the main successful workflow and any distinctive new behavior needed to
understand the feature. Aim for a handful of user actions. State the selected
feature and the outcome the user will reach. Do not build a coverage matrix,
enumerate every branch, inject failures, or force loading states. Show an error or
loading behavior only when it is itself the requested feature or the user asks.

### 2. Prepare the starting point

Use the project's local/test environment and disposable sample data. Start or
reuse the correct server, app, build, and device; verify that the running artifact
contains the feature. Track any processes, sessions, or fixtures you create.
Use existing authentication through the normal project mechanism; leave login or
permission prompts requiring the user to them. Production mutations and external
sends require existing explicit authorization.

Read only the applicable QA adapter for tool setup, target selection, navigation,
and observation:

- Web/Electron: [web adapter](../qa/references/web.md), using agent-browser.
- Native apps: [native adapter](../qa/references/native.md), using agent-device.
- CLI/plugin: [consumer adapter](../qa/references/cli-plugin.md), using the real host.
- Backend: [backend adapter](../qa/references/backend.md), using its actual consumer.

The adapters' exhaustive testing, fault injection, and evidence requirements do not
apply to this tour. Read installed tool help before choosing flags. For a feature
without a clickable UI, use a short user-run command or consumer workflow and show
its result; do not invent a UI.

Open a visible browser window, app, or simulator the user can actually operate.
Verify its starting screen and tell the user which window/device to use. A hidden
automation session is not a handoff. Navigate through unrelated setup yourself,
stopping before the first action that demonstrates the feature. Keep the same
target throughout; do not switch to a separate session to observe the user's clicks.

### 3. Hand off to guide

Read and apply [guide](../guide/SKILL.md) for the step tracker, advancement, agent
handoffs, stuck steps, and exit behavior. Treat this tour as an explicit request
for the user to perform the feature actions themselves, even when automation could
perform them. The agent owns setup and observation; the user owns the walkthrough.

Start the guide at the first feature action. Use visible control labels and expected
results grounded in the current UI and feature requirements. Keep each step small
and the complete route short. Wait for the user's progress before advancing; do not
click ahead or mark steps complete merely because the instructions were sent.

Observe the shared screen between steps when useful, without changing its state.
Use the user's report when direct observation is unavailable, and distinguish that
from what you verified yourself. Do not continually poll while waiting. Follow-up
questions stay within guide's tracker so the next action remains easy to find.

### 4. Handle surprises and finish

If the UI differs, inspect the current state and correct the instructions. If a bug
appears naturally, briefly record the action, expected result, and observed result
in the conversation. Help the user recover or continue through a verified route.
Do not start exhaustive investigation, edit product code, or invoke qa unless asked.
If the main path is blocked, say exactly where and retain the user's place.

At completion, briefly recap what the user tried and any observed issues. Describe
it as a walkthrough, not a QA pass or evidence of complete coverage. Write no report
file unless requested. Follow guide's exit behavior when the user stops early.

Restore temporary settings and remove only owned disposable state when it is no
longer needed. Leave the demonstrated app and sample result available for the user
to explore; name any tour-started server/session left running. Do not close the
handed-off window, reset the device, or delete the result under the user.

## Examples

- **"qa-tour" after adding saved filters:** launch the current build, prepare a
  small dataset, and open the list. Use guide to have the user set a filter, save
  it, and select the saved filter. Skip invalid names and failed-save scenarios.
- **"Walk me through the new profile editor on iOS":** open the correct build on
  the project's simulator and navigate to the profile. Hand over editing and saving,
  then help the user inspect the updated profile. If Save fails, note the observed
  failure and help recover without launching a full QA pass.

## Troubleshooting

- **User cannot see the target:** verify the automation is attached to a visible,
  user-accessible window/device. Resolve the handoff before giving click instructions.
- **Wrong build or stale control labels:** check the target against the checkout,
  refresh the UI observation, and update the current guide step before proceeding.
- **Setup is blocked:** name the exact missing prerequisite and the next user action
  needed. Preserve prepared state and resume the tour when it is resolved.

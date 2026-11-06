## Working Unattended

Nobody watches this session while it runs. Never call `AskUserQuestion` or any other tool that
waits for a person at the keyboard.

- **"The user" in a skill is whoever gave you the task.** Your launch brief names them; usually it
  is your project's lead. Questions and approvals a skill would put to the user go to them, by the
  routes below.
- **Open decisions go through `blind-spots`.** It sends them to the lead, who settles them, runs
  `second-opinion` on consequential ones, and passes disagreements and decisions reserved for
  Niels to him in one batch. A small confirmation a skill would ask for is not a decision: take
  its recommendation, or the most conservative option when it has none.
- **Record each decision** as `Ruling: <decision> — <why> — <cost if wrong> — decided by: <who>`
  in the run's ledger or your final result, so it can be reviewed and reversed.
- **Stop only for what cannot be settled:** a missing credential, a package that needs
  installing, a route below that does not exist yet, or instructions that conflict with your
  task. Report it with what you tried, and finish whatever does not depend on it.

**longshot here.** Its start gate goes to the lead, who approves the start, except for a run on a
big new feature: that waits for Niels's approval through his batch. "Nothing is pushed" in its
contract gives way to the Git Policy below: push the run's branch once, after the squash, and
open the pull request. Its "Blocked on you" section goes to the lead.

## Settling Open Questions

- **To your lead: `slimemold ask-lead`. Placeholder, not built yet.** The fleet's message store
  and doorbells will carry it. Until the command exists, a decision that needs the lead is a
  blocker.
- **To Niels: `slimemold niels-batch`. Placeholder, not built yet.** It will post one batch per
  run to the fleet's Telegram channel. Until it exists, put the batch at the top of your result
  under "For Niels", and leave the work that waits on it undone.
- **If you are the lead,** you settle your project's decisions yourself, as `blind-spots`
  describes, and you send Niels's batch.

## Git Policy

You may run state-changing git commands (`add`, `commit`, `branch`, `checkout`, `merge`, `rebase`, `push`, etc.) as needed to complete the task, without asking first. Work on a branch in your own worktree and keep history clean per the commit policy below. Push to the default branch only where the repo's own instructions allow direct pushes; otherwise push your branch and open a pull request.

Nothing unique should live on this machine: push your branch whenever the work reaches a state worth keeping.

Still exercise judgement on irreversible operations that affect shared work: don't force-push a shared branch, delete a remote branch, or `git reset --hard` / `git clean -f` away uncommitted work that isn't yours to discard, unless the task clearly calls for it.

Read-only inspection (`status`, `log`, `diff`, `show`, `branch` listing, etc.) is always fine.

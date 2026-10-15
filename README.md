# Agent Branch Guard

**Stop an AI coding agent from undoing a PR you already merged.** Before a new task starts, this tiny CLI fetches the target branch and checks that the local checkout still points to it. It refuses to create a worktree from an old commit.

[Français](README.fr.md) · English · [Español](README.es.md)

## See the failure in one command

```sh
python3 demo.py
```

The offline demo creates a temporary remote and two clones. One clone merges change A. The agent's old checkout tries to start task B: **blocked before worktree creation**. After a fast-forward, B starts with A already present. No account, model, API key or network service is needed.

## Use it on your own repo

```sh
python3 guard.py check --repo /path/to/repo --base origin/main
python3 guard.py create --repo /path/to/repo --base origin/main \
  --branch agent-task-b --path /path/to/agent-task-b
```

Exit codes: `0` ready/created; `2` stale local HEAD or queued task base; `1` Git/configuration error. `--json` prints a receipt with the local SHA, fetched SHA and observation time. Save the base SHA when queueing a task, then pass `--expected SHA` at launch; the task is blocked if the remote moved in between. Set `--lang fr` or `--lang es` for translated status messages.

**What it checks:** the current local `HEAD` must equal the freshly fetched remote branch. This deliberately rejects local commits ahead of the remote too. Review or push those commits before creating a worktree. A remote can move after the fetch; the receipt records the SHA actually used, not a permanent lock on the branch. `--offline` skips fetch and cannot prove freshness.

## Related projects

- [Agent Office issue #119](https://github.com/AgentSystemLabs/agent-office/issues/119) describes a second agent PR reversing the first after its worktree started from stale local `HEAD`. This is the concrete failure reproduced by the demo.
- [Worktrunk](https://github.com/max-sixty/worktrunk) manages Git worktrees for parallel agents. Agent Branch Guard focuses only on proving the starting commit at task launch. No integration or affiliation is claimed.
- [A Claude Code worktree report](https://www.reddit.com/r/ClaudeCode/comments/1uwmz32/psa_claude_code_creates_subagent_worktrees_from/) describes a different mismatch between local commits and the chosen remote base. The strict SHA comparison catches that shape too.

## Test

```sh
python3 -m unittest discover -s tests -v
```

Python 3.11+, Git; no Python packages. MIT. This is an alpha command-line guard, not an integration with Agent Office or Worktrunk. It does not merge, pull or push on your behalf.

## Check the finished branch before review

```sh
python3 guard.py review --repo /path/to/feature --base origin/main --json
```

`review` fetches the base and accepts local feature commits only when `HEAD` contains that fetched base in its ancestry. A branch missing a newly merged base commit exits `2` with `base_missing`; merge or rebase deliberately, then check again. The receipt records `contains_base`, `ahead_by` (commits reachable only from HEAD) and the observed SHAs. `--expected` requires a full SHA and still blocks a moved queued base. `check` and `create` retain their strict equality rule. This ancestry check does not detect semantic reversions, replace code review, prove a clean worktree, or lock the remote after fetching.

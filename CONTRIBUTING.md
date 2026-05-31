# Contributing

## Branch & merge policy

**Nothing goes directly to `main`.** Every change — code, data, or docs — lands through a pull
request that the repository owner (**@darthmolen**) reviews and merges.

1. Create a feature branch off `main` (`feature/<name>`, `claude/<name>`, etc.).
2. Commit your work there and push the branch.
3. Open a pull request into `main`.
4. The **owner** approves and merges. No one merges their own work without the owner's sign-off.

`main` is protected on GitHub: a pull request is required before merging, the rule is enforced
for administrators (no bypass), and force-pushes and branch deletion are blocked. A rejected
push to `main` is expected behavior — branch and open a PR instead.

> Note for AI agents (e.g. Claude Code): you may push feature branches and open PRs, but you
> must **never** push to `main` or merge a PR. Stop at "PR opened" and report the URL.

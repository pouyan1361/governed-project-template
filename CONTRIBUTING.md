# Working as a team

- One owner per specialist (descriptive, diagnostic, predictive, prescriptive), one owner for governance and CI. Everyone touches the coordinator.
- Commit under your own GitHub account; the history is part of the individual grade. Small commits with messages that say what changed.
- Work on a branch, open a pull request, have one teammate read it. CI must be green before merging.
- Never commit an API key. Keys go in `export OPENAI_API_KEY=...` in your terminal or in a Codespaces secret.
- Policy edits (governance/*.json) bump `policy_version` and say why in the commit message. That is your change log for the governance package.
- Results quoted in the docs must come from a run that is reproducible from the README.

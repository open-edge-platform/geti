@AGENTS.md

## Claude Code Adapter

- Use project skills from `.claude/skills/` when the task matches them; they are
  symlink adapters into the canonical `skills/<bucket>/<name>` directories.
- Author and edit skills under `skills/`, then run
  `python3 .github/scripts/skills/agent_skills.py sync` to refresh the adapters.

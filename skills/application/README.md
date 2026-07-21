# Application agent skills

Skills for the application stack: `application/backend/` (FastAPI `geti`),
`application/ui/` (React + TypeScript), the OpenAPI contract between them, the
REST pipeline, and cross-cutting documentation.

Run commands from the relevant component root (`application/backend/` or
`application/ui/`); each uses a different runtime and toolchain.

## Skills

| Skill                     | Covers                                                                                                                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `geti-backend-dev`        | Develop and validate changes under `application/backend/app`, backend tests, packaging, API routers/schemas/services/repositories; `uv`/`just` setup, targeted pytest/behave, local server. |
| `geti-ui-dev`             | Develop and validate changes under `application/ui/src`, frontend tests, RSBuild/Vitest config, Playwright, generated API typings; Node/npm setup, lint, typecheck, test workflows.         |
| `geti-openapi-sync`       | Regenerate and validate the OpenAPI contract: backend spec generation, UI spec placement, TypeScript type regeneration, minimal cross-component checks.                                     |
| `geti-using-the-pipeline` | Drive the Geti application end to end via its REST API (project → dataset → annotate → train/quantize → deploy) and the async job model.                                                    |
| `geti-docs-update`        | Update `README.md`, `CHANGELOG.md`, Sphinx docs, or inline docstrings to reflect behavior changes.                                                                                          |

New application skills must pass at least three scenarios in
[`EVALUATION.md`](EVALUATION.md).

## Add an application skill

```bash
NAME=geti-my-workflow
mkdir -p "skills/application/$NAME"
$EDITOR "skills/application/$NAME/SKILL.md"
python3 .github/scripts/skills/agent_skills.py sync
```

Global authoring rules: [`../README.md`](../README.md).

# Agent Guidelines

These instructions apply to this repository. Follow the principles in
[andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md):
understand the problem, keep solutions simple, make focused changes, and verify the result.
Open issues, old TODOs, and feature branches are not approval to implement a roadmap.

## Scope and style

- Check `git status --short` and relevant diffs first. Preserve existing staged, unstaged, and untracked work.
- Read the implementation, callers, and samples before changing behavior. Distinguish released behavior from local changes and unverified reports.
- Keep changes limited to the task. Reuse existing parsers, CLI commands, and data structures; avoid unrelated refactors or dependency upgrades.
- Follow the existing style and use Black only on files changed for the task.
- Write project documentation, code comments, issue text, and commit messages in English. Maintain existing localized documentation when relevant.
- Keep README changes concise and update both `README.md` and `README.zh-Hans.md` for user-facing behavior changes. Use short `Add`, `Fix`, or `Update` commit messages and the existing `Changes since ...` release-note style.
- Keep personal agent preferences, machine-specific notes, and optional plugin configuration outside shared project instructions.
- Do not change versions, commit, push, tag, or publish unless requested.

## Project structure and compatibility

| Path | Responsibility |
| --- | --- |
| `sd_prompt_reader/image_data_reader.py` | Image loading, format detection, parser entry point, metadata saving |
| `sd_prompt_reader/format/base_format.py` | Shared parser properties, parameters, and status |
| `sd_prompt_reader/format/*.py` | Generation-tool parsers |
| `sd_prompt_reader/cli.py` | Click CLI and file/directory processing |
| `sd_prompt_reader/app.py`, `*_viewer.py` | CustomTkinter GUI and interactions |
| `sd_prompt_reader/utility.py`, `constants.py` | Shared helpers, constants, and GUI resources |
| `pyproject.toml`, `requirements.txt`, `poetry.lock` | Package metadata and dependencies |
| `setup.py`, `win.spec` | macOS py2app and Windows PyInstaller builds |
| `tests/` | Regression tests, fixtures, and manual experiments |

- Add parsers under `sd_prompt_reader/format/` and connect detection in `ImageDataReader`. Keep parsing independent of GUI callbacks and avoid adding GUI, clipboard, network, or platform-specific dependencies to parsing code.
- `ImageDataReader` is used by the GUI, CLI, and ComfyUI nodes. Check callers before changing property names, types, status values, parameter keys, or exported structures. Inspect downstream repositories read-only unless changes there are explicitly requested.
- Preserve support for older metadata layouts when adding new fields or formats. Parse the actual metadata; do not infer prompts from pixels or model names.
- Treat metadata as untrusted input. Never execute embedded code, install custom nodes, or run workflows to parse an image.
- Report unknown ComfyUI nodes, branches, and partial results accurately; do not present incomplete parsing as complete success.
- Propagate save failures to callers so failed operations are not displayed or counted as successful.

## Running and testing

Use a project virtual environment after checking its interpreter and dependencies; do not assume a fresh checkout contains `venv/` or upgrade global Python packages.
The commands below use the macOS/Linux layout. On Windows, use `venv\Scripts\python.exe` and adapt shell syntax.

```sh
venv/bin/python --version
venv/bin/python -m pytest --version
venv/bin/python -m sd_prompt_reader.cli --help
venv/bin/python -m sd_prompt_reader.app
```

Use explicit CLI or GUI modules when testing: `main.py` selects an entry point based on stdin/TTY state. PyCharm is not required.

- Reproduce parser and file-operation bugs with a fixture or minimal example before adding a focused regression test.
- Derive expected values from metadata, format documentation, or manual inspection, not by copying parser output. `tests/generator/testGenerator.py` writes expectations and test scripts; do not run it as a read-only check.
- Run affected tests first. Changes to detection, shared parser behavior, or common helpers also require the available format regression suite.
- Keep the entire `tests/` directory local and ignored by Git. Do not commit test collections, user-submitted attachments, or metadata extracted from them. Issue uploads are not permission to redistribute their contents. Do not add ignore exceptions or force-add these files. A fresh checkout or CI cannot assume local tests or fixtures are available.

Run the available local regression suite from `tests/` with the repository on the import path:

```sh
(
  cd tests
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. ../venv/bin/python -m pytest -q -p no:cacheprovider \
    a1111 comfyui drawthings easydiffusion fooocus invokeai novelai swarmui ruinedfooocus maintenance
)
```

- Do not collect all of `tests/` indiscriminately: `misc/` contains GUI experiments and manual scripts.
- Use temporary directories and fixture copies for editing, export, and clearing tests. Reopen output files and verify the metadata, pixels, and transparency relevant to the operation. Never overwrite source fixtures.
- Removing ordinary PNG/EXIF metadata does not necessarily remove NovelAI stealth data. Clearing tests must check for readable hidden metadata after saving.
- Distinguish code failures, missing dependencies, and unavailable fixtures. Do not hide failures by weakening assertions or broadening exception handling.
- Documentation-only changes normally need content and diff checks, not unrelated test runs. Report checks actually performed and any untested platforms or workflows; parser tests do not establish GUI or packaged-application compatibility.

## Dependencies and packaging

- Check package declarations, requirements, lock files, and build configuration together before changing dependencies. Separate runtime dependencies from platform build requirements.
- Only package for build/release tasks. Existing entry points are `venv/bin/python setup.py py2app` on macOS and `venv\Scripts\python.exe setup.py` on Windows; inspect scripts and dependencies first.
- `setup.py` writes `sd_prompt_reader/__version__.py`; the macOS path also copies Tcl/Tk and invokes `poetry add`, which can modify dependency files. Build in isolated output or a temporary copy and check diffs afterward.
- `win.spec` contains local dependency paths. `whl/` contains architecture-specific build helpers. Do not rebuild or install these artifacts unless needed for the requested build.
- Treat `venv/`, `.idea/`, `build/`, `dist/`, and temporary artifacts as local environment/output, not source. `dist/dev.sh` deletes and renames build artifacts; it is not a safe general validation command.
- Validate Windows artifacts on Windows. Universal macOS builds require dependency architecture checks and validation on each target architecture. Building, GUI smoke testing, signing, notarization, and publishing are separate steps.

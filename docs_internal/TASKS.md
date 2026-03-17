# Task System

Internal reference for pjkm's DAG-based task execution.

## Core Abstractions

### BaseTask (ABC)

```python
class BaseTask(ABC):
    id: str                    # unique task identifier (e.g., "init_project")
    phase: Phase               # SCAFFOLD | CONFIGURE | INSTALL | VERIFY
    depends_on: list[str]      # task IDs this task must run after (within same phase)
    description: str           # human-readable, shown in progress output

    def should_run(self, ctx: TaskContext) -> bool:
        """Return False to skip. Default: True."""

    @abstractmethod
    def execute(self, ctx: TaskContext) -> TaskResult:
        """Perform the work. Return TaskResult."""

    def skip_result(self) -> TaskResult: ...
    def success_result(self, message="", files_created=None, files_modified=None) -> TaskResult: ...
    def failure_result(self, message: str) -> TaskResult: ...
```

### TaskContext

Shared mutable state passed to every task:

```python
class TaskContext(BaseModel):
    config: ProjectConfig            # user selections (name, archetype, groups, etc.)
    platform: PlatformInfo           # OS, arch, has_tool() helper
    results: dict[str, TaskResult]   # completed task results keyed by task_id (O(1) lookup)
    pyproject_data: dict             # accumulated pyproject.toml content
    extra: dict                      # arbitrary task-to-task communication (e.g., github settings)

    @property
    def project_dir(self) -> Path           # shortcut to config.project_dir
    def get_result(self, task_id) -> TaskResult | None
    def has_group(self, group_id) -> bool   # checks config.selected_groups
```

### TaskResult

```python
class TaskResult(BaseModel):
    task_id: str
    success: bool = True
    message: str = ""
    files_created: list[str] = []
    files_modified: list[str] = []
    duration_ms: float = 0.0
    skipped: bool = False
```

### TaskRegistry

```python
class TaskRegistry:
    def register(self, task: BaseTask) -> None           # raises ValueError on duplicate
    def get(self, task_id: str) -> BaseTask | None
    def get_definitions(self, archetype=None) -> list[TaskDefinition]
    def all_tasks(self) -> list[BaseTask]
    @property
    def task_ids(self) -> list[str]
```

Tasks are registered in `create_default_registry()` in `src/pjkm/core/tasks/defaults.py`. No decorator magic — explicit `registry.register(TaskClass())` calls.

### TaskRunner

```python
class TaskRunner:
    def __init__(self, registry: TaskRegistry, on_event: Callable[[TaskEvent], None] | None = None)
    def run(self, ordered_definitions: list[TaskDefinition], ctx: TaskContext) -> list[TaskResult]
```

Execution logic:

1. Receives a topologically sorted task list from `DAGResolver`.
2. For each task:
   - Emit `PhaseStarted` if phase changed since last task.
   - Check `should_run(ctx)`. If `False`, store `skip_result()` and emit `TaskCompleted`.
   - Emit `TaskStarted`.
   - Call `execute(ctx)`, measure `duration_ms` via `perf_counter`.
   - If exception: catch it, create failure `TaskResult` with exception message.
   - Store result in `ctx.results[task_id]`.
   - Emit `TaskCompleted`.
   - If `not result.success and not result.skipped`: raise `TaskRunError` (immediate stop).
3. Emit `PhaseCompleted` for the final phase.

Event callbacks are wrapped in try-except — a broken callback cannot crash the build (errors print to stderr).

## DAG Resolution

`DAGResolver.resolve(tasks: list[TaskDefinition]) -> list[TaskDefinition]`

1. Group tasks by phase (SCAFFOLD, CONFIGURE, INSTALL, VERIFY).
2. Within each phase, build adjacency graph from `depends_on` edges.
3. Topologically sort using Kahn's algorithm.
4. For tasks with equal in-degree, sort by `id` for deterministic ordering.
5. Raises `CyclicDependencyError(phase, remaining_tasks)` if cycle detected.
6. Return flat list: all SCAFFOLD tasks first, then CONFIGURE, then INSTALL, then VERIFY.

Cross-phase dependencies are ignored by the DAG resolver — phase ordering is implicit and strict.

## Events

`TaskRunner` emits `TaskEvent` instances via the `on_event` callback:

| Event            | Fields                        | When                                 |
| ---------------- | ----------------------------- | ------------------------------------ |
| `PhaseStarted`   | `phase: Phase`                | Before the first task of a new phase |
| `TaskStarted`    | `task_id, phase, description` | Before `should_run()` check          |
| `TaskProgress`   | `task_id, message, fraction`  | During long-running tasks (optional) |
| `TaskCompleted`  | `task_id, result: TaskResult` | After `execute()` or skip            |
| `PhaseCompleted` | `phase: Phase`                | After the last task of a phase       |

`TaskEvent` is a union type: `TaskStarted | TaskProgress | TaskCompleted | PhaseStarted | PhaseCompleted`

CLI subscribes to render Rich console output. TUI subscribes to update ProgressBar, RichLog, and status Label widgets.

## Built-in Tasks (9)

### SCAFFOLD Phase

**`init_project`** (`scaffold/init_project.py`)

- depends_on: `[]`
- Description: "Create project structure from templates"
- Logic: Creates `project_dir`, renders base + archetype templates via `TemplateComposer`. Stores `applied_templates` list in `ctx.extra`.
- Fails if: project directory already exists and is not empty.

**`init_git`** (`scaffold/init_git.py`)

- depends_on: `["init_project"]`
- Description: "Initialize git repository"
- should_run: `.git` doesn't exist AND `git` tool is available.
- Logic: Runs `git init` in project_dir.
- Respects dry-run.

**`setup_remote`** (`scaffold/setup_remote.py`)

- depends_on: `["init_git"]`
- Description: "Configure git remote"
- should_run: `ctx.extra["github"]` has `org` or `remote` configured.
- Logic:
  1. Builds remote URL from `org` and `remote` host (default: github.com).
  2. Optionally creates the repo via `gh repo create` if `create_repo=True` and `gh` CLI is available.
  3. Runs `git remote add origin <url>`.
  4. Sets default branch via `git branch -M <branch>` (default: main).
- Configuration comes from `ctx.extra["github"]` dict, which is populated from `UserDefaults.github` or `.pjkmrc.yaml`.
- Respects dry-run.

### CONFIGURE Phase

**`apply_groups`** (`configure/apply_groups.py`)

- depends_on: `[]`
- Description: "Apply package groups (dependencies + scaffolded code)"
- should_run: `len(selected_groups) > 0`
- Logic:
  1. Loads `GroupRegistry` with `load_all()` (built-in + custom + remote sources).
  2. Validates group IDs (fails with clear error if unknown).
  3. Resolves groups transitively via `GroupResolver`.
  4. Reads `pyproject.toml`, merges deps into `[project.optional-dependencies]`.
  5. Merges tool config via `_deep_merge()` (handles dotted keys like `ruff.lint`).
  6. Writes `pyproject.toml` back (skipped in dry-run).
  7. Renders scaffolded files from group fragments (silently skips missing fragments).

**`configure_linting`** (`configure/configure_linting.py`)

- depends_on: `[]`
- Description: "Configure pre-commit, trunk, and secrets baseline"
- Logic: Writes these files (skipped if they already exist):
  - `.pre-commit-config.yaml` — 17 hooks: pre-commit-hooks v6, pyupgrade, ruff, pygrep-hooks, docformatter, lazy-log-formatter, editorconfig-checker, detect-secrets, yamlfix, yamllint, markdownlint-cli2, shellcheck, shfmt, commitizen (commit-msg stage)
  - `.trunk/trunk.yaml` — trunk v1.25.0, actions disabled: git-lfs, trunk-announce, trunk-check-pre-push, trunk-fmt-pre-commit
  - `.secrets.baseline` — detect-secrets baseline with 20 detector plugins
  - `.config/yamllint.yaml` — line-length 120, truthy check-keys false
  - `.config/.markdownlint-cli2.yaml` — line-length 120, MD033/MD041 disabled
- Respects dry-run.

**`setup_git_lfs`** (`configure/setup_git_lfs.py`)

- depends_on: `[]`
- Description: "Set up Git LFS for ML model files"
- should_run: `"hf"` or `"ml"` in `selected_groups`
- Logic:
  1. Appends LFS tracking rules for 12 ML file types (*.onnx, *.safetensors, *.bin, *.pt, *.pth, *.h5, *.hdf5, *.pkl, *.joblib, *.npy, *.npz, *.parquet) to `.gitattributes`.
  2. Runs `git lfs install` if git-lfs is available.
  3. Skips gracefully if git-lfs is not installed (adds tracking patterns but warns).
- Respects dry-run.

### INSTALL Phase

**`pdm_install`** (`install/pdm_install.py`)

- depends_on: `[]`
- Description: "Install project dependencies with PDM"
- should_run: `pdm` tool available AND `pyproject.toml` exists.
- Logic: Runs `pdm install` with 120s timeout. Captures stderr for error reporting.
- Respects dry-run.

**`pre_commit_install`** (`install/pre_commit_install.py`)

- depends_on: `["pdm_install"]`
- Description: "Install pre-commit hooks"
- should_run: `pre-commit` tool available AND `.pre-commit-config.yaml` exists AND `.git` exists.
- Logic: Runs `pre-commit install` twice — once for pre-commit hooks, once for commit-msg hooks. 60s timeout each.
- Respects dry-run.

### VERIFY Phase

**`verify_structure`** (`verify/verify_structure.py`)

- depends_on: `[]`
- Description: "Verify project structure"
- Logic: Checks that expected files exist for the archetype. Base files (all archetypes): pyproject.toml, README.md, .gitignore, .editorconfig, .gitattributes, .python-version, .github/dependabot.yml, .github/workflows/ci.yml, tests/**init**.py. Service and poly_repo add: Makefile, infra/compose.yaml, .env.example. Also verifies `src/{project_slug}/__init__.py`.

## ProjectEngine

Top-level orchestrator:

```python
class ProjectEngine:
    def __init__(self, task_registry: TaskRegistry, dag_resolver: DAGResolver | None = None)
    def execute(self, config: ProjectConfig, on_event=None, extra=None) -> ProjectResult
```

The `extra` dict is passed through to `TaskContext.extra`. The CLI populates this with `{"github": user_defaults.github.model_dump()}` for the `setup_remote` task.

**ProjectResult**:

```python
class ProjectResult(BaseModel):
    config: ProjectConfig
    results: list[TaskResult]

    @property
    def success(self) -> bool              # all tasks succeeded
    @property
    def failed_tasks(self) -> list[TaskResult]
    @property
    def skipped_tasks(self) -> list[TaskResult]
    @property
    def completed_tasks(self) -> list[TaskResult]
```

## Dry-Run Mode

All tasks check `ctx.config.dry_run` and skip destructive operations:

- `init_git`: skips `git init`
- `setup_remote`: reports what would be configured without running git/gh commands
- `apply_groups`: skips `tomli_w.dump()` and `dest.mkdir()`, still reports what would happen
- `configure_linting`: skips all file writes, still reports which files would be created
- `pdm_install`: skips `pdm install` subprocess
- `pre_commit_install`: skips `pre-commit install` subprocesses
- `TemplateRenderer`: passes `pretend=True` to `copier.run_copy()`

Success messages include "(dry run)" suffix when running in dry-run mode.

## How to Add a New Task

1. Create a file in the appropriate phase directory under `src/pjkm/core/tasks/`.
2. Subclass `BaseTask`, set `id`, `phase`, `depends_on`, `description`.
3. Implement `execute(ctx)`. Optionally override `should_run(ctx)`.
4. Register it in `src/pjkm/core/tasks/defaults.py`:

```python
from pjkm.core.tasks.my_phase.my_task import MyTask

def create_default_registry() -> TaskRegistry:
    registry = TaskRegistry()
    # ... existing tasks ...
    registry.register(MyTask())
    return registry
```

The DAG resolver picks it up automatically based on `phase` and `depends_on`.

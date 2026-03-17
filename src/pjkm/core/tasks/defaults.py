"""Default task registry with all built-in tasks."""

from __future__ import annotations

from pjkm.core.tasks.configure.apply_groups import ApplyGroupsTask
from pjkm.core.tasks.configure.configure_linting import ConfigureLintingTask
from pjkm.core.tasks.configure.setup_git_lfs import SetupGitLfsTask
from pjkm.core.tasks.install.pdm_install import PdmInstallTask
from pjkm.core.tasks.install.pre_commit_install import PreCommitInstallTask
from pjkm.core.tasks.registry import TaskRegistry
from pjkm.core.tasks.scaffold.init_git import InitGitTask
from pjkm.core.tasks.scaffold.init_project import InitProjectTask
from pjkm.core.tasks.scaffold.setup_remote import SetupRemoteTask
from pjkm.core.tasks.verify.verify_structure import VerifyStructureTask


def create_default_registry() -> TaskRegistry:
    """Create a TaskRegistry with all built-in tasks registered."""
    registry = TaskRegistry()

    # Scaffold phase
    registry.register(InitProjectTask())
    registry.register(InitGitTask())
    registry.register(SetupRemoteTask())

    # Configure phase
    registry.register(ApplyGroupsTask())
    registry.register(ConfigureLintingTask())
    registry.register(SetupGitLfsTask())

    # Install phase
    registry.register(PdmInstallTask())
    registry.register(PreCommitInstallTask())

    # Verify phase
    registry.register(VerifyStructureTask())

    # Load plugin tasks
    from importlib.metadata import entry_points

    from pjkm.core.tasks.base import BaseTask

    for ep in entry_points(group="pjkm.tasks"):
        try:
            task = ep.load()()
            if isinstance(task, BaseTask):
                registry.register(task)
        except Exception:
            pass  # Skip broken plugins silently

    return registry

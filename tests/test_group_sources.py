"""Tests for the remote group source system."""

from __future__ import annotations

import yaml

from pjkm.core.groups.sources import GroupSourceManager, SourceEntry, _slug_from_url


class TestSlugFromUrl:
    def test_https_url(self):
        slug = _slug_from_url("https://github.com/org/repo.git")
        assert slug.startswith("org-repo-")

    def test_ssh_url(self):
        slug = _slug_from_url("git@github.com:org/repo.git")
        assert slug.startswith("org-repo-")

    def test_unique_for_different_urls(self):
        s1 = _slug_from_url("https://github.com/org/repo1.git")
        s2 = _slug_from_url("https://github.com/org/repo2.git")
        assert s1 != s2

    def test_same_for_same_url(self):
        s1 = _slug_from_url("https://github.com/org/repo.git")
        s2 = _slug_from_url("https://github.com/org/repo.git")
        assert s1 == s2


class TestSourceEntry:
    def test_to_dict_minimal(self):
        entry = SourceEntry(url="https://github.com/org/repo.git")
        d = entry.to_dict()
        assert d["url"] == "https://github.com/org/repo.git"
        assert "name" in d

    def test_to_dict_full(self):
        entry = SourceEntry(
            url="https://github.com/org/repo.git",
            name="my-source",
            path="groups/",
            ref="v1.0",
        )
        d = entry.to_dict()
        assert d["name"] == "my-source"
        assert d["path"] == "groups/"
        assert d["ref"] == "v1.0"

    def test_from_dict(self):
        entry = SourceEntry.from_dict(
            {
                "url": "https://github.com/org/repo.git",
                "name": "test",
                "path": "defs/",
            }
        )
        assert entry.url == "https://github.com/org/repo.git"
        assert entry.name == "test"
        assert entry.path == "defs/"
        assert entry.ref == ""

    def test_roundtrip(self):
        original = SourceEntry(
            url="git@github.com:org/repo.git",
            name="mygroups",
            path="packages/groups",
            ref="main",
        )
        restored = SourceEntry.from_dict(original.to_dict())
        assert restored.url == original.url
        assert restored.name == original.name
        assert restored.path == original.path
        assert restored.ref == original.ref

    def test_groups_dir_no_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pjkm.core.groups.sources.CACHE_DIR", tmp_path)
        entry = SourceEntry(url="https://x.com/a/b.git", name="test")
        assert entry.cache_dir == tmp_path / "test"
        assert entry.groups_dir == tmp_path / "test"

    def test_groups_dir_with_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pjkm.core.groups.sources.CACHE_DIR", tmp_path)
        entry = SourceEntry(url="https://x.com/a/b.git", name="test", path="sub/dir")
        assert entry.groups_dir == tmp_path / "test" / "sub" / "dir"


class TestGroupSourceManager:
    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE", tmp_path / "sources.yaml"
        )
        monkeypatch.setattr("pjkm.core.groups.sources.CACHE_DIR", tmp_path / "cache")

        mgr = GroupSourceManager()
        mgr.add(url="https://github.com/org/groups.git", name="test1")
        mgr.add(url="https://github.com/org/groups2.git", name="test2", path="defs/")

        # Load in a new instance
        mgr2 = GroupSourceManager()
        mgr2.load()
        assert len(mgr2.sources) == 2
        assert mgr2.sources[0].name == "test1"
        assert mgr2.sources[1].path == "defs/"

    def test_remove(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE", tmp_path / "sources.yaml"
        )
        monkeypatch.setattr("pjkm.core.groups.sources.CACHE_DIR", tmp_path / "cache")

        mgr = GroupSourceManager()
        mgr.add(url="https://x.com/a.git", name="keep")
        mgr.add(url="https://x.com/b.git", name="remove")
        assert len(mgr.sources) == 2

        assert mgr.remove("remove") is True
        assert len(mgr.sources) == 1
        assert mgr.sources[0].name == "keep"

    def test_remove_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE", tmp_path / "sources.yaml"
        )
        mgr = GroupSourceManager()
        assert mgr.remove("nope") is False

    def test_add_replaces_same_name(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE", tmp_path / "sources.yaml"
        )
        monkeypatch.setattr("pjkm.core.groups.sources.CACHE_DIR", tmp_path / "cache")

        mgr = GroupSourceManager()
        mgr.add(url="https://old.com/repo.git", name="src")
        mgr.add(url="https://new.com/repo.git", name="src")
        assert len(mgr.sources) == 1
        assert mgr.sources[0].url == "https://new.com/repo.git"

    def test_get_all_group_dirs(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pjkm.core.groups.sources.CACHE_DIR", tmp_path)
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE", tmp_path / "sources.yaml"
        )

        # Create a fake cached source with yaml files
        (tmp_path / "mysrc").mkdir()
        (tmp_path / "mysrc" / ".git").mkdir()
        (tmp_path / "mysrc" / "test.yaml").write_text(
            yaml.dump(
                {
                    "id": "remote_test",
                    "name": "Remote Test",
                    "dependencies": {"remote_test": ["requests>=2.0"]},
                }
            )
        )

        mgr = GroupSourceManager()
        mgr.add(url="https://x.com/repo.git", name="mysrc")

        dirs = mgr.get_all_group_dirs()
        assert len(dirs) == 1
        assert dirs[0][0] == "mysrc"

    def test_load_from_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE", tmp_path / "sources.yaml"
        )
        mgr = GroupSourceManager()
        mgr.load_from_defaults(
            [
                {"url": "https://github.com/org/groups.git", "name": "from-defaults"},
            ]
        )
        assert len(mgr.sources) == 1
        assert mgr.sources[0].name == "from-defaults"

    def test_load_from_defaults_no_duplicates(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE", tmp_path / "sources.yaml"
        )
        monkeypatch.setattr("pjkm.core.groups.sources.CACHE_DIR", tmp_path / "cache")

        mgr = GroupSourceManager()
        mgr.add(url="https://github.com/org/groups.git", name="existing")
        mgr.load_from_defaults(
            [
                {"url": "https://github.com/org/groups.git", "name": "from-defaults"},
            ]
        )
        assert len(mgr.sources) == 1  # No duplicate


class TestRegistryLoadSources:
    def test_load_all_includes_remote(self, tmp_path, monkeypatch):
        """Registry.load_all() picks up groups from cached remote sources."""
        from pjkm.core.groups.registry import GroupRegistry

        monkeypatch.setattr("pjkm.core.groups.sources.CACHE_DIR", tmp_path / "cache")
        monkeypatch.setattr(
            "pjkm.core.groups.sources.SOURCES_FILE", tmp_path / "sources.yaml"
        )

        # Create a cached source
        cache_dir = tmp_path / "cache" / "test-src"
        cache_dir.mkdir(parents=True)
        (cache_dir / ".git").mkdir()
        (cache_dir / "quant.yaml").write_text(
            yaml.dump(
                {
                    "id": "quant_data",
                    "name": "Quant Data",
                    "description": "Market data packages",
                    "archetypes": [],
                    "requires_groups": [],
                    "platform_filter": None,
                    "dependencies": {"quant_data": ["pandas>=2.0", "yfinance>=1.0"]},
                    "scaffolded_files": [],
                    "pyproject_tool_config": {},
                }
            )
        )

        # Register the source
        mgr = GroupSourceManager()
        mgr._sources = [SourceEntry(url="https://x.com/repo.git", name="test-src")]
        mgr.save()

        # Load all and verify the remote group is available
        registry = GroupRegistry()
        registry.load_all()

        group = registry.get("quant_data")
        assert group is not None
        assert group.name == "Quant Data"
        assert "pandas>=2.0" in group.dependencies["quant_data"]

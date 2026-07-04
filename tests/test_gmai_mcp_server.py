from pathlib import Path

from gmai_mcp_server.server import (
    build_workspace_summary,
    get_git_status,
    list_directory,
    read_text_file,
    search_files,
)


def test_build_workspace_summary_includes_top_level_entries(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "src").mkdir()

    summary = build_workspace_summary(tmp_path)

    assert summary["root"] == str(tmp_path)
    assert "README.md" in summary["entries"]
    assert "src" in summary["entries"]
    assert summary["readme_excerpt"] == "# Demo"


def test_read_text_file_returns_content_for_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "notes.txt"
    target.write_text("hello from mcp", encoding="utf-8")

    result = read_text_file(target)

    assert result["path"] == str(target)
    assert result["content"] == "hello from mcp"


def test_list_directory_returns_child_entries(tmp_path: Path) -> None:
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta.txt").write_text("beta", encoding="utf-8")

    result = list_directory(tmp_path)

    assert result["path"] == str(tmp_path.resolve())
    assert "alpha" in result["entries"]
    assert "beta.txt" in result["entries"]


def test_search_files_finds_matching_paths(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("hello world", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("hello world", encoding="utf-8")

    result = search_files(tmp_path, "hello")

    assert result["query"] == "hello"
    assert str(tmp_path / "docs" / "guide.md") in result["matches"]
    assert str(tmp_path / "notes.txt") in result["matches"]


def test_get_git_status_returns_repository_information(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)

    result = get_git_status(tmp_path)

    assert result["root"] == str(tmp_path.resolve())
    assert result["is_git_repo"] is True
    assert "branch" in result

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_workspace_summary(root: str | Path) -> dict[str, Any]:
    root_path = Path(root).resolve()
    entries = sorted([entry.name for entry in root_path.iterdir()])
    readme_path = root_path / "README.md"
    readme_excerpt = ""

    if readme_path.exists():
        readme_excerpt = readme_path.read_text(encoding="utf-8").splitlines()[0].strip()

    return {
        "root": str(root_path),
        "entries": entries,
        "readme_excerpt": readme_excerpt,
    }


def read_text_file(path: str | Path) -> dict[str, Any]:
    target = Path(path).resolve()
    content = target.read_text(encoding="utf-8")
    return {"path": str(target), "content": content}


def list_directory(path: str | Path) -> dict[str, Any]:
    target = Path(path).resolve()
    entries = sorted([entry.name for entry in target.iterdir()])
    return {"path": str(target), "entries": entries}


def search_files(root: str | Path, query: str) -> dict[str, Any]:
    root_path = Path(root).resolve()
    matches: list[str] = []

    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if query in content:
            matches.append(str(file_path))

    return {"root": str(root_path), "query": query, "matches": sorted(matches)}


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "build_workspace_summary",
            "description": "Summarize the contents of a workspace root.",
            "inputSchema": {
                "type": "object",
                "properties": {"root": {"type": "string"}},
                "required": [],
            },
        },
        {
            "name": "read_text_file",
            "description": "Read a text file from disk.",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
        {
            "name": "list_directory",
            "description": "List the direct children of a directory.",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
        {
            "name": "search_files",
            "description": "Search for files whose contents contain a query string.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "root": {"type": "string"},
                    "query": {"type": "string"},
                },
                "required": ["root", "query"],
            },
        },
    ]


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    arguments = arguments or {}

    if name == "build_workspace_summary":
        return build_workspace_summary(arguments.get("root", "."))

    if name == "read_text_file":
        path = arguments.get("path")
        if not path:
            raise ValueError("The 'path' argument is required for read_text_file")
        return read_text_file(path)

    if name == "list_directory":
        path = arguments.get("path")
        if not path:
            raise ValueError("The 'path' argument is required for list_directory")
        return list_directory(path)

    if name == "search_files":
        root = arguments.get("root")
        query = arguments.get("query")
        if not root:
            raise ValueError("The 'root' argument is required for search_files")
        if not query:
            raise ValueError("The 'query' argument is required for search_files")
        return search_files(root, query)

    raise ValueError(f"Unknown tool: {name}")


def handle_request(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = payload.get("id")
    method = payload.get("method")

    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"status": "ok"}}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": list_tools()}}

    if method == "tools/call":
        params = payload.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments", {}) or {}
        try:
            result = call_tool(tool_name, tool_args)
        except Exception as exc:  # pragma: no cover - defensive branch
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(exc)},
            }
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Unsupported method: {method}"},
    }


def serve(stdin: Any = sys.stdin, stdout: Any = sys.stdout) -> None:
    for raw_line in stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()
            continue

        response = handle_request(payload)
        stdout.write(json.dumps(response) + "\n")
        stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="GMAI MCP Server")
    parser.add_argument("--root", default=".", help="Workspace root to inspect")
    parser.add_argument("--stdio", action="store_true", help="Run as a stdio-based MCP-style server")
    args = parser.parse_args()

    if args.stdio:
        serve()
        return

    summary = build_workspace_summary(args.root)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

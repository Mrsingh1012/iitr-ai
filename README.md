# Saksham Arora

**Software Engineer 2 @ Intuit** | Ex - Microsoft | 2x Intern @ Microsoft + 1x Intern @ Amazon

[![LinkedIn](https://img.shields.io/badge/LinkedIn-sakshamarora9575-blue?logo=linkedin)](https://linkedin.com/in/sakshamarora9575)

---

## About This Repository

This repository is used for tracking all codes of the **Agentic AI Course**.

## GMAI MCP Server

A lightweight MCP-style server is included for inspecting a workspace tree and reading text files.

Run it directly:

```bash
python -m gmai_mcp_server --root .
```

Run it in stdio mode for MCP-style JSON-RPC requests:

```bash
python -m gmai_mcp_server --stdio
```

Example request:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
```


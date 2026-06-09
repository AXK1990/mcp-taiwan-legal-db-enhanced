# mcp-taiwan-legal-db (Enhanced Version) 🌟

**English** · [繁體中文](README.md)

**This project is an enhanced version of [mcp-taiwan-legal-db](https://github.com/lawchat-oss/mcp-taiwan-legal-db)**

The original project [mcp-taiwan-legal-db](https://github.com/lawchat-oss/mcp-taiwan-legal-db) is an MCP Server developed by [LawChat](https://lawchat.com.tw), providing any MCP-compatible AI assistant with direct access to Taiwan's public legal databases:

- **Judicial Yuan judgments** — judgment.judicial.gov.tw (full-text search + retrieval)
- **National regulation database** — law.moj.gov.tw (11,700+ laws and ordinances)
- **Constitutional Court** — cons.judicial.gov.tw (868 interpretations + constitutional judgments, with full reasoning, offline cache)

This project **mcp-taiwan-legal-db-enhanced** builds upon the original architecture, adding the following features to provide AI assistants with more comprehensive access to legal data:

🌟 **Simple case system queries**<br>
🌟 **Legal interpretation system queries** (including selected judgments, precedents, judicial interpretations, resolutions, legal questions)<br>
🌟 **Advanced judgment search and pagination**

For detailed changes, see [CHANGELOG.md](CHANGELOG.md).

---

## Why we open-sourced this

Taiwan's legal data is public. Open-sourcing this so nobody has to write the same scraper twice.

---

## Features

> **Note**: In the feature table below, 🌟 marks enhanced features added by this version, while other features are inherited from the original project.

| Feature | Description |
|---------|-------------|
| **Original 8 MCP Tools** | Judgment search/full-text, regulation queries, constitutional court interpretations, citation graphs |
| **🌟 Simple Case System** | Query district court simple cases and small claim cases (🌟 enhanced feature) |
| **🌟 Legal Interpretation System** | Query Grand Justice interpretations, decisions, legal questions, selected judgments, administrative interpretations (🌟 enhanced feature) |
| **🌟 Advanced Search** | Judgment pagination, system selection, count information (🌟 enhanced feature) |
| **Offline Cache** | 868 Grand Justice interpretations and constitutional judgments (with full reasoning/opinions) returned instantly from local JSON |
| **Citation Graph** | Extract all cited interpretations from reasoning, trace constitutional jurisprudence evolution |
| **Full-text Search** | Judgment keyword search + interpretation issues/reasoning full-text search |
| **Hybrid Request Strategy** | Default httpx direct request (~0.25s), auto-fallback to Playwright when Judicial Yuan F5 WAF triggers |

---

## ⚡ Quick Start

### Linux / macOS

Run these commands **in order** (Python 3.10+ supported).

```bash
# 0. Debian / Ubuntu prerequisite (run if step 2 venv creation fails)
sudo apt install python3-venv python3-pip

# 1. Clone the repo (enhanced version repository)
git clone https://github.com/AXK1990/mcp-taiwan-legal-db-enhanced.git
cd mcp-taiwan-legal-db-enhanced

# 2. Create and populate the virtual environment
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e .

# 3. Install Playwright Chromium (only invoked when the Judicial Yuan WAF triggers; idle otherwise)
# macOS:
.venv/bin/python -m playwright install chromium

# Linux (requires system dependencies; the command will ask for sudo privileges; fully supported on Debian/Ubuntu only):
.venv/bin/python -m playwright install --with-deps chromium

# 4. Verify server installation
.venv/bin/python verify.py
```

**Expected output:**
```
Server: 台灣法律資料庫
Tools: ['search_judgments', 'get_judgment', 'query_regulation', 'get_pcode', 'search_regulations', 'get_interpretation', 'search_interpretations', 'get_citations', 'search_legal_interpretations', 'search_legal_interpretations_advanced', 'get_legal_interpretation']
Setup OK
```
(Note: Tools list will be printed as a single line)

**Done!** The repo ships a `.mcp.json` at the root, so **any Claude Code session opened inside this folder will automatically load the server**. No extra registration needed.

---

### Windows

Windows users should run these PowerShell commands (can copy and paste the entire block):

```powershell
# 1. Clone the repo (enhanced version repository)
git clone https://github.com/AXK1990/mcp-taiwan-legal-db-enhanced.git
cd mcp-taiwan-legal-db-enhanced

# 2. Create and populate the virtual environment
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\pip install -e .

# 3. Install Playwright Chromium (only invoked when the Judicial Yuan WAF triggers; idle otherwise)
.venv\Scripts\python -m playwright install chromium

# 4. Verify server installation
.venv\Scripts\python verify.py
```

**Expected output:**
```
Server: 台灣法律資料庫
Tools: ['search_judgments', 'get_judgment', 'query_regulation', 'get_pcode', 'search_regulations', 'get_interpretation', 'search_interpretations', 'get_citations', 'search_legal_interpretations', 'search_legal_interpretations_advanced', 'get_legal_interpretation']
Setup OK
```
(Note: Tools list will be printed as a single line)

**⚙️ Windows Additional Setup**

The `.mcp.json` at the repo root uses Linux / macOS path format by default. Windows users need to change:

```bash
# In .mcp.json, change "command" from
".venv/bin/python"
# to
".venv\Scripts\python.exe"
```

Or see the "Register with your Claude client" section below for the complete example.

**Done!** After modifying `.mcp.json`, **any Claude Code session opened inside this folder will automatically load the server**. No extra registration needed.

---

## 🔄 Migrating from Original Version

If you previously installed the original `mcp-taiwan-legal-db`, it's recommended to uninstall it first before installing this enhanced version to avoid package conflicts.

### Uninstall Original Version

Choose the uninstall command based on your installation method:

**If installed via pip:**

```bash
# Windows (PowerShell / CMD)
pip uninstall mcp-taiwan-legal-db

# Linux / macOS
pip3 uninstall mcp-taiwan-legal-db
```

**If installed via pipx:**

```bash
pipx uninstall mcp-taiwan-legal-db
```

**If installed via uv:**

```bash
uv tool uninstall mcp-taiwan-legal-db
```

### Install Enhanced Version

After uninstalling the original version, follow the "Quick Start" section above to install the enhanced version.

### Update MCP Configuration

If you configured the original version in Claude Desktop or other MCP clients, you'll need to update your configuration file:

**Claude Desktop config file locations:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Windows (Microsoft Store / MSIX install): `C:\Users\<YourName>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: Claude Desktop is not available for Linux. Use Claude Code CLI instead

Update the paths in your configuration to point to the enhanced version's installation location.

---

## What you get

> **Note**: This enhanced version maintains the original 8 tools and adds 3 new tools for the legal interpretation system (11 tools total). Additionally, the `search_judgments` tool has been enhanced to support simple case system queries, advanced search, and pagination.

11 MCP tools, all read-only, all hitting only public Taiwan government databases:

### Regulations & Judgments (Original Project Features)

| Tool | Purpose | Typical call |
|---|---|---|
| `search_judgments` | Search Judicial Yuan judgment database (includes 🌟 enhanced feature: simple case queries) | `search_judgments(keyword="預售屋 遲延交屋", case_type="民事")` |
| `get_judgment` | Fetch full text of a single judgment by JID or URL | `get_judgment(jid="TPSM,114,台上,3753,20251112,1")` |
| `query_regulation` | Query a regulation article / range / full text / amendment history | `query_regulation(law_name="民法", article_no="184")` |
| `get_pcode` | Resolve regulation name → pcode (law code) | `get_pcode(law_name="律師法")` |
| `search_regulations` | Keyword search across 11,700+ regulations | `search_regulations(keyword="勞動")` |

### Constitutional Court (Original Project Features)

| Tool | Purpose | Typical call |
|---|---|---|
| `get_interpretation` | Grand Justice interpretations / constitutional judgments (offline cache) | `get_interpretation("釋字748", reasoning_keyword="婚姻")` |
| `search_interpretations` | Search interpretations (issues + reasoning full text) | `search_interpretations(keyword="集會自由")` |
| `get_citations` | Citation graph (trace references backward) | `get_citations("釋字748", include_context=True)` |

### Legal Interpretation System (🌟 Enhanced Features)

| Tool | Purpose | Typical call |
|---|---|---|
| `search_legal_interpretations` | Search Judicial Yuan legal interpretation system | `search_legal_interpretations(keyword="不完全給付&瑕疵擔保")` |
| `search_legal_interpretations_advanced` | Advanced search with date range | `search_legal_interpretations_advanced(date_from="114/1/1", date_to="114/12/31", doc_types=["法律問題"])` |
| `get_legal_interpretation` | Get legal interpretation full text | `get_legal_interpretation(ty="Q", doc_id="114,1234")` |

### Tool details

<details>
<summary><b><code>search_judgments</code></b></summary>

Searches the Judicial Yuan judgment system. Supports:

- **Precise case number lookup** (fast, HTTP GET): set `case_word` + `case_number`
- **Full-text keyword search**: set `keyword`
- Filter by `court`, `case_type` (民事/刑事/行政/懲戒), `year_from`/`year_to`
- Returns results auto-sorted by court authority (最高 → 高等 → 地方)

**Important**: when looking up a specific case by its number, **always** use `case_word`+`case_number`, not `keyword`. When querying precise case numbers, **do not pass** `year_from`/`year_to`, as the case number year and judgment date year may differ.

```python
# ✅ Correct — find 台上 3753 (Supreme Court)
search_judgments(case_word="台上", case_number="3753", court="最高法院")

# ✅ Correct — full-text search
search_judgments(keyword="預售屋 遲延交屋")

# ❌ Wrong — putting case number in keyword
search_judgments(keyword="114年度台上字第3753號")
```
</details>

<details>
<summary><b><code>get_judgment</code></b></summary>

Fetches a single judgment's full structured text.

- Input: `jid` (from `search_judgments` results) OR `url`
- Output: `{case_id, court, date, main_text, facts, reasoning, cited_statutes, cited_cases, full_text, source_url}`
- Uses HTTP GET to data.aspx for full text
- Caches results for 30 days

```python
get_judgment(jid="TPSM,114,台上,3753,20251112,1")
```

Single judgments can be 10K+ tokens. Prefer `search_judgments` metadata first, only fetch full text when the user explicitly needs it.
</details>

<details>
<summary><b><code>query_regulation</code></b></summary>

Queries the national regulation database.

```python
# Single article
query_regulation(law_name="民法", article_no="184")

# Range
query_regulation(law_name="民法", from_no="184", to_no="198")

# Full law
query_regulation(law_name="律師法")

# With amendment history
query_regulation(law_name="勞動基準法", article_no="23", include_history=True)
```

Supports both `law_name` (automatic pcode resolution via `get_pcode`) and direct `pcode`. Sub-articles like `247-1`, `15-1` work.
</details>

<details>
<summary><b><code>get_pcode</code></b></summary>

Converts a regulation name to its pcode (the law.moj.gov.tw internal ID).

```python
get_pcode(law_name="律師法")
# → {"success": true, "law_name": "律師法", "pcode": "I0020006", "status": "現行法規"}

get_pcode(law_name="勞基法")
# → fuzzy match to "勞動基準法" → {"success": true, "pcode": "N0030001", ...}
```

Covers 11,700+ laws and ordinances. Bundled `pcode_all.json` is auto-refreshed weekly from the official API.
</details>

<details>
<summary><b><code>search_regulations</code></b></summary>

Keyword search across regulation names. Paginated (50 per page), current regulations sorted before abolished ones.

```python
search_regulations(keyword="勞動")
search_regulations(keyword="勞動", offset=50)  # page 2
search_regulations(keyword="消費", exclude_abolished=True)
```
</details>

<details>
<summary><b><code>get_interpretation</code></b></summary>

Gets Grand Justice interpretations (釋字第 1–813) or constitutional court judgments (憲判字) full text. Default layer returns instantly from local JSON cache.

**Layered design** (saves context):

| Layer | Trigger | Offline? |
|-------|---------|----------|
| Default (number/date/issues/interpretation) | Always | ✓ |
| Reasoning snippet | `reasoning_keyword="keyword"` | ✓ |
| Reasoning full text (max 15,000 chars) | `include_reasoning=True` | ✓ |
| Opinions snippet | `opinions_keyword="keyword"` | ✓ |
| Opinions full text | `include_opinions=True` | ✓ |

```python
# Default layer (offline, ~0ms)
get_interpretation("釋字748")

# Search keyword in reasoning
get_interpretation("釋字748", reasoning_keyword="婚姻自由")

# Locate specific justice in opinions
get_interpretation("釋字499", opinions_keyword="林子儀")

# New constitutional judgments
get_interpretation("111年憲判字第1號")
```

Prefer keyword snippet mode for locating content, only use full text mode when needed.
</details>

<details>
<summary><b><code>search_interpretations</code></b></summary>

Search Grand Justice interpretations and constitutional judgments. Keywords match title, issues, and reasoning full text.

```python
# Full-text search (searches issues + reasoning)
search_interpretations(keyword="集會自由")

# Filter by year (new system)
search_interpretations(keyword="言論自由", year=112)

# List last 10 interpretations
search_interpretations(number_from=804, number_to=813)
```
</details>

<details>
<summary><b><code>get_citations</code></b></summary>

Extracts all cited interpretation numbers from reasoning. Trace direction: find which earlier interpretations **a given ruling cites**.

```python
get_citations("釋字748")
# → citations: [釋字第242號, 釋字第362號, 釋字第365號, ...]

# Include 80-char context before/after each citation
get_citations("釋字748", include_context=True)
```
</details>

<details>
<summary><b><code>search_legal_interpretations</code></b> (🌟 Enhanced)</summary>

Search the Judicial Yuan legal interpretation system (legal.judicial.gov.tw/FINT).

Searches across:
- Grand Justice interpretations
- Constitutional court judgments
- Decisions (決議)
- Legal questions (法律問題)
- Selected judgments (精選裁判)
- Administrative interpretations (行政函釋)

```python
# Full-text search with Boolean operators
search_legal_interpretations(keyword="不完全給付&瑕疵擔保", max_results=20)

# Filter by document type
search_legal_interpretations(keyword="侵權行為", doc_type="法律問題")
```

Supports Boolean operators: `+` (OR), `-` (NOT), `&` (AND), `()` (grouping).
</details>

<details>
<summary><b><code>search_legal_interpretations_advanced</code></b> (🌟 Enhanced)</summary>

Advanced search with date range filtering. Uses **two-stage query mechanism**:
1. First query: get category counts
2. Second query: precise filtering by document types

```python
# Stage 1: Explore available types
result1 = search_legal_interpretations_advanced(
    date_from="114/1/1",
    date_to="114/12/31"
)
# categories: [{"ty": "Q", "name": "法律問題", "count": 80}, ...]

# Stage 2: Get all results for specific type
result2 = search_legal_interpretations_advanced(
    date_from="114/1/1",
    date_to="114/12/31",
    doc_types=["法律問題"],  # Use category names from stage 1
    max_results=100
)
```
</details>

<details>
<summary><b><code>get_legal_interpretation</code></b> (🌟 Enhanced)</summary>

Get full text of a legal interpretation document.

```python
# ty code mapping (complete 10 types):
# JCC = Constitutional Court Judgment
# CD  = Grand Justice Interpretation
# T   = Grand Justice Rejection Decision
# C   = Judicial Interpretation
# J2  = Grand Chamber Section
# J1  = Suspended Precedent
# J   = Selected Judgment
# D   = Decision
# Q   = Legal Question
# E   = Administrative Interpretation

get_legal_interpretation(ty="Q", doc_id="114,1234")
get_legal_interpretation(ty="D", doc_id="96,5678")
```
</details>

---

## Registering with your Claude client

Pick the section that matches the Claude client you use.

### Claude Code (CLI)

Claude Code auto-loads `.mcp.json` files at the project root. This repo already ships one.

**Linux / macOS users** (included version, no changes needed):
```json
{
  "mcpServers": {
    "taiwan-legal-db": {
      "command": ".venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "."
    }
  }
}
```

**Windows users** (modify `.mcp.json`):
```json
{
  "mcpServers": {
    "taiwan-legal-db": {
      "command": ".venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_server.server"],
      "cwd": "."
    }
  }
}
```

**Zero config**: `cd` into the repo and run `claude`. You'll see `taiwan-legal-db` in the MCP server list and nothing else in this folder.

**Share with teammates**: the `.mcp.json` is committed to the repo. Anyone who clones and completes the Quick Start gets the same MCP registration automatically.

**Add to another project** (e.g. you want this MCP available in some other folder): use `claude mcp add` with project scope:

**macOS / Linux:**
```bash
cd /path/to/your/other/project
claude mcp add taiwan-legal-db --scope project --cwd "/absolute/path/to/mcp-taiwan-legal-db-enhanced" -- \
  "/absolute/path/to/mcp-taiwan-legal-db-enhanced/.venv/bin/python" \
  -m mcp_server.server
```

**Windows (PowerShell):**
```powershell
cd C:/path/to/your/other/project
claude mcp add taiwan-legal-db --scope project --cwd "C:/path/to/mcp-taiwan-legal-db-enhanced" -- `
  "C:/path/to/mcp-taiwan-legal-db-enhanced/.venv/Scripts/python.exe" `
  -m mcp_server.server
```

This writes a `.mcp.json` in your other project's root. Change `--scope project` to `--scope user` if you want it in every project you open.

### Claude Desktop (macOS / Windows)

Claude Desktop uses a single global config file at:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Windows (Microsoft Store / WinGet / MSIX installs)**: `C:\Users\<YourName>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`

**Easiest way to open it**: in Claude Desktop, click the menu bar (not the window) → **Settings** → **Developer** → **Edit Config**. If the file doesn't exist yet, Claude Desktop creates it.

Add this under `mcpServers` (merge with anything already there):

**macOS / Linux:**
```json
{
  "mcpServers": {
    "taiwan-legal-db": {
      "command": "/absolute/path/to/mcp-taiwan-legal-db-enhanced/.venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/mcp-taiwan-legal-db-enhanced"
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "taiwan-legal-db": {
      "command": "C:/Users/YourName/mcp-taiwan-legal-db-enhanced/.venv/Scripts/python.exe",
      "args": ["-m", "mcp_server.server"],
      "cwd": "C:/Users/YourName/mcp-taiwan-legal-db-enhanced"
    }
  }
}
```

Replace the path with your actual clone path. The `cwd` field is recommended (ensures data files load correctly). Windows paths can use forward slashes `/` or double backslashes `\`.

**After saving, fully quit and reopen Claude Desktop** (not just close the window — on macOS use ⌘Q, on Windows right-click the tray icon → Quit). The config is only re-read on restart.

### Claude Cowork (Pro and above)

Claude Cowork runs inside Claude Desktop and **shares the same `claude_desktop_config.json`** — there is no separate Cowork config. Any MCP server you register for Claude Desktop is automatically bridged into Cowork's sandboxed VM by the Claude Desktop SDK layer.

**Setup**:

1. Follow the **Claude Desktop** section above to add `taiwan-legal-db` to `claude_desktop_config.json`
2. **Fully quit and reopen Claude Desktop** — this also restarts Cowork
3. Open a Cowork session. The `taiwan-legal-db` tools will be available to the Cowork agent

**Note**: Cowork is available on Claude Pro / Max / Team / Enterprise, and only accesses folders you explicitly grant permission to. The MCP server itself runs on your host (not inside the Cowork VM) and communicates via the Desktop SDK bridge, so it has access to the bundled `pcode_all.json` data file regardless of which folder you grant Cowork.

### Other MCP-compatible clients

Any MCP client that follows the [Model Context Protocol specification](https://modelcontextprotocol.io/) can use this server. The launch command is always the same:

```
.venv/bin/python -m mcp_server.server
```

**Windows:**
```
.venv\Scripts\python.exe -m mcp_server.server
```

...with `cwd` set to the repo root (so Python can find the `mcp_server` package). Consult your client's documentation for where to add the `mcpServers` JSON block.

---

## Troubleshooting

> **Note**: The following commands are in Linux / macOS format. Windows users should replace `.venv/bin/` with `.venv\Scripts\`.

**`ModuleNotFoundError: No module named 'mcp_server'`**
→ You did not run `pip install -e .` inside the venv. Go back to Quick Start step 2.

**`FileNotFoundError: data/pcode_all.json`**
→ The bundled `mcp_server/data/pcode_all.json` is missing or got deleted. Restore from `git checkout mcp_server/data/pcode_all.json`, or trigger a refresh:
```bash
.venv/bin/python -m mcp_server.updater
```

**MCP client reports "server failed to start"**
→ Run the verify command from Quick Start step 4 directly. If it fails, the import chain is broken — read the traceback. If it passes, the issue is in the MCP client's launch configuration (wrong path, wrong cwd).

---

## WAF Handling

The Judicial Yuan's `judgment.judicial.gov.tw` is behind an F5 BIG-IP ASM WAF. Plain HTTP requests may be blocked (returning a fixed 245-byte "Request Rejected" page).

This project uses a hybrid strategy:

- Requests go out via httpx directly by default (~0.25s)
- When a block is detected (response contains `Request Rejected` or JS challenge markers `bobcmn` / `TSPD`), it falls back to Playwright to execute the JS challenge
- The resulting TSPD cookies are persisted to `mcp_server/data/.judicial_cookies.json` (0600 permissions, gitignored)
- Subsequent queries resume via httpx with the refreshed cookies

`cons.judicial.gov.tw` (Constitutional Court) and `law.moj.gov.tw` (regulations) are not affected — they bypass the WAF path entirely.

---

## Data sources

All data is fetched from **public** Taiwan government databases. No other network calls are made:

| Source | Domain | Description |
|--------|--------|-------------|
| Judicial Yuan Judgment Database | judgment.judicial.gov.tw | Judgment search and full text (including simple case system) |
| Judicial Yuan Legal Interpretations | legal.judicial.gov.tw | Constitutional interpretations, decisions, legal questions, selected judgments, administrative interpretations |
| Constitutional Court | cons.judicial.gov.tw | Constitutional interpretations and judgments (offline cache) |
| National Regulations Database | law.moj.gov.tw | Regulation articles and amendment history |

`mcp_server/config.py:ALLOWED_DOMAINS` enforces this as a hard allow-list. The server refuses to fetch any URL outside these domains.

## Caching

| Data type | TTL | Location |
|---|---|---|
| Judgment full text | 30 days | `mcp_server/data/cache/legal_mcp.db` (SQLite, created on first run) |
| Search results | 24 hours | same |
| Regulation articles | 7 days | same |
| pcode metadata | 30 days | same |

Flush everything: delete `mcp_server/data/cache/legal_mcp.db`. The cache file is in `.gitignore`.

## pcode_all.json auto-update

On startup, the server checks the age of `mcp_server/data/pcode_all.json`. If the last update was before the most recent Saturday, it triggers a background refresh from `law.moj.gov.tw` official API. Failures are logged as warnings and do not block startup.

Manual refresh:
```bash
.venv/bin/python -m mcp_server.updater
```

---

## Project layout

```
mcp-taiwan-legal-db-enhanced/
├── .gitignore
├── .mcp.json              # Auto-registration for in-folder Claude Code sessions
├── LICENSE                # MIT
├── README.md              # 繁體中文 (primary)
├── README.en.md           # This file (English)
├── pyproject.toml         # Package metadata and deps
└── mcp_server/
    ├── __init__.py
    ├── server.py          # FastMCP entry — defines the 5 @mcp.tool() functions
    ├── config.py          # URLs, court codes, cache TTLs, allowed domains
    ├── updater.py         # Standalone pcode_all.json refresh script
    ├── cache/db.py        # SQLite cache layer
    ├── data/
    │   ├── pcode_all.json          # 11,700+ regulations (bundled, ~780 KB)
    │   └── law_histories.json      # Amendment history (bundled, ~9.6 MB)
    ├── models/            # Judgment / Regulation dataclasses
    ├── parsers/           # HTML parsers for judgment and regulation pages
    ├── tools/
    │   ├── judicial_search.py      # search_judgments
    │   ├── judicial_doc.py         # get_judgment
    │   └── regulations.py          # query_regulation, get_pcode, search_regulations
    └── tests/             # pytest suite
```

## Running the test suite

```bash
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest mcp_server/tests/ -v
```

---

## About

### Original Project

The original project is **[lawchat-oss/mcp-taiwan-legal-db](https://github.com/lawchat-oss/mcp-taiwan-legal-db)**.

- Original Author: [LawChat](https://lawchat.com.tw)
- Original Repository: [lawchat-oss/mcp-taiwan-legal-db](https://github.com/lawchat-oss/mcp-taiwan-legal-db)

The original project provides Taiwan legal data query functionality, including:
- Judicial Yuan judgment system queries
- National regulation database queries
- Constitutional Court Grand Justice interpretation queries
- WAF handling mechanism
- Offline cache design

### This Project (Enhanced Version)

**This enhanced version adds features that were not implemented in the original project:**

🌟 **Simple Case System Queries**: Support for district court simple cases and small claim cases<br>
🌟 **Legal Interpretation System Queries**: Support for querying Grand Justice interpretations, decisions, legal questions, selected judgments, administrative interpretations, etc.<br>
🌟 **Advanced Judgment Search**: Pagination mechanism, system selection, count statistics, and other features

**Maintenance Information**:
- Enhanced Version Repository: [AXK1990/mcp-taiwan-legal-db-enhanced](https://github.com/AXK1990/mcp-taiwan-legal-db-enhanced)
- Report Issues: [GitHub Issues](https://github.com/AXK1990/mcp-taiwan-legal-db-enhanced/issues)

**Important Statement**:
- This enhanced version is personally maintained by a community developer and is independent of the original project author and maintainers
- The quality, errors, or issues of enhanced features are unrelated to the original project author
- Users with questions or suggestions should submit issues in the enhanced version repository

## License

[MIT](LICENSE)

## Disclaimer

### General Disclaimer (Inherited from Original Project)

This is an **unofficial** tool for querying publicly-available Taiwan legal databases. It is not affiliated with, endorsed by, or authorized by the Judicial Yuan, the Ministry of Justice, or any Taiwan government agency.

The data returned by this tool reflects the state of the upstream official sources at the time of query. It may be cached (see TTLs above), and **must not be treated as legal advice or a substitute for the authoritative official sources**. Always verify against the original sources before relying on the data for any legal or official purpose.

本工具為非官方的台灣公開法規資料查詢工具，與司法院、法務部或任何台灣政府機關無隸屬關係。查詢結果以上游官方資料庫當下狀態為準，不得作為法律意見或正式用途依據，使用前請向官方資料庫驗證。

### About This Enhanced Version

This project is a enhanced version of [lawchat-oss/mcp-taiwan-legal-db](https://github.com/lawchat-oss/mcp-taiwan-legal-db), with the project architecture fully inherited from the original author's design, and only enhanced features added based on personal needs.

**Responsibility Attribution for Enhanced Version**:
- Enhanced features (legal interpretation system queries, advanced judgment search, pagination mechanism, etc.) are personally maintained by a community developer
- The quality, errors, or issues of enhanced features are unrelated to the original project author and maintainers
- The functionality and design of the original project belong to the original author
- Users should evaluate the tool's suitability themselves and take full responsibility for any decisions made using this tool
- Any applications, services, or derivative works built on this tool must take responsibility for their behavior, output correctness, and claims made to users

---
name: ai-pr-reviewer
description: Use this skill to review an Azure DevOps PR. Requires PR_URL. Supports optional MODE argument (simple|full, default: simple). Use whenever a user asks to review, check, or audit an Azure DevOps pull request, even if they don't explicitly mention a mode.
---

# AI PR Reviewer

## Overview

This skill reviews Azure DevOps pull requests with intelligent batching for large PRs (100+ files), parallel processing via sub-agents, and automatic comment posting. It auto-detects tech stacks and applies relevant coding guidelines.

## Arguments

| Argument | Required | Default  | Description |
|----------|----------|----------|-------------|
| `PR_URL` | ✅ Yes   | —        | Full Azure DevOps PR URL to review |
| `MODE`   | ❌ No    | `simple` | `simple` — download changed files via MCP (fast); `full` — clone the entire repo and compare base/target commits for deeper context |

## Workflow Overview

STRICTLY follow the workflow below for every PR review request.
DO NOT skip, merge, or reorder any steps. Each step is crucial for ensuring a thorough and efficient review process.

### Simple Mode (default)

```
1. Parse PR URL → Extract org/project/repo/pr_id
2. Fetch PR changes via MCP → Save to {session}/pr-changes/
3. Run batch_files.py → Create batches with file metadata and file list, source files kept
4. Spawn sub-agents (parallel, background) → Review each batch simultaneously
5. Each sub-agent:
    - Reads batch JSON (file list + metadata), reads actual files from pr-changes/
    - Reads tech-stack guidelines
    - Reviews files against guidelines
    - Posts negative comments to PR via MCP
    - Writes summary to {session}/
6. Main agent waits for all sub-agents → Read summaries → Final report
7. Clean up → Delete {session} folder
```

### Full Mode

```
1. Parse PR URL → Extract org/project/repo/pr_id
2. Fetch PR metadata via MCP → Get source_branch, target_branch, and file list
3. Derive clone URL → Clone repo to {session}/repo/
4. Generate manifest from git diff → List of changed files with original paths
5. Run batch_files.py → Create batches (files read directly from cloned repo)
6. Spawn sub-agents (parallel, background) → Review each batch simultaneously
7. Each sub-agent:
    - Reads batch JSON, reads full files from {session}/repo/{original_path}
    - Gets file diffs via git diff commands
    - Reads tech-stack guidelines
    - Reviews files with full context against guidelines
    - Posts negative comments to PR via MCP
    - Writes summary to {session}/
8. Main agent waits for all sub-agents → Read summaries → Final report
   (No cleanup — cloned repo remains in {session}/repo/ for further inspection)
```

## Step 1: Parse PR URL

Extract components from Azure DevOps PR URL:

**URL Format:**
```
https://dev.azure.com/{organization}/{project}/_git/{repository}/pullrequest/{pr_id}
```

Alternative URL format:
```
https://{organization}.visualstudio.com/{project}/_git/{repository}/pullrequest/{pr_id}
```

**Example:**
```
https://dev.azure.com/myOrg/MyProject/_git/dapr-shop/pullrequest/1234
or https://myOrg.visualstudio.com/myProject/_git/dapr-shop/pullrequest/1234

→ organization: myOrg
→ project: MyProject
→ repository: dapr-shop
→ pr_id: 1234
```

## Step 2: Fetch PR Changes

### Simple Mode

Use the MCP server called `ado-pr-helper` to fetch all changed files:
Abandon the workflow if you can find this MCP server is not available.

```
Call: azure_devops_fetch_pr_changes
  pr_url: {the PR URL}
  output_folder: {session}/pr-changes
```

**Important:** The MCP tool has file system access and saves files directly to disk. It returns only a small summary - file contents do NOT enter the agent's context. This prevents context overflow for large PRs.

**MCP creates:**
```
{session}/pr-changes/
├── manifest.json                     # File metadata
├── src~~~services~~~UserService.cs   # Full file (escaped path)
├── src~~~services~~~UserService.cs.diff
└── ...
```

**Path Escaping:** The MCP handles escaping - paths use `~~~` as separator (e.g., `src/services/UserService.cs` → `src~~~services~~~UserService.cs`)

**MCP Response (small, context-safe):**
```json
{
  "success": true,
  "manifest_path": "{session}/pr-changes/manifest.json",
  "files_saved": 87,
  "total_bytes": 1234567
}
```

See `references/mcp-integration.md` for full MCP tool documentation.

### Full Mode

Use the MCP server called `ado-pr-helper` to fetch PR metadata (branch names and file list):
Abandon the workflow if the MCP server is not available.

```
Call: azure_devops_fetch_pr_changes
  pr_url: {the PR URL}
  output_folder: {session}/pr-changes
```

Read `{session}/pr-changes/manifest.json` to get `source_branch` and `target_branch`. Then:

1. **Derive clone URL** from the parsed URL components:
   ```
   https://dev.azure.com/{organization}/{project}/_git/{repository}
   ```

2. **Clone the repository** to the session folder:
   ```bash
   git clone {clone_url} {session}/repo
   ```

3. **Fetch both branches:**
   ```bash
   git -C {session}/repo fetch origin {source_branch} {target_branch}
   ```

The cloned repo at `{session}/repo/` is the authoritative source for file content. Sub-agents will read full files directly from it.

## Step 3: Create Batches

### Simple Mode

Run the batching script to organize files:

```bash
python "{skill_path}/scripts/batch_files.py" "{session}/pr-changes/manifest.json" "{session}/batches/"
```

**What it does:**
- Groups files by tech stack (dotnet, frontend, python, config)
- Excludes lock files, generated files, binaries
- Creates batches under 90K token limit (with 20K overhead reserve)
- **Stores file metadata only** (paths, sizes) — no content embedded in batch JSON
- **Keeps all source files** in pr-changes folder — sub-agents read them directly

**Output:**
```
{session}/batches/
├── batch-summary.json          # Overview of all batches
├── batch-1-dotnet.json         # .NET files batch (metadata only)
├── batch-2-frontend.json       # Frontend files batch (metadata only)
├── batch-3-python.json         # Python files batch (metadata only)
└── batch-4-config.json         # Config files batch (metadata only)
```

**Batch JSON Structure (path-as-key):**
```json
{
  "batch_number": 1,
  "tech_stack": "dotnet",
  "file_count": 5,
  "total_tokens": 45000,
  "pr_changes_dir": "{session}/pr-changes",
  "files": {
    "src/services/UserService.cs": {
      "escaped_name": "src~~~services~~~UserService.cs",
      "diff_name": "src~~~services~~~UserService.cs.diff",
      "size_bytes": 1234,
      "diff_size_bytes": 567
    },
    "src/controllers/OrderController.cs": {
      "escaped_name": "src~~~controllers~~~OrderController.cs",
      "diff_name": "src~~~controllers~~~OrderController.cs.diff",
      "size_bytes": 890,
      "diff_size_bytes": 210
    }
  }
}
```

**Important:** Source files remain in `pr-changes/` after batching. Sub-agents read files directly using the `escaped_name` and `diff_name` paths from the batch JSON, combined with `pr_changes_dir`.

### Full Mode

Generate a manifest compatible with `batch_files.py` from the git diff output, then run the batching script.

**Step 1 — Generate manifest at `{session}/repo/manifest.json`:**

Run this Python snippet (the manifest must live inside the repo dir so `batch_files.py` sets `pr_changes_dir` to the repo root):

```python
import subprocess, json, os

repo_dir = r"{session}/repo"
source_branch = "{source_branch}"
target_branch = "{target_branch}"

result = subprocess.run(
    ["git", "-C", repo_dir, "diff", f"origin/{target_branch}...origin/{source_branch}", "--name-only"],
    capture_output=True, text=True
)
changed_files = [f for f in result.stdout.strip().split("\n") if f]

files = []
for path in changed_files:
    full_path = os.path.join(repo_dir, path)
    size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
    diff_result = subprocess.run(
        ["git", "-C", repo_dir, "diff", f"origin/{target_branch}...origin/{source_branch}", "--", path],
        capture_output=True, text=True
    )
    diff_size = len(diff_result.stdout.encode("utf-8"))
    files.append({
        "originalPath": path,
        "escapedName": path,      # No escaping — files live at original paths in repo
        "diffName": None,         # Diffs fetched via git diff at review time
        "changeType": "modified",
        "sizeBytes": size,
        "diffSizeBytes": diff_size
    })

manifest = {
    "pr_url": "{pr_url}",
    "source_branch": source_branch,
    "target_branch": target_branch,
    "statistics": {"total_files": len(files)},
    "files": files
}

with open(os.path.join(repo_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Generated manifest with {len(files)} changed files")
```

**Step 2 — Run batching script** (manifest inside repo dir → `pr_changes_dir` auto-set to `{session}/repo`):

```bash
python "{skill_path}/scripts/batch_files.py" "{session}/repo/manifest.json" "{session}/batches/"
```

**Batch JSON in full mode:** `pr_changes_dir` = `{session}/repo`. Each file entry has `escaped_name` = original path (no `~~~` escaping) and `diff_name` = null. Sub-agents use these to read files directly from the cloned repo and fetch diffs via git.

## Step 4: Spawn Sub-agents for Parallel Review

For each batch, spawn a sub-agent using the Task tool with background execution. **All sub-agents must be launched simultaneously in parallel.**

**Method: Background Task Agents**

Launch ALL batch review agents in a **single message** with multiple Task tool calls, each with `run_in_background: true`:

```
For each batch file in {session}/batches/:
  Use Task tool with:
    subagent_type: "general-purpose"
    run_in_background: true
    prompt: {sub-agent prompt - see template below}
```

**Important:**
- All Task tool calls MUST be in the SAME message to ensure parallel execution
- Use `run_in_background: true` so all agents run concurrently
- Each agent will return an `output_file` path - use `Read` tool to check results when done
- Wait for all agents to complete before consolidating summaries

### Sub-agent Prompt Template

```markdown
# PR Review Task - Batch {batch_number}

## Your Task
Review the files in this batch for security vulnerabilities, code quality issues, logic errors, and performance problems. Post comments for any issues found.

## Review Strategy
Read the `{skill_path}/references/pr-review-strategy.md` file for detailed review strategy and best practices.

## Guidelines
Read the guidelines file before reviewing:
- For dotnet: `{skill_path}/references/dotnet-guidelines.md`
- For frontend: `{skill_path}/references/frontend-guidelines.md`
- For python: `{skill_path}/references/python-guidelines.md`
- For config: Review for syntax correctness, security (no hardcoded secrets), and best practices

## Files to Review

Read the batch file: {session}/batches/batch-{batch_number}-{tech_stack}.json

The batch JSON has this structure:
```json
{
  "batch_number": N,
  "tech_stack": "dotnet|frontend|python|config",
  "pr_changes_dir": "/path/to/session/pr-changes-or-repo",
  "files": {
    "path/to/file.cs": {
      "escaped_name": "path~~~to~~~file.cs",  // original path in full mode (no escaping)
      "diff_name": "path~~~to~~~file.cs.diff", // null in full mode
      "size_bytes": 1234,
      "diff_size_bytes": 567
    }
  }
}
```

**Reading files — depends on mode:**
- **Simple mode** (`diff_name` is not null):
  1. Read the full file: `{pr_changes_dir}/{escaped_name}`
  2. Read the diff: `{pr_changes_dir}/{diff_name}` (may not exist for new files)
- **Full mode** (`diff_name` is null, `pr_changes_dir` points to repo root):
  1. Read the full file: `{pr_changes_dir}/{escaped_name}` (escaped_name = original path)
  2. Get the diff by running:
     ```bash
     git -C {pr_changes_dir} diff origin/{target_branch}...origin/{source_branch} -- {file_path}
     ```

In both modes, focus your review on changed lines shown in the diff.

## LSP Analysis (best-effort)

If your environment provides LSP tools, use them to enrich the review. Useful LSP operations:
- **Go to definition** — understand what a changed function/class actually does
- **Find references** — see how many callers a modified function has (useful for assessing impact of changes)
- **Hover / type info** — verify types for suspicious parameters or return values

Use whatever is available. Skip this step if no LSP tools are accessible.

## Severity Levels
- **Critical**: Security vulnerabilities, data loss risks, production crashes, blocking bugs
- **Major**: Performance issues, code correctness problems, maintainability concerns, significant best practice violations
- **Minor**: Code style issues, minor optimizations, documentation gaps, suggestions for improvement

## Posting Comments
For each issue found, call MCP server `ado-pr-helper` tools to post comments:
```
azure_devops_post_comment:
  pr_url: {pr_url}
  file_path: {file_path_from_batch_key}
  line_number: {line number from diff}
  comment_text: |
    **[{Severity}]** `{file_path}:{line_number}`
    {Brief description of the issue}

    ```suggestion
    {Corrected code snippet}
    ```
  severity: {Critical|Major|Minor}
```

**Format Guidelines:**
- First line: Severity level and file reference in format `**[Severity]** `file/path:line``
- Second line: Brief, clear description of the issue
- Include `suggestion` code block with corrected code whenever possible
- For multi-line suggestions, you may use `/* Lines X-Y omitted */` to indicate unchanged code sections
- Only post comments for actual issues (negative findings). Do NOT post positive/praise comments.

## Output Summary
After reviewing all files, write a summary to:
{session}/batch-{batch_number}-summary.md

Use this format:
```markdown
## Batch {batch_number}: {tech_stack} Files ({file_count} files)

### Findings by Severity
- Critical: {count}
- Major: {count}
- Minor: {count}

### Key Issues
- {Brief description of most important issues}

### Patterns Observed
- {Any recurring issues or patterns}
```

Then respond with: "Batch {batch_number} complete: {file_count} files, {finding_count} findings posted"
```

## Step 5: Consolidate Final Report

After launching all sub-agents in background:

1. **Wait for completion:** Use `TaskOutput` tool with each agent's task_id to wait for completion, or use `Read` tool to check the `output_file` returned by each background task
2. Read all summary files from `{session}/`
3. Aggregate findings across batches
4. Identify cross-cutting concerns
5. Generate final report
6. **Clean up (simple mode only):** Delete the entire `{session}` folder to free disk space

**Cleanup for simple mode (cross-platform Python):**
```bash
python -c "import shutil; shutil.rmtree(r'{session}')"
```

This removes:
- `{session}/pr-changes/manifest.json` and all downloaded source files/diffs
- `{session}/batches/*.json` (all batch files)
- `{session}/*.md` (all summary files)
- The entire session directory

**Full mode:** No cleanup. The cloned repo at `{session}/repo/` is preserved for further inspection.

### Final Report Format

```markdown
# PR Review Summary

**PR:** {pr_url}
**Mode:** {simple|full}
**Files Reviewed:** {total_files}
**Batches:** {batch_count}

## Overall Findings

| Severity | Count |
|----------|-------|
| Critical | {n}   |
| Major    | {n}   |
| Minor    | {n}   |

## Critical Issues
{List of critical issues from all batches}

## High Priority Issues
{List of high priority issues}

## Patterns & Recommendations
{Cross-cutting concerns observed across multiple files}

## Review by Tech Stack

### .NET ({n} files)
{Summary from dotnet batch}

### Frontend ({n} files)
{Summary from frontend batch}

### Python ({n} files)
{Summary from python batch}

### Configuration ({n} files)
{Summary from config batch}
```

## Tech Stack Detection

Files are classified by extension:

| Extension | Tech Stack |
|-----------|------------|
| .cs, .csproj, .sln, .slnx, .props, .razor, .cshtml | dotnet |
| .js, .jsx, .ts, .tsx, .html, .css, .scss, .vue, .svelte | frontend |
| .py, .pyi, .pyx | python |
| .json, .yaml, .yml, .http, .rest | config |

## File Exclusions

These files are automatically excluded from review:
- Lock files: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Pipfile.lock`, `poetry.lock`, `packages.lock.json`
- Generated: `*.min.js`, `*.min.css`, `*.d.ts`, `*.g.cs`, `*.Designer.cs`, `*.generated.cs`
- Binaries: Images, fonts, compiled files
- Misc: `.gitignore`, `.editorconfig`

**Note:** Configuration files (JSON, YAML) and HTTP test files are now included in reviews.

## Resources

### scripts/batch_files.py
Python script that creates optimal batches for review. Estimates token budget using file size (4 bytes per token heuristic).

### references/
- `pr-review-strategy.md` - General review strategy
- `dotnet-guidelines.md` - .NET security, quality, performance guidelines
- `frontend-guidelines.md` - JS/TS/React security, quality guidelines
- `python-guidelines.md` - Python security, quality guidelines
- `mcp-integration.md` - MCP server `ado-pr-helper` documentation

## Example Usage

### Simple Mode (default)

**User:** Review this PR: https://dev.azure.com/myOrg/MyProject/_git/dapr-shop/pullrequest/1234

**Agent Response:**
1. Parses URL → myOrg/MyProject/dapr-shop/1234
2. Fetches changes via MCP → 87 files downloaded to session folder
3. Creates batches → 4 batches (32 .NET, 41 frontend, 11 python, 3 config files), source files kept in pr-changes/
4. Reviews in parallel → Spawns 4 background sub-agents, posts 23 comments
5. Consolidates → Returns summary with 2 Critical, 5 Major, 12 Minor findings
6. Cleanup → Deletes session folder

### Full Mode

**User:** Review this PR in full mode: https://dev.azure.com/myOrg/MyProject/_git/dapr-shop/pullrequest/1234

**Agent Response:**
1. Parses URL → myOrg/MyProject/dapr-shop/1234
2. Fetches PR metadata via MCP → source_branch: feature/auth, target_branch: main
3. Clones repo → `git clone https://dev.azure.com/myOrg/MyProject/_git/dapr-shop {session}/repo`
4. Generates manifest from git diff → 87 changed files identified
5. Creates batches → 4 batches pointing to cloned repo (pr_changes_dir = {session}/repo)
6. Reviews in parallel → Spawns 4 background sub-agents with full file context, posts 23 comments
7. Consolidates → Returns summary with 2 Critical, 5 Major, 12 Minor findings
   (Cloned repo preserved at {session}/repo for further inspection)

---
name: ai-pr-reviewer
description: Use this skill when user asks for Azure DevOps PR review with a URL
---

# AI PR Reviewer

## Overview

This skill reviews Azure DevOps pull requests with intelligent batching for large PRs (100+ files), parallel processing via sub-agents, and automatic comment posting. It auto-detects tech stacks and applies relevant coding guidelines.

## Workflow Overview

```
1. Parse PR URL → Extract org/project/repo/pr_id
2. Fetch PR changes via MCP → Save to {session}/pr-changes/
3. Run batch_files.py → Create batches with embedded content, delete source files
4. Spawn sub-agents (parallel, background) → Review each batch simultaneously
5. Each sub-agent:
    - Reads batch JSON (contains all file content and diffs)
    - Reads tech-stack guidelines
    - Reviews files against guidelines
    - Posts negative comments to PR via MCP
    - Writes summary to {session}/
6. Main agent waits for all sub-agents → Read summaries → Final report
7. Clean up → Delete {session} folder
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

## Step 3: Create Batches

Run the batching script to organize files:

```bash
python "{skill_path}/scripts/batch_files.py" "{session}/pr-changes/manifest.json" "{session}/batches/"
```

**What it does:**
- Groups files by tech stack (dotnet, frontend, python, config)
- Excludes lock files, generated files, binaries
- Creates batches under 90K token limit (with 20K overhead reserve)
- **Embeds file content and diff directly in batch JSON files**
- **Deletes source files from pr-changes folder after batching** (keeps manifest.json only)

**Output:**
```
{session}/batches/
├── batch-summary.json          # Overview of all batches
├── batch-1-dotnet.json         # .NET files batch (with embedded content)
├── batch-2-frontend.json       # Frontend files batch (with embedded content)
├── batch-3-python.json         # Python files batch (with embedded content)
└── batch-4-config.json         # Config files batch (with embedded content)
```

**Batch JSON Structure (path-as-key):**
```json
{
  "batch_number": 1,
  "tech_stack": "dotnet",
  "file_count": 5,
  "total_tokens": 45000,
  "files": {
    "src/services/UserService.cs": {
      "content": "// Full file content here...",
      "diff": "@@ -10,5 +10,8 @@ diff content here..."
    },
    "src/controllers/OrderController.cs": {
      "content": "// Full file content...",
      "diff": "@@ -1,3 +1,5 @@ diff..."
    }
  }
}
```

**Important:** After batching, the pr-changes folder will only contain `manifest.json`. All file content and diffs are embedded in the batch JSON files. Sub-agents should ONLY read batch files, not the pr-changes folder.

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
  "files": {
    "path/to/file.cs": {
      "content": "full file content",
      "diff": "diff showing changes"
    }
  }
}
```

For each file path in the `files` object:
1. Review the `content` (full file)
2. Focus on changed lines shown in the `diff`
3. The key is the original file path (use this for posting comments)

**IMPORTANT:** All file content is embedded in the batch JSON. Do NOT look for files in pr-changes folder.

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
6. **Clean up session folder:** Delete the entire `{session}` folder to free disk space

**Cleanup (cross-platform Python):**
```bash
python -c "import shutil; shutil.rmtree(r'{session}')"
```

This removes:
- `{session}/pr-changes/manifest.json` (only remaining file after batching)
- `{session}/batches/*.json` (all batch files)
- `{session}/*.md` (all summary files)
- The entire session directory

### Final Report Format

```markdown
# PR Review Summary

**PR:** {pr_url}
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
- Generated: `*.min.js`, `*.min.css`, `*.d.ts`, `*.g.cs`, `*.Designer.cs`
- Binaries: Images, fonts, compiled files
- Misc: `.gitignore`, `.editorconfig`

**Note:** Configuration files (JSON, YAML) and HTTP test files are now included in reviews.

## Resources

### scripts/batch_files.py
Python script that creates optimal batches for review. Uses tiktoken for accurate token counting.

### references/
- `pr-review-strategy.md` - General review strategy
- `dotnet-guidelines.md` - .NET security, quality, performance guidelines
- `frontend-guidelines.md` - JS/TS/React security, quality guidelines
- `python-guidelines.md` - Python security, quality guidelines
- `mcp-integration.md` - MCP server `ado-pr-helper` documentation

## Example Usage

**User:** Review this PR: https://dev.azure.com/myOrg/MyProject/_git/dapr-shop/pullrequest/1234

**Agent Response:**
1. Parses URL → myOrg.visualstudio.com/myProject/Engineering%20China/dapr-shop/1234
2. Fetches changes via MCP → 87 files downloaded to session folder
3. Creates batches → 4 batches (32 .NET, 41 frontend, 11 python, 3 config files), deletes source files
4. Reviews in parallel → Spawns 4 background sub-agents, posts 23 comments
5. Consolidates → Returns summary with 2 Critical, 5 Major, 12 Minor findings
6. Cleanup → Deletes session folder

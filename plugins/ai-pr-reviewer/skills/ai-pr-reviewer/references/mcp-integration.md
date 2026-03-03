# Azure DevOps MCP Integration

This document describes the Azure DevOps MCP tools used by this skill.

> **Note**: This is a placeholder. Update with actual MCP tool definitions when available.

## MCP Tools

### azure_devops_fetch_pr_changes

Fetches all changed files from a pull request and **saves them directly to a local folder**.

**Important:** This MCP tool has file system access and writes files directly to disk. The agent's context remains clean - only the small response metadata is returned.

**Input Parameters:**
```json
{
  "pr_url": "https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{id}",
  "output_folder": "{session}/pr-changes"
}
```

**What the MCP does:**
1. Fetches PR metadata (title, author, branches, etc.)
2. Gets list of all changed files
3. For each file:
   - Fetches full file content (right/target version)
   - Fetches diff showing changes
   - Escapes the file path using `~~~` separator
   - Writes `{escaped_name}` (full file)
   - Writes `{escaped_name}.diff` (diff file)
4. Creates `manifest.json` with all metadata
5. Returns small summary to agent (NOT file contents)

**Path Escaping Rules (Handled by MCP):**
- Path separators (`/` and `\`) are replaced with `~~~`
- Example: `src/services/UserService.cs` → `src~~~services~~~UserService.cs`
- The MCP is responsible for this escaping logic

**Output Structure:**
Creates the following in `output_folder`:
```
pr-changes/
├── manifest.json                             # Metadata (see structure below)
├── src~~~services~~~UserService.cs           # Full file content
├── src~~~services~~~UserService.cs.diff      # Diff showing changes
├── src~~~controllers~~~OrderController.cs
├── src~~~controllers~~~OrderController.cs.diff
└── ...
```

**manifest.json Structure:**
```json
{
  "pr_url": "https://dev.azure.com/org/project/_git/repo/pullrequest/368461",
  "pr_id": 368461,
  "pr_title": "Add user authentication",
  "pr_description": "Implements JWT-based auth...",
  "pr_author": {
    "display_name": "John Doe",
    "email": "john.doe@example.com"
  },
  "pr_status": "active",
  "source_branch": "feature/auth",
  "target_branch": "main",
  "created_date": "2026-01-20T10:30:00Z",
  "fetch_timestamp": "2026-01-22T08:40:00Z",
  "statistics": {
    "total_files": 15,
    "total_size_bytes": 52000,
    "changes": {
      "added": 3,
      "modified": 10,
      "deleted": 2,
      "renamed": 0
    }
  },
  "files": [
    {
      "original_path": "src/services/UserService.cs",
      "escaped_name": "src~~~services~~~UserService.cs",
      "diff_name": "src~~~services~~~UserService.cs.diff",
      "change_type": "modified",
      "size_bytes": 4523,
      "diff_size_bytes": 892,
      "lines_added": 45,
      "lines_deleted": 12
    }
  ]
}
```

**MCP Response (returned to agent):**
```json
{
  "success": true,
  "manifest_path": "{output_folder}/manifest.json",
  "files_saved": 15,
  "total_bytes": 52000,
  "summary": {
    "added": 3,
    "modified": 10,
    "deleted": 2
  }
}
```

**Key Point:** The agent never sees the file contents in its context - only the small response above. This prevents context overflow for large PRs.

---

### azure_devops_post_comment

Posts a review comment to a specific file and line in the PR.

**Input Parameters:**
```json
{
  "pr_url": "https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{id}",
  "file_path": "src/services/UserService.cs",
  "line_number": 42,
  "comment_text": "Potential SQL injection vulnerability. Use parameterized queries.",
  "severity": "Critical",
  "thread_status": "active"
}
```

**Severity Levels:**
- `Critical` - Security vulnerabilities, data loss risks
- `High` - Bugs, logic errors, potential crashes
- `Medium` - Code quality, performance issues
- `Low` - Best practice suggestions, minor improvements

**Thread Status:**
- `active` - Requires resolution
- `fixed` - Marked as resolved
- `wontFix` - Acknowledged but won't fix
- `closed` - Closed without action

**Output:**
```json
{
  "success": true,
  "comment_id": 12345,
  "thread_id": 67890
}
```

---

## Comment Format

When posting comments, use this format:

```
**[{Severity}]** {Brief Issue Title}

{Detailed explanation of the issue}

**Suggestion:**
{Code suggestion or fix recommendation}

**Reference:** {Guideline section if applicable}
```

**Example:**
```
**[Critical]** SQL Injection Vulnerability

The query uses string interpolation which is vulnerable to SQL injection attacks.

**Suggestion:**
Use parameterized queries:
```csharp
var query = "SELECT * FROM Users WHERE Id = @Id";
command.Parameters.AddWithValue("@Id", userId);
```

**Reference:** .NET Guidelines - Security - SQL Injection
```

---

## Error Handling

MCP tools may return errors in this format:

```json
{
  "success": false,
  "error": {
    "code": "PR_NOT_FOUND",
    "message": "Pull request not found or access denied"
  }
}
```

**Common Error Codes:**
- `PR_NOT_FOUND` - PR doesn't exist or no access
- `AUTH_FAILED` - Authentication failed
- `RATE_LIMITED` - Too many requests
- `FILE_NOT_FOUND` - File doesn't exist in PR
- `COMMENT_FAILED` - Failed to post comment

---

*[TODO: Update this document with actual MCP tool definitions when the MCP is implemented]*

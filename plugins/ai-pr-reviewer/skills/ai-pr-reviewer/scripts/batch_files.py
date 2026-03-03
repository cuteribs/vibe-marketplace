#!/usr/bin/env python3
"""
Batch Files for PR Review

Groups PR changed files into optimal batches for parallel review by sub-agents.
Uses tiktoken for accurate token counting to stay under context window limits.

Usage:
    python batch_files.py <manifest_path> <output_dir> [--max-tokens 90000] [--overhead 20000]

Example:
    python batch_files.py ./pr-changes/manifest.json ./batches/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not installed. Using character-based estimation.", file=sys.stderr)


# Path separator for escaped filenames
PATH_SEPARATOR = "~~~"

# Tech stack mappings by file extension
TECH_STACK_MAP = {
    # .NET
    ".cs": "dotnet",
    ".csproj": "dotnet",
    ".sln": "dotnet",
    ".slnx": "dotnet",
    ".props": "dotnet",
    ".razor": "dotnet",
    ".cshtml": "dotnet",
    
    # Frontend (JS/TS/React/HTML)
    ".js": "frontend",
    ".jsx": "frontend",
    ".ts": "frontend",
    ".tsx": "frontend",
    ".html": "frontend",
    ".htm": "frontend",
    ".css": "frontend",
    ".scss": "frontend",
    ".sass": "frontend",
    ".less": "frontend",
    ".vue": "frontend",
    ".svelte": "frontend",
    
    # Python
    ".py": "python",
    ".pyi": "python",
    ".pyx": "python",
    ".pxd": "python",
    
    # Configuration & Test Files
    ".json": "config",
    ".yaml": "config",
    ".yml": "config",
    ".http": "config",
    ".rest": "config",
}

# Files to exclude from review (only for files within supported tech stacks)
# Note: Files without tech stack mappings are already excluded automatically
EXCLUSION_PATTERNS = [
    # Lock files (have valid extensions but shouldn't be reviewed)
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pipfile.lock",
    "poetry.lock",
    "packages.lock.json",
    
    # Generated/minified files with valid tech stack extensions
    ".min.js",      # Frontend - minified JavaScript
    ".min.css",     # Frontend - minified CSS
    ".d.ts",        # Frontend - TypeScript declaration files
    ".g.cs",        # .NET - generated C# files
    ".Designer.cs", # .NET - designer generated files
    ".generated.cs",# .NET - generated C# files
]


def get_tech_stack(filepath: str) -> Optional[str]:
    """Determine tech stack from file extension."""
    path = Path(filepath)
    ext = path.suffix.lower()
    return TECH_STACK_MAP.get(ext)


def should_exclude(filepath: str) -> bool:
    """Check if file should be excluded from review (generated/minified/lock files)."""
    path = Path(filepath)
    filename = path.name.lower()
    filepath_lower = filepath.lower()
    
    # Check each exclusion pattern
    for pattern in EXCLUSION_PATTERNS:
        if pattern.startswith("."):
            # Extension pattern - check if filename ends with it
            if filepath_lower.endswith(pattern.lower()):
                return True
        else:
            # Exact filename match (for lock files)
            if filename == pattern.lower():
                return True
    
    return False


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken or fallback to char estimation."""
    if TIKTOKEN_AVAILABLE:
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            pass
    # Fallback: ~4 chars per token
    return len(text) // 4


def read_file_content(file_path: Path) -> str:
    """Read file content, returning empty string if file doesn't exist."""
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}", file=sys.stderr)
            return ""
    return ""


def create_batches(
    manifest_path: str,
    output_dir: str,
    max_tokens: int = 90000,
    overhead_tokens: int = 20000,
    delete_source_files: bool = True
) -> dict:
    """
    Create optimal batches from manifest file.

    Args:
        manifest_path: Path to manifest.json
        output_dir: Directory to write batch JSON files
        max_tokens: Maximum tokens per batch (default: 90K)
        overhead_tokens: Reserved tokens for prompts/guidelines (default: 20K)
        delete_source_files: Delete source files after batching (default: True)

    Returns:
        Summary dict with batch information
    """
    # Load manifest
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    pr_changes_dir = manifest_file.parent

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Available tokens per batch after overhead
    available_tokens = max_tokens - overhead_tokens

    # Group files by tech stack, excluding unwanted files
    stacks: dict[str, list] = {}
    excluded_files = []
    files_to_delete = []  # Track files for cleanup

    for file_info in manifest.get("files", []):
        original_path = file_info.get("originalPath", "")
        escaped_name = file_info.get("escapedName", "")
        diff_name = file_info.get("diffName", "")

        # Determine tech stack
        stack = get_tech_stack(original_path)
        if not stack:
            # Exclude files with unknown extensions
            excluded_files.append(original_path)
            continue

        # Check exclusion
        if should_exclude(original_path):
            excluded_files.append(original_path)
            continue

        # Track files for potential cleanup
        if escaped_name:
            files_to_delete.append(pr_changes_dir / escaped_name)
        if diff_name:
            files_to_delete.append(pr_changes_dir / diff_name)

        # Read file content and diff content
        content = ""
        diff = ""
        if escaped_name:
            content = read_file_content(pr_changes_dir / escaped_name)
        if diff_name:
            diff = read_file_content(pr_changes_dir / diff_name)

        # Add content to file_info for batching
        file_info["content"] = content
        file_info["diff"] = diff

        if stack not in stacks:
            stacks[stack] = []
        stacks[stack].append(file_info)
    
    # Sort files within each stack by size (ascending) for better packing
    for stack in stacks:
        stacks[stack].sort(key=lambda f: f.get("sizeBytes", 0) + f.get("diffSizeBytes", 0))
    
    # Create batches with path-as-key structure
    batches = []
    batch_number = 1

    for stack, files in stacks.items():
        current_batch_files = {}
        current_batch_tokens = 0
        
        for file_info in files:
            # Count tokens for this file
            content = file_info.get("content", "")
            diff = file_info.get("diff", "")
            file_tokens = count_tokens(content) + count_tokens(diff)
            
            # Check if adding this file would exceed the limit
            if current_batch_tokens + file_tokens > available_tokens and current_batch_files:
                # Save current batch and start a new one
                batches.append({
                    "batch_number": batch_number,
                    "tech_stack": stack,
                    "file_count": len(current_batch_files),
                    "total_tokens": current_batch_tokens,
                    "files": current_batch_files
                })
                batch_number += 1
                current_batch_files = {}
                current_batch_tokens = 0
            
            # Add file to current batch (using original_path as key)
            original_path = file_info.get("originalPath", "")
            current_batch_files[original_path] = {
                "content": content,
                "diff": diff
            }
            current_batch_tokens += file_tokens
        
        # Add the last batch for this stack if it has files
        if current_batch_files:
            batches.append({
                "batch_number": batch_number,
                "tech_stack": stack,
                "file_count": len(current_batch_files),
                "total_tokens": current_batch_tokens,
                "files": current_batch_files
            })
            batch_number += 1
    
    # Write batch files
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for batch in batches:
        batch_filename = f"batch-{batch['batch_number']}-{batch['tech_stack']}.json"
        batch_file = output_path / batch_filename
        with open(batch_file, "w", encoding="utf-8") as f:
            json.dump(batch, f, indent=2)
    
    # Create summary
    summary = {
        "total_batches": len(batches),
        "total_files_to_review": sum(b["file_count"] for b in batches),
        "excluded_files_count": len(excluded_files),
        "batches": [
            {
                "batch_number": b["batch_number"],
                "tech_stack": b["tech_stack"],
                "file_count": b["file_count"],
                "estimated_tokens": b["total_tokens"],
                "filename": f"batch-{b['batch_number']}-{b['tech_stack']}.json"
            }
            for b in batches
        ],
        "excluded_files": excluded_files,
        "settings": {
            "max_tokens": max_tokens,
            "overhead_tokens": overhead_tokens,
            "available_tokens_per_batch": available_tokens
        }
    }
    
    # Write summary
    summary_file = output_path / "batch-summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Delete source files if requested
    deleted_count = 0
    if delete_source_files:
        for file_path in files_to_delete:
            try:
                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
            except Exception:
                pass  # Ignore deletion errors

    summary["deleted_source_files"] = deleted_count

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Create optimal batches for PR review"
    )
    parser.add_argument(
        "manifest_path",
        help="Path to manifest.json file"
    )
    parser.add_argument(
        "output_dir",
        help="Directory to write batch JSON files"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=90000,
        help="Maximum tokens per batch (default: 90000)"
    )
    parser.add_argument(
        "--overhead",
        type=int,
        default=20000,
        help="Reserved tokens for prompts/guidelines (default: 20000)"
    )
    parser.add_argument(
        "--no-delete",
        action="store_true",
        help="Do not delete source files after batching"
    )

    args = parser.parse_args()

    try:
        summary = create_batches(
            args.manifest_path,
            args.output_dir,
            args.max_tokens,
            args.overhead,
            delete_source_files=not args.no_delete
        )

        print(f"✅ Created {summary['total_batches']} batches")
        print(f"   Files to review: {summary['total_files_to_review']}")
        print(f"   Excluded files: {summary['excluded_files_count']}")
        if summary.get("deleted_source_files", 0) > 0:
            print(f"   Deleted source files: {summary['deleted_source_files']}")
        print()
        for batch in summary["batches"]:
            print(f"   Batch {batch['batch_number']} ({batch['tech_stack']}): "
                  f"{batch['file_count']} files, ~{batch['estimated_tokens']:,} tokens")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

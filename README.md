# scrape_gh

# GitHub Content Extractor

A tool that extracts content from GitHub PRs and issues for LLM consumption using Firecrawl.

## Features

- Extract conversations from GitHub issues
- Extract conversations, commits, and file changes from PRs
- Parse and follow links to related issues, PRs, and commits
- Format the extracted content for optimal LLM consumption
- Recursively extract content from related items with depth control

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/scrape_gh.git
cd scrape_gh
```

2. Install dependencies:
```
pip install -r requirements.txt
```
or
```
# With uv (recommended)
uv pip install -e .
```

3. Set up your Firecrawl API key:
```
cp .env.example .env
```
Then edit `.env` and replace `your_api_key_here` with your actual Firecrawl API key from [firecrawl.dev](https://firecrawl.dev).

## Usage

### Command Line

Note: If you're using uv, replace `python` with `uv run` in the following commands.


Extract content from a GitHub issue or PR:

```
python cli.py https://github.com/owner/repo/issues/123
```

Options:
- `-o, --output FILE`: Save the output to a file instead of printing to stdout
- `-r, --raw`: Output raw extracted data without LLM-friendly formatting
- `-f, --format {json,markdown}`: Output format (default: json)
- `-d, --depth INT`: Maximum depth for recursive extraction of related items (default: 0, no recursion)
- `-t, --types [PR issue commit]`: Types of related items to include (default: all types)

Examples:

```
# Extract a PR and save as JSON
python cli.py https://github.com/owner/repo/pull/456 -o pr_456.json

# Extract an issue and format as Markdown
python cli.py https://github.com/owner/repo/issues/123 -f markdown -o issue_123.md

# Extract a PR with related issues (depth 1)
python cli.py https://github.com/owner/repo/pull/456 -d 1 -t issue -o pr_with_issues.json

# Extract an issue with all related items (depth 2)
python cli.py https://github.com/owner/repo/issues/123 -d 2 -f markdown -o issue_with_related.md
```

### Python API

You can also use the library in your Python code:

```python
from extract import extract_content, extract_content_with_related, format_for_llm

# Basic extraction from a GitHub issue or PR
content = extract_content("https://github.com/owner/repo/issues/123")

# Extract with related items (depth 1)
content_with_related = extract_content_with_related(
    "https://github.com/owner/repo/issues/123",
    max_depth=1,
    include_types=["PR", "issue"]  # Optional: filter by type
)

# Format the content for LLM consumption
formatted_content = format_for_llm(content_with_related)

# Use the formatted content in your application
print(formatted_content["title"])
print(formatted_content["conversation"])

# Access related items
for item in formatted_content["related_items"]:
    print(f"Related: {item['reference']}")
    if item.get("content"):
        print(f"  Title: {item['content']['title']}")
```

## Output Format

The tool returns a structured dictionary containing:
- Title and description
- Conversation thread
- Related PRs, issues, and commits
- For PRs: commit messages and file changes

When recursive extraction is enabled, related items will also include their extracted content.

This format is optimized for feeding into LLMs for analysis or summarization.

## License

MIT
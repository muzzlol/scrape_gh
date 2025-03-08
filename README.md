# scrape_gh

# GitHub Content Extractor

A tool that extracts content from GitHub PRs and issues for LLM consumption using Firecrawl.

## Features

- Extract conversations from GitHub issues
- Extract conversations, commits, and file changes from PRs
- Parse and follow links to related issues, PRs, and commits
- Format the extracted content for optimal LLM consumption

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

Examples:

```
# Extract a PR and save as JSON
python cli.py https://github.com/owner/repo/pull/456 -o pr_456.json

# Extract an issue and format as Markdown
python cli.py https://github.com/owner/repo/issues/123 -f markdown -o issue_123.md
```

### Python API

You can also use the library in your Python code:

```python
from extract import extract_content, format_for_llm

# Extract content from a GitHub issue or PR
content = extract_content("https://github.com/owner/repo/issues/123")

# Format the content for LLM consumption
formatted_content = format_for_llm(content)

# Use the formatted content in your application
print(formatted_content["title"])
print(formatted_content["conversation"])
```

## Output Format

The tool returns a structured dictionary containing:
- Title and description
- Conversation thread
- Related PRs, issues, and commits
- For PRs: commit messages and file changes

This format is optimized for feeding into LLMs for analysis or summarization.

## License

MIT
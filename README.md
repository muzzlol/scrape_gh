# scrape_gh

# GitHub Content Extractor

A tool that extracts content from GitHub PRs and issues for LLM consumption using Firecrawl.

## Features

- Extract conversations from GitHub issues
- Extract conversations, commits, and file changes from PRs
- Parse and follow links to related issues, PRs, and commits
- Format the extracted content for optimal LLM consumption



## Output Format

The tool returns a structured dictionary containing:
- Title and description
- Conversation thread
- Related PRs, issues, and commits
- For PRs: commit messages and file changes

This format is optimized for feeding into LLMs for analysis or summarization.
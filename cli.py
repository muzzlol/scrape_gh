#!/usr/bin/env python3
import argparse
import json
import sys
from extract import extract_content, extract_content_with_related, format_for_llm, FirecrawlError

def main():
    parser = argparse.ArgumentParser(description="Extract content from GitHub issues and PRs for LLM consumption")
    parser.add_argument("url", help="URL to the GitHub issue or pull request")
    parser.add_argument("-o", "--output", help="Output file path (if not specified, prints to stdout)")
    parser.add_argument("-r", "--raw", action="store_true", help="Output raw extracted data without LLM formatting")
    parser.add_argument("-f", "--format", choices=["json", "markdown"], default="json", 
                        help="Output format (default: json)")
    parser.add_argument("-d", "--depth", type=int, default=0, 
                        help="Maximum depth for recursive extraction of related items (default: 0, no recursion)")
    parser.add_argument("-t", "--types", nargs="+", choices=["PR", "issue", "commit"], 
                        help="Types of related items to include (default: all types)")
    
    args = parser.parse_args()
    
    try:
        # Extract content from the GitHub URL
        if args.depth > 0:
            print(f"Extracting content from {args.url} with related items (depth: {args.depth})...")
            # extract_content_with_related already returns formatted content
            output_data = extract_content_with_related(args.url, max_depth=args.depth, include_types=args.types)
        else:
            print(f"Extracting content from {args.url}...")
            content = extract_content(args.url)
            
            # Process the content based on the requested format
            if args.raw:
                # Use the raw model output
                output_data = content.model_dump()
            else:
                # Format for LLM consumption
                output_data = format_for_llm(content)
        
        # Convert to the requested format
        if args.format == "json":
            output_str = json.dumps(output_data, indent=2)
        else:  # markdown
            output_str = convert_to_markdown(output_data)
        
        # Output the result
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_str)
            print(f"Output written to {args.output}")
        else:
            print(output_str)
        
    except FirecrawlError as e:
        print(f"Firecrawl Error: {str(e)}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"Invalid URL: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(3)

def convert_to_markdown(data):
    """Convert the formatted data to Markdown"""
    if data["type"] == "issue":
        return _convert_issue_to_markdown(data)
    else:
        return _convert_pr_to_markdown(data)

def _convert_issue_to_markdown(data):
    """Convert issue data to Markdown"""
    md = f"# Issue #{data['number']}: {data['title']}\n\n"
    md += f"**State:** {data['state']}  \n"
    md += f"**Author:** {data['author']}  \n"
    md += f"**Created:** {data['created_at']}  \n\n"
    
    md += "## Description\n\n"
    md += f"{data['description']}\n\n"
    
    if data["labels"]:
        md += "## Labels\n\n"
        md += ", ".join(f"`{label}`" for label in data["labels"]) + "\n\n"
    
    md += "## Conversation\n\n"
    for comment in data["conversation"]:
        md += f"{comment}\n\n---\n\n"
    
    if data["related_items"]:
        md += "## Related Items\n\n"
        for item in data["related_items"]:
            md += f"* {item}\n"
    
    return md

def _convert_pr_to_markdown(data):
    """Convert PR data to Markdown"""
    md = f"# Pull Request #{data['number']}: {data['title']}\n\n"
    md += f"**State:** {data['state']}  \n"
    md += f"**Author:** {data['author']}  \n"
    md += f"**Created:** {data['created_at']}  \n"
    if data["merged_at"]:
        md += f"**Merged:** {data['merged_at']}  \n\n"
    else:
        md += "\n"
    
    md += "## Description\n\n"
    md += f"{data['description']}\n\n"
    
    if data["labels"]:
        md += "## Labels\n\n"
        md += ", ".join(f"`{label}`" for label in data["labels"]) + "\n\n"
    
    md += "## Conversation\n\n"
    for comment in data["conversation"]:
        md += f"{comment}\n\n---\n\n"
    
    md += "## Commits\n\n"
    for commit in data["commits"]:
        md += f"* {commit}\n"
    md += "\n"
    
    md += "## File Changes\n\n"
    for change in data["file_changes"]:
        md += f"### {change['filename']} ({change['status']}, {change['changes']})\n\n"
        if change.get("patch"):
            md += "```diff\n" + change["patch"] + "\n```\n\n"
    
    if data["related_items"]:
        md += "## Related Items\n\n"
        for item in data["related_items"]:
            md += f"* {item}\n"
    
    return md

if __name__ == "__main__":
    main()

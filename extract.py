from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Set
import time
from functools import wraps

load_dotenv()

# Initialize Firecrawl
app = FirecrawlApp()

def retry_on_error(max_retries=3, initial_delay=1):
    """
    Decorator to retry a function on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    # Print informative message about the retry
                    print(f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}")
                    print(f"Retrying in {delay} seconds...")
                    
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
            
            # If we get here, all retries failed
            raise FirecrawlError(f"All {max_retries + 1} attempts failed. Last error: {str(last_exception)}")
        
        return wrapper
    return decorator

class FirecrawlError(Exception):
    """Custom exception for Firecrawl-related errors"""
    pass

# Define data models
class Comment(BaseModel):
    """Model for GitHub issue or PR comment"""
    author: str = Field(description="GitHub username of the comment author")
    content: str = Field(description="Text content of the comment")
    created_at: str = Field(description="Timestamp when the comment was created")
    updated_at: Optional[str] = Field(description="Timestamp when the comment was last updated", default=None)

class Commit(BaseModel):
    """Model for GitHub commit"""
    sha: str = Field(description="The commit SHA")
    message: str = Field(description="The commit message")
    author: str = Field(description="GitHub username of the commit author")
    created_at: str = Field(description="Timestamp when the commit was created")
    url: str = Field(description="URL to the commit")

class FileChange(BaseModel):
    """Model for file changes in a PR"""
    filename: str = Field(description="Name of the file that was changed")
    status: str = Field(description="Status of the change (added, modified, removed)")
    additions: int = Field(description="Number of lines added")
    deletions: int = Field(description="Number of lines deleted")
    changes: int = Field(description="Total number of changes")
    patch: Optional[str] = Field(description="Diff patch showing the actual changes", default=None)

class RelatedItem(BaseModel):
    """Model for related PRs, issues, or commits"""
    type: str = Field(description="Type of item (PR, issue, or commit)")
    number: Optional[int] = Field(description="Number of the PR or issue", default=None)
    sha: Optional[str] = Field(description="SHA of the commit", default=None)
    title: Optional[str] = Field(description="Title of the PR or issue", default=None)
    url: str = Field(description="URL to the item")
    content: Optional[Dict[str, Any]] = Field(description="Extracted content of the related item", default=None)

class GitHubIssue(BaseModel):
    """Model for GitHub issue"""
    title: str = Field(description="Title of the issue")
    number: int = Field(description="Issue number")
    state: str = Field(description="State of the issue (open, closed)")
    author: str = Field(description="GitHub username of the issue creator")
    created_at: str = Field(description="Timestamp when the issue was created")
    updated_at: str = Field(description="Timestamp when the issue was last updated")
    body: str = Field(description="Description of the issue")
    comments: List[Comment] = Field(description="Comments on the issue")
    labels: List[str] = Field(description="Labels attached to the issue")
    related_items: List[RelatedItem] = Field(description="Related PRs, issues, or commits", default_factory=list)

class GitHubPR(BaseModel):
    """Model for GitHub pull request"""
    title: str = Field(description="Title of the PR")
    number: int = Field(description="PR number")
    state: str = Field(description="State of the PR (open, closed, merged)")
    author: str = Field(description="GitHub username of the PR creator")
    created_at: str = Field(description="Timestamp when the PR was created")
    updated_at: str = Field(description="Timestamp when the PR was last updated")
    merged_at: Optional[str] = Field(description="Timestamp when the PR was merged", default=None)
    body: str = Field(description="Description of the PR")
    comments: List[Comment] = Field(description="Comments on the PR")
    commits: List[Commit] = Field(description="Commits in the PR")
    file_changes: List[FileChange] = Field(description="File changes in the PR")
    labels: List[str] = Field(description="Labels attached to the PR")
    related_items: List[RelatedItem] = Field(description="Related PRs, issues, or commits", default_factory=list)

@retry_on_error()
def extract_issue(url: str) -> GitHubIssue:
    """
    Extract content from a GitHub issue.
    
    Args:
        url: URL to the GitHub issue
        
    Returns:
        GitHubIssue: Structured data from the issue
        
    Raises:
        FirecrawlError: If extraction fails after all retries
    """
    try:
        result = app.extract(
            urls=[url],
            params={
                "prompt": "Extract GitHub issue information based on the schema provided.",
                "schema": GitHubIssue.model_json_schema(),
            },
        )
        
        if not result or "data" not in result:
            raise FirecrawlError(f"Invalid response from Firecrawl for {url}")
        
        return GitHubIssue(**result["data"])
    except Exception as e:
        if "500" in str(e):
            raise FirecrawlError(f"Firecrawl service error (500). This might be temporary, please try again in a few minutes. URL: {url}")
        elif "429" in str(e):
            raise FirecrawlError(f"Rate limit exceeded. Please wait a few minutes before trying again. URL: {url}")
        elif "403" in str(e):
            raise FirecrawlError(f"Access forbidden. Please check your API key and permissions. URL: {url}")
        elif "404" in str(e):
            raise FirecrawlError(f"Issue not found or private. Please check the URL and your permissions: {url}")
        else:
            raise FirecrawlError(f"Error extracting issue: {str(e)}")

@retry_on_error()
def extract_pr(url: str) -> GitHubPR:
    """
    Extract content from a GitHub pull request.
    
    Args:
        url: URL to the GitHub pull request
        
    Returns:
        GitHubPR: Structured data from the pull request
        
    Raises:
        FirecrawlError: If extraction fails after all retries
    """
    try:
        result = app.extract(
            urls=[url],
            params={
                "prompt": "Extract GitHub pull request information including comments, commits, and file changes based on the schema provided.",
                "schema": GitHubPR.model_json_schema(),
            },
        )
        
        if not result or "data" not in result:
            raise FirecrawlError(f"Invalid response from Firecrawl for {url}")
        
        return GitHubPR(**result["data"])
    except Exception as e:
        if "500" in str(e):
            raise FirecrawlError(f"Firecrawl service error (500). This might be temporary, please try again in a few minutes. URL: {url}")
        elif "429" in str(e):
            raise FirecrawlError(f"Rate limit exceeded. Please wait a few minutes before trying again. URL: {url}")
        elif "403" in str(e):
            raise FirecrawlError(f"Access forbidden. Please check your API key and permissions. URL: {url}")
        elif "404" in str(e):
            raise FirecrawlError(f"PR not found or private. Please check the URL and your permissions: {url}")
        else:
            raise FirecrawlError(f"Error extracting PR: {str(e)}")

def extract_content(url: str) -> Union[GitHubIssue, GitHubPR]:
    """
    Extract content from a GitHub issue or pull request.
    
    Args:
        url: URL to the GitHub issue or pull request
        
    Returns:
        Union[GitHubIssue, GitHubPR]: Structured data from the issue or pull request
        
    Raises:
        FirecrawlError: If extraction fails
        ValueError: If the URL is not a valid GitHub issue or PR URL
    """
    if not url.startswith("https://github.com/"):
        raise ValueError("URL must be a GitHub URL")
    
    # Determine if the URL is for an issue or a PR
    if "/pull/" in url:
        return extract_pr(url)
    elif "/issues/" in url:
        return extract_issue(url)
    else:
        raise ValueError("URL must point to a GitHub issue or pull request")

def extract_content_with_related(url: str, max_depth: int = 1, include_types: List[str] = None, visited_urls: Set[str] = None) -> Union[GitHubIssue, GitHubPR]:
    """
    Extract content from a GitHub issue or pull request, including related items up to a specified depth.
    
    Args:
        url: URL to the GitHub issue or pull request
        max_depth: Maximum depth for recursive extraction of related items (default: 1)
        include_types: List of related item types to include (default: all types)
        visited_urls: Set of URLs already visited to prevent cycles (default: empty set)
        
    Returns:
        Union[GitHubIssue, GitHubPR]: Structured data from the issue or pull request with related items
    """
    if visited_urls is None:
        visited_urls = set()
    
    # Edge case for when depth is <1 and related items have og url in thier related items
    if url in visited_urls:
        return None
    
    visited_urls.add(url)
    
    # Extract content from the URL
    content = extract_content(url)
    
    # Stop recursion if we've reached the maximum depth
    if max_depth <= 0:
        return content
    
    # Process related items
    for i, item in enumerate(content.related_items):
        # Skip if we're filtering by type and this type is not included
        if include_types and item.type not in include_types:
            continue
        
        # Skip if we've already visited this URL
        if item.url in visited_urls:
            continue
        
        try:
            # Recursively extract content from the related item
            related_content = extract_content_with_related(
                item.url, 
                max_depth=max_depth-1, 
                include_types=include_types,
                visited_urls=visited_urls
            )
            
            if related_content:
                # Store the formatted content in the related item
                content.related_items[i].content = format_for_llm(related_content)
        except Exception as e:
            print(f"Error extracting content from {item.url}: {str(e)}")
    
    return content

def format_for_llm(content: Union[GitHubIssue, GitHubPR]) -> Dict[str, Any]:
    """
    Format the extracted content for optimal LLM consumption.
    
    Args:
        content: The extracted GitHub content
        
    Returns:
        Dict[str, Any]: Formatted content optimized for LLM consumption
    """
    if isinstance(content, GitHubIssue):
        return {
            "type": "issue",
            "title": content.title,
            "number": content.number,
            "state": content.state,
            "author": content.author,
            "created_at": content.created_at,
            "description": content.body,
            "conversation": [
                f"**{comment.author}** ({comment.created_at}):\n{comment.content}"
                for comment in content.comments
            ],
            "labels": content.labels,
            "related_items": [
                {
                    "reference": f"{item.type} {item.number or item.sha}: {item.title or ''} ({item.url})",
                    "content": item.content
                }
                for item in content.related_items
            ] if content.related_items else []
        }
    else:  # GitHubPR
        return {
            "type": "pull_request",
            "title": content.title,
            "number": content.number,
            "state": content.state,
            "author": content.author,
            "created_at": content.created_at,
            "merged_at": content.merged_at,
            "description": content.body,
            "conversation": [
                f"**{comment.author}** ({comment.created_at}):\n{comment.content}"
                for comment in content.comments
            ],
            "commits": [
                f"{commit.sha[:7]}: {commit.message} (by {commit.author} on {commit.created_at})"
                for commit in content.commits
            ],
            "file_changes": [
                {
                    "filename": change.filename,
                    "status": change.status,
                    "changes": f"+{change.additions} -{change.deletions}",
                    "patch": change.patch
                }
                for change in content.file_changes
            ],
            "labels": content.labels,
            "related_items": [
                {
                    "reference": f"{item.type} {item.number or item.sha}: {item.title or ''} ({item.url})",
                    "content": item.content
                }
                for item in content.related_items
            ] if content.related_items else []
        }


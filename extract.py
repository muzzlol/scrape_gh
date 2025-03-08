from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

load_dotenv()

# Initialize Firecrawl
app = FirecrawlApp()

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

def extract_issue(url: str) -> GitHubIssue:
    """
    Extract content from a GitHub issue.
    
    Args:
        url: URL to the GitHub issue
        
    Returns:
        GitHubIssue: Structured data from the issue
    """
    result = app.extract(
        urls=[url],
        params={
            "prompt": "Extract GitHub issue information based on the schema provided.",
            "schema": GitHubIssue.model_json_schema(),
        },
    )
    
    return GitHubIssue(**result["data"])

def extract_pr(url: str) -> GitHubPR:
    """
    Extract content from a GitHub pull request.
    
    Args:
        url: URL to the GitHub pull request
        
    Returns:
        GitHubPR: Structured data from the pull request
    """
    result = app.extract(
        urls=[url],
        params={
            "prompt": "Extract GitHub pull request information including comments, commits, and file changes based on the schema provided.",
            "schema": GitHubPR.model_json_schema(),
        },
    )
    
    return GitHubPR(**result["data"])

def extract_content(url: str) -> Union[GitHubIssue, GitHubPR]:
    """
    Extract content from a GitHub issue or pull request.
    
    Args:
        url: URL to the GitHub issue or pull request
        
    Returns:
        Union[GitHubIssue, GitHubPR]: Structured data from the issue or pull request
    """
    # Determine if the URL is for an issue or a PR
    if "/pull/" in url:
        return extract_pr(url)
    elif "/issues/" in url:
        return extract_issue(url)
    else:
        raise ValueError("URL must be a GitHub issue or pull request URL")

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
                f"{item.type} {item.number or item.sha}: {item.title or ''} ({item.url})"
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
                f"{item.type} {item.number or item.sha}: {item.title or ''} ({item.url})"
                for item in content.related_items
            ] if content.related_items else []
        }

content = extract_content("https://github.com/huggingface/transformers/issues/36564")

# Format the content for LLM consumption
formatted_content = format_for_llm(content)

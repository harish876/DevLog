import os
from github import Github
import yaml

def load_preferences():
    preferences_path = os.environ.get("BLOG_SETTINGS_FILE", "preferences.yaml")
    if not os.path.exists(preferences_path):
        # Default settings for personal blog
        return {
            "repo": "harish876/harish876.github.io",
            "posts_dir": "content/posts",
            "base_branch": "main",
            "pr_base": "main",
            "default_mood": "excited",
            "default_system_prompt": "You are Harish, a developer who writes personal, story-driven, and technical blogs. Write in a way that is engaging, authentic, and reflective of your unique voice. Let your emotions and personal journey shine through.",
            "default_opening_line": "In this installment of Tools, Terminal and TCP, ...",
            "default_series": "Tools, Terminal and TCP",
            "default_is_new_series": "no",
            "default_takeaway": "Hope you found this article engaging and exciting.",
            "default_anecdotes": "If you liked it, please give some clappies, star the repo, and tell a friend!"
        }
    with open(preferences_path, "r") as f:
        return yaml.safe_load(f)

def create_blog_file_and_pr(blog_markdown, blog_title, branch_name, pr_title, pr_body):
    """
    Create a new markdown file, push a branch, and open a PR to the blog repo.
    Uses preferences.yaml for repo and directory info.
    """
    preferences = load_preferences()
    repo_name = preferences["repo"]
    posts_dir = preferences["posts_dir"]
    base_branch = preferences.get("base_branch", "main")
    pr_base = preferences.get("pr_base", base_branch)
    file_name = blog_title.lower().replace(" ", "-") + ".md"
    file_path = f"{posts_dir}/{file_name}"
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(repo_name)
    # Get latest commit SHA of base branch
    base = repo.get_branch(base_branch)
    base_sha = base.commit.sha
    # Create new branch
    ref = f"refs/heads/{branch_name}"
    try:
        repo.create_git_ref(ref=ref, sha=base_sha)
    except Exception as e:
        # Branch may already exist
        pass
    # Create or update the file in the new branch
    try:
        repo.create_file(
            path=file_path,
            message=pr_title,
            content=blog_markdown,
            branch=branch_name
        )
    except Exception as e:
        # If file exists, update it
        contents = repo.get_contents(file_path, ref=branch_name)
        repo.update_file(
            path=file_path,
            message=pr_title,
            content=blog_markdown,
            sha=contents.sha,
            branch=branch_name
        )
    # Create PR
    pr = repo.create_pull(
        title=pr_title,
        body=pr_body,
        head=branch_name,
        base=pr_base
    )
    return pr.html_url 
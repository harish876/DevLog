from github import Github
import os

def get_github_client():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise Exception("Please set the GITHUB_TOKEN environment variable.")
    return Github(token)

def fetch_all_blogs():
    """Fetch all blog posts as a list of texts from the content/posts directory of the blog repo."""
    g = get_github_client()
    repo = g.get_repo("harish876/harish876.github.io")
    posts_dir = "content/posts"
    try:
        contents = repo.get_contents(posts_dir)
    except Exception:
        return []
    blogs = []
    for file in contents:
        if file.type == "file" and file.name.endswith(".md"):
            try:
                text = file.decoded_content.decode(errors='ignore')
                blogs.append({
                    "name": file.name,
                    "content": text,
                    "path": file.path,
                    "sha": file.sha
                })
            except Exception:
                continue
    return blogs

def fetch_latest_blog():
    """Fetch the latest blog post (by last commit date) from the content/posts directory."""
    blogs = fetch_all_blogs()
    if not blogs:
        return ""
    # Use the GitHub API to get the latest commit date for each file
    g = get_github_client()
    repo = g.get_repo("harish876/harish876.github.io")
    latest_blog = None
    latest_date = None
    for blog in blogs:
        try:
            commits = repo.get_commits(path=blog["path"])
            commit = next(commits, None)
            if commit:
                commit_date = commit.commit.author.date
                if latest_date is None or commit_date > latest_date:
                    latest_date = commit_date
                    latest_blog = blog["content"]
        except Exception:
            continue
    return latest_blog or blogs[0]["content"] 
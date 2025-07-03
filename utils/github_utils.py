from github import Github
import os

def get_github_client():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise Exception("Please set the GITHUB_TOKEN environment variable.")
    return Github(token)

def get_commit_history(repo_full_name):
    g = get_github_client()
    repo = g.get_repo(repo_full_name)
    commits = repo.get_commits()
    history = []
    for commit in commits[:20]:  # Limit to latest 20 for brevity
        history.append({
            "sha": commit.sha,
            "author": commit.commit.author.name,
            "date": commit.commit.author.date.isoformat(),
            "message": commit.commit.message
        })
    return history

def get_readme_and_key_files(repo_full_name):
    g = get_github_client()
    repo = g.get_repo(repo_full_name)
    # Get README
    try:
        readme_content = repo.get_readme().decoded_content.decode()
    except Exception:
        readme_content = ""
    # Get key files (top-level, non-hidden, non-dir, not README)
    contents = repo.get_contents("")
    key_files = []
    for content_file in contents:
        if content_file.type == "file" and not content_file.name.lower().startswith("readme"):
            snippet = content_file.decoded_content.decode(errors='ignore')[:500]
            key_files.append({
                "name": content_file.name,
                "snippet": snippet
            })
    return readme_content, key_files

def analyze_codebase(repo_full_name, max_files=50, snippet_lines=20):
    """
    Recursively walk the repo, extract file metadata, code snippets, and basic insights.
    Returns a dict with largest files, most common extensions, and file summaries.
    """
    g = get_github_client()
    repo = g.get_repo(repo_full_name)
    all_files = []
    def walk(path=""):
        try:
            contents = repo.get_contents(path)
        except Exception:
            return
        for content in contents:
            if content.type == "dir":
                walk(content.path)
            elif content.type == "file":
                try:
                    raw = content.decoded_content.decode(errors='ignore')
                except Exception:
                    raw = ""
                snippet = "\n".join(raw.splitlines()[:snippet_lines])
                all_files.append({
                    "path": content.path,
                    "size": content.size,
                    "lines": len(raw.splitlines()),
                    "snippet": snippet,
                    "extension": os.path.splitext(content.name)[-1].lower()
                })
    walk()
    # Largest files
    largest = sorted(all_files, key=lambda x: -x["size"])[:5]
    # Most lines
    most_lines = sorted(all_files, key=lambda x: -x["lines"])[:5]
    # Most common extensions
    from collections import Counter
    ext_counter = Counter(f["extension"] for f in all_files)
    most_common_ext = ext_counter.most_common(5)
    return {
        "largest_files": largest,
        "most_lines_files": most_lines,
        "most_common_extensions": most_common_ext,
        "all_files_count": len(all_files),
        "file_summaries": all_files[:max_files]  # limit for LLM context
    } 
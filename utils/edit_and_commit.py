import os
from github import Github
import glob

def get_github_client():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise Exception("Please set the GITHUB_TOKEN environment variable.")
    return Github(token)

def pick_markdown_file():
    files = glob.glob("contents/*.md")
    if not files:
        print("No markdown files found in contents/.")
        exit(1)
    print("Available markdown files:")
    for i, f in enumerate(files):
        print(f"{i+1}. {f}")
    idx = int(input("Select file to edit/commit (number): ")) - 1
    return files[idx]

def main():
    g = get_github_client()
    repo_name = input("GitHub repo (e.g. harish876/harish876.github.io): ").strip()
    repo = g.get_repo(repo_name)
    branch = input("Branch name to commit to (e.g. blog-title-20240703...-auto): ").strip()
    file_path = pick_markdown_file()
    print(f"You can now edit {file_path} in your editor. Press Enter when done.")
    input()
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    github_path = "content/posts/" + os.path.basename(file_path)  # adjust as needed
    # Get file SHA on branch
    contents = repo.get_contents(github_path, ref=branch)
    sha = contents.sha
    commit_msg = input("Commit message: ").strip()
    repo.update_file(
        path=github_path,
        message=commit_msg,
        content=content,
        sha=sha,
        branch=branch
    )
    print(f"Committed {file_path} to branch {branch} in {repo_name}.")

if __name__ == "__main__":
    main() 
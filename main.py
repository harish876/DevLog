import argparse
from flow import create_qa_flow, create_blog_flow
from dotenv import load_dotenv
from rich.progress import Progress
from rich.console import Console
from rich.prompt import Prompt, Confirm
from github import Github
import glob
import os
from nodes import (
    InputGatherNode, RepoAnalyzerNode, BlogContextNode, PersonalPromptNode,
    BlogDraftGeneratorNode, ReviewAndEditNode, PRCreatorNode, WebContextNode
)
from utils.pr_creator import load_preferences

load_dotenv()
console = Console()

def prompt_with_default(prompt, key, default, example=None):
    prompt_str = f"[bold cyan]{prompt}[/bold cyan]"
    if default:
        prompt_str += f" [dim](default: {default})[/dim]"
    if example:
        prompt_str += f" [dim]e.g., {example}[/dim]"
    prompt_str += "\n> "
    val = console.input(prompt_str)
    return val.strip() if val.strip() else default

def run_qa_flow():
    shared = {
        "question": "In one sentence, what's the end of universe?",
        "answer": None
    }
    qa_flow = create_qa_flow()
    qa_flow.run(shared)
    print("Question:", shared["question"])
    print("Answer:", shared["answer"])

def run_blog_flow():
    preferences = load_preferences()
    console.rule("[bold green]PocketFlow Blog Generator[/bold green]")
    console.print("[bold yellow]Project Information[/bold yellow]")
    repo_url = Prompt.ask("Enter the GitHub repo URL to summarize", default="")
    notes = Prompt.ask("Any personal notes or anecdotes? (optional)", default="")
    extra = Prompt.ask("Anything else you'd like to add to the blog? (optional)", default="")

    console.rule("[bold yellow]Personal Context[/bold yellow]")
    series = prompt_with_default("Which series is this part of?", "series", preferences.get("default_series", ""), "Tools, Terminal and TCP")
    is_new_series = prompt_with_default("Is this a new series? (yes/no)", "is_new_series", preferences.get("default_is_new_series", "no"))
    emotions = prompt_with_default("What emotions or mood do you want to convey?", "mood", preferences.get("default_mood", ""), "excited, nostalgic, frustrated")
    takeaway = prompt_with_default("Any specific message or takeaway for readers?", "takeaway", preferences.get("default_takeaway", ""))
    anecdotes = prompt_with_default("Any anecdotes, inside jokes, or meta-commentary?", "anecdotes", preferences.get("default_anecdotes", ""))
    opening_line = prompt_with_default("How do you want to start the blog?", "opening_line", preferences.get("default_opening_line", ""), "In this installment of Tools, Terminal and TCP, ...")
    system_prompt = preferences.get("default_system_prompt", "")

    console.rule("[bold yellow]Extra Resources[/bold yellow]")
    user_urls = Prompt.ask("Any related blog URLs or websites to scan? (comma-separated, optional)", default="")
    user_urls = [u.strip() for u in user_urls.split(",") if u.strip()] if user_urls else []

    # Show summary and confirm
    console.rule("[bold green]Summary[/bold green]")
    console.print(f"[bold]Repo:[/bold] {repo_url}")
    console.print(f"[bold]Notes:[/bold] {notes}")
    console.print(f"[bold]Extra:[/bold] {extra}")
    console.print(f"[bold]Series:[/bold] {series}")
    console.print(f"[bold]Is New Series:[/bold] {is_new_series}")
    console.print(f"[bold]Emotions:[/bold] {emotions}")
    console.print(f"[bold]Takeaway:[/bold] {takeaway}")
    console.print(f"[bold]Anecdotes:[/bold] {anecdotes}")
    console.print(f"[bold]Opening Line:[/bold] {opening_line}")
    console.print(f"[bold]User URLs:[/bold] {user_urls}")
    if not Confirm.ask("Proceed with these settings?"):
        console.print("[red]Aborted.[/red]")
        return

    shared = {
        "repo_url": repo_url,
        "notes": notes,
        "extra": extra,
        "series": series,
        "is_new_series": is_new_series,
        "emotions": emotions,
        "takeaway": takeaway,
        "anecdotes": anecdotes,
        "opening_line": opening_line,
        "system_prompt": system_prompt,
        "user_urls": user_urls
    }
    steps = [
        ("Repo Analysis", RepoAnalyzerNode()),
        ("Web Context", WebContextNode()),
        ("Blog Context/Style", BlogContextNode()),
        ("Draft Generation", BlogDraftGeneratorNode())
    ]
    with Progress() as progress:
        task = progress.add_task("[cyan]Blog Generation Pipeline...", total=len(steps))
        for step_name, node in steps:
            progress.console.print(f"[bold yellow]Step: {step_name}[/bold yellow]")
            node.run(shared)
            progress.advance(task)
    # Interactive review/edit after progress bar
    console.rule("[bold green]Review/Edit[/bold green]")
    console.print("--- Blog Draft ---")
    console.print(shared["blog_draft"])
    console.print("--- End Draft ---")
    edit = Prompt.ask("Edit the draft? Paste new text or leave blank to accept", default="")
    shared["final_blog"] = edit if edit.strip() else shared["blog_draft"]
    # PR creation after review
    console.rule("[bold green]PR Creation[/bold green]")
    blog_title = Prompt.ask("Enter a title for the blog post", default="")
    pr_node = PRCreatorNode()
    shared["blog_title"] = blog_title
    pr_node.run(shared)

def run_edit_commit():
    preferences = load_preferences()
    contents_dir = preferences.get("default_local_contents_dir", "contents")
    files = glob.glob(f"{contents_dir}/*.md")
    if not files:
        console.print(f"[red]No markdown files found in {contents_dir}/.[/red]")
        return
    console.print("[bold]Available markdown files:[/bold]")
    for i, f in enumerate(files):
        console.print(f"{i+1}. {f}")
    idx = Prompt.ask("Select file to edit/commit (number)", default="1")
    try:
        idx = int(idx) - 1
        file_path = files[idx]
    except Exception:
        console.print("[red]Invalid selection.[/red]")
        return
    repo_name = Prompt.ask("GitHub repo name", default=preferences.get("repo", ""))
    branch_name = Prompt.ask("PR branch name (e.g. blog-title-20240703-auto)")
    console.print(f"[green]Edit the file in your editor, then save and press Enter to continue...[/green]")
    input("Press Enter when done editing...")
    commit_msg = Prompt.ask("Commit message", default="Update blog post")
    g = Github(os.environ.get("GITHUB_TOKEN"))
    repo = g.get_repo(repo_name)
    with open(file_path, "r") as f:
        content = f.read()
    # Get the file path in the repo (strip local dir if needed)
    posts_dir = preferences.get("posts_dir", "content/posts")
    rel_path = os.path.basename(file_path)
    repo_path = f"{posts_dir}/{rel_path}"
    # Get the file SHA if it exists in the branch
    try:
        contents = repo.get_contents(repo_path, ref=branch_name)
        sha = contents.sha
    except Exception:
        sha = None
    repo.update_file(
        repo_path,
        commit_msg,
        content,
        sha,
        branch=branch_name
    )
    console.print(f"[bold green]Committed and pushed {file_path} to {repo_name}@{branch_name}![/bold green]")

def main():
    parser = argparse.ArgumentParser(description="PocketFlow Project CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # QA Flow
    qa_parser = subparsers.add_parser("qa", help="Run the Question-Answer flow")

    # Blog Flow
    blog_parser = subparsers.add_parser("blog", help="Run the Project-to-Blog flow")

    # Edit and Commit Utility
    edit_commit_parser = subparsers.add_parser("edit-commit", help="Edit and commit a generated markdown file to a PR branch")

    args = parser.parse_args()

    if args.command == "qa":
        run_qa_flow()
    elif args.command == "blog":
        run_blog_flow()
    elif args.command == "edit-commit":
        run_edit_commit()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

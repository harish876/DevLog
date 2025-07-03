from pocketflow import Node
from utils.call_llm import call_llm
from utils.github_utils import get_commit_history, get_readme_and_key_files, analyze_codebase
from utils.blog_scraper import fetch_latest_blog, fetch_all_blogs
from utils.style_analyzer import analyze_style, summarize_style_patterns
from utils.pr_creator import create_blog_file_and_pr
from utils.web_search import search_duckduckgo
import os
import requests
from bs4 import BeautifulSoup
import datetime

class GetQuestionNode(Node):
    def exec(self, _):
        # Get question directly from user input
        user_question = input("Enter your question: ")
        return user_question
    
    def post(self, shared, prep_res, exec_res):
        # Store the user's question
        shared["question"] = exec_res
        return "default"  # Go to the next node

class AnswerNode(Node):
    def prep(self, shared):
        # Read question from shared
        return shared["question"]
    
    def exec(self, question):
        # Call LLM to get the answer
        return call_llm(question)
    
    def post(self, shared, prep_res, exec_res):
        # Store the answer in shared
        shared["answer"] = exec_res

class InputGatherNode(Node):
    def exec(self, _):
        repo_url = input("Enter the GitHub repo URL to summarize: ")
        notes = input("Any personal notes or anecdotes? (optional): ")
        return {"repo_url": repo_url, "notes": notes}
    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"

class RepoAnalyzerNode(Node):
    def prep(self, shared):
        return shared["repo_url"]
    def exec(self, repo_url):
        # Expect repo_url in the form 'https://github.com/owner/repo'
        # Extract 'owner/repo' for API usage
        import re
        m = re.match(r"https://github.com/([^/]+/[^/]+)", repo_url)
        if not m:
            raise ValueError("Invalid GitHub repo URL format. Use https://github.com/owner/repo")
        repo_full_name = m.group(1)
        commits = get_commit_history(repo_full_name)
        readme, key_files = get_readme_and_key_files(repo_full_name)
        codebase_insights = analyze_codebase(repo_full_name)
        return {
            "repo_full_name": repo_full_name,
            "commits": commits,
            "readme": readme,
            "key_files": key_files,
            "codebase_insights": codebase_insights
        }
    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"

class WebContextNode(Node):
    def prep(self, shared):
        return {
            "readme": shared.get("readme", ""),
            "commits": shared.get("commits", []),
            "notes": shared.get("notes", ""),
            "user_urls": shared.get("user_urls", []),
        }
    def exec(self, context):
        # 1. Summarize user-provided URLs
        url_summaries = []
        for url in context["user_urls"]:
            try:
                resp = requests.get(url, timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text(separator="\n")
                summary = call_llm(f"Summarize the following web page for a technical blog context:\n{text[:4000]}")
                url_summaries.append(f"Summary of {url}:\n{summary}")
            except Exception as e:
                url_summaries.append(f"Could not fetch {url}: {e}")
        # 2. Extract keywords/concepts from repo context
        extract_prompt = f"""
Given the following README, commit messages, and notes, extract a list of new technologies, libraries, frameworks, or concepts that should be explained or researched for a technical blog.

README:
{context['readme']}

Commits:
{context['commits']}

Notes:
{context['notes']}

Return a YAML list of keywords/technologies.
"""
        keywords_yaml = call_llm(extract_prompt)
        import yaml
        try:
            keywords = yaml.safe_load(keywords_yaml)
            if not isinstance(keywords, list):
                keywords = []
        except Exception:
            keywords = []
        # 3. DuckDuckGo search for each keyword
        keyword_summaries = []
        for kw in keywords:
            results = search_duckduckgo(kw)
            summary = "\n".join(results)
            keyword_summaries.append(f"Context for {kw}:\n{summary}")
        # 4. Combine all context
        combined = "\n\n".join(url_summaries + keyword_summaries)
        return {"web_context": combined}
    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"

class BlogContextNode(Node):
    def exec(self, _):
        latest_blog = fetch_latest_blog()
        all_blogs = fetch_all_blogs()
        style_analysis = analyze_style(all_blogs)
        style_summary = summarize_style_patterns(style_analysis)
        return {"latest_blog": latest_blog, "style_summary": style_summary}
    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"

class PersonalPromptNode(Node):
    def exec(self, _):
        extra = input("Anything else you'd like to add to the blog? (optional): ")
        return {"extra": extra}
    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"

class BlogDraftGeneratorNode(Node):
    def prep(self, shared):
        return {
            "repo_url": shared["repo_url"],
            "commits": shared["commits"],
            "readme": shared["readme"],
            "key_files": shared["key_files"],
            "codebase_insights": shared.get("codebase_insights", {}),
            "notes": shared.get("notes", ""),
            "extra": shared.get("extra", ""),
            "series": shared.get("series", ""),
            "is_new_series": shared.get("is_new_series", ""),
            "emotions": shared.get("emotions", ""),
            "takeaway": shared.get("takeaway", ""),
            "anecdotes": shared.get("anecdotes", ""),
            "opening_line": shared.get("opening_line", ""),
            "system_prompt": shared.get("system_prompt", ""),
            "latest_blog": shared["latest_blog"],
            "style_summary": shared["style_summary"],
            "web_context": shared.get("web_context", "")
        }
    def exec(self, context):
        system_prompt = context.get("system_prompt", "")
        prompt = f"""
{system_prompt}\n\nYou are Harish, a developer who writes personal, story-driven, and technical blogs.\n\nWrite a new blog post about the project at {context['repo_url']} in your style.\n\nProject context:\nREADME:\n{context['readme']}\n\nKey files:\n{context['key_files']}\n\nCommit history highlights:\n{context['commits']}\n\nCodebase insights:\n{context['codebase_insights']}\n\nPersonal notes:\n{context['notes']}\n\nExtra anecdotes:\n{context['extra']}\n\nPersonal context:\n- Series: {context['series']}\n- Is this a new series: {context['is_new_series']}\n- Emotions/mood: {context['emotions']}\n- Message/takeaway: {context['takeaway']}\n- Anecdotes/meta: {context['anecdotes']}\n\nOpening line/tone: {context['opening_line']}\nIf provided, start the blog with this line or closely match its tone and style.\n\nExtra context from related blogs and web resources:\n{context.get('web_context', '')}\n\nStyle guide:\n{context['style_summary']}\n\nUse the following blog as a style template:\n---\n{context['latest_blog']}\n---\n\nWrite the blog in a way that strongly reflects the above personal context and emotions. Let the author's voice and feelings shine through, as in their previous blogs.\n"""
        blog_draft = call_llm(prompt)
        # Save to local .md file in contents dir
        os.makedirs("contents", exist_ok=True)
        title = f"blog_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = os.path.join("contents", title)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(blog_draft)
        return {"blog_draft": blog_draft, "blog_file_path": file_path}
    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        print(f"Blog draft saved to {exec_res['blog_file_path']}")
        return "default"

class ReviewAndEditNode(Node):
    def prep(self, shared):
        return shared["blog_draft"]
    def exec(self, blog_draft):
        print("\n--- Blog Draft ---\n")
        print(blog_draft)
        print("\n--- End Draft ---\n")
        edit = input("Edit the draft? Paste new text or leave blank to accept: ")
        return edit if edit.strip() else blog_draft
    def post(self, shared, prep_res, exec_res):
        shared["final_blog"] = exec_res
        return "default"

class PRCreatorNode(Node):
    def prep(self, shared):
        return shared["final_blog"], shared["repo_url"]
    def exec(self, inputs):
        blog_markdown, repo_url = inputs
        blog_title = input("Enter a title for the blog post: ")
        # Make branch name unique by appending timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        branch_name = f"blog-{blog_title.lower().replace(' ', '-')}-{timestamp}-auto"
        pr_title = f"Add blog: {blog_title}"
        pr_body = "Automated blog post PR. Please review."
        pr_url = create_blog_file_and_pr(blog_markdown, blog_title, branch_name, pr_title, pr_body)
        return {"pr_url": pr_url}
    def post(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        print(f"Pull Request created: {exec_res['pr_url']}")
        return None
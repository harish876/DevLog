from utils.call_llm import call_llm
import re
from collections import Counter

def analyze_style(blog_texts, new_draft=None):
    """
    Analyze a list of blog texts for tone, structure, and signature elements using both heuristics and LLM.
    If new_draft is provided, compare its style to previous blogs using the LLM.
    Returns a dict with:
      - heuristic analysis (as before)
      - llm_style_summary (LLM's description of the style)
      - llm_similarity (LLM's assessment of similarity if new_draft is provided)
    """
    headings = []
    opening_lines = []
    closing_lines = []
    emoji_count = 0
    code_blocks = 0
    word_counter = Counter()
    total_length = 0
    all_contents = []
    for blog in blog_texts:
        content = blog["content"] if isinstance(blog, dict) else blog
        all_contents.append(content)
        lines = content.splitlines()
        # Headings
        headings += [line.strip() for line in lines if line.strip().startswith("#")]
        # Opening/closing
        if lines:
            opening_lines.append(lines[0].strip())
            closing_lines.append(lines[-1].strip())
        # Emoji
        emoji_count += len(re.findall(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]", content))
        # Code blocks
        code_blocks += content.count("```")
        # Words
        words = re.findall(r"\b\w+\b", content.lower())
        word_counter.update(words)
        total_length += len(content)
    n = len(blog_texts) or 1
    heuristics = {
        "common_headings": [h for h, _ in Counter(headings).most_common(5)],
        "average_length": total_length // n,
        "common_openings": [l for l, _ in Counter(opening_lines).most_common(3)],
        "common_closings": [l for l, _ in Counter(closing_lines).most_common(3)],
        "emoji_per_post": emoji_count / n,
        "code_blocks_per_post": code_blocks / n,
        "most_common_words": [w for w, _ in word_counter.most_common(10)]
    }
    # LLM style summary
    style_prompt = f"""
You are an expert writing coach. Analyze the following set of blog posts and describe the author's writing style, tone, and structure in detail. List any signature elements or recurring patterns.\n\nBLOGS:\n---\n{chr(10).join(all_contents[:3])}\n---\n"""
    llm_style_summary = call_llm(style_prompt)
    llm_similarity = None
    if new_draft:
        compare_prompt = f"""
You are an expert writing coach. Compare the following new blog draft to the author's previous blogs.\n\nPREVIOUS BLOGS:\n---\n{chr(10).join(all_contents[:3])}\n---\n\nNEW DRAFT:\n---\n{new_draft}\n---\n\nDoes the new draft match the style, tone, and structure of the previous blogs? Give a detailed comparison and a similarity score out of 10.\n"""
        llm_similarity = call_llm(compare_prompt)
    return {
        "heuristics": heuristics,
        "llm_style_summary": llm_style_summary,
        "llm_similarity": llm_similarity
    }

def summarize_style_patterns(style_analysis):
    """
    Summarize the style analysis into a prompt-friendly format.
    """
    summary = []
    heuristics = style_analysis.get("heuristics", {})
    if heuristics.get("common_headings"):
        summary.append(f"Common headings: {', '.join(heuristics['common_headings'])}")
    summary.append(f"Average blog length: {heuristics.get('average_length', 0)} characters")
    if heuristics.get("common_openings"):
        summary.append(f"Typical openings: {', '.join(heuristics['common_openings'])}")
    if heuristics.get("common_closings"):
        summary.append(f"Typical closings: {', '.join(heuristics['common_closings'])}")
    summary.append(f"Average emojis per post: {heuristics.get('emoji_per_post', 0):.1f}")
    summary.append(f"Average code blocks per post: {heuristics.get('code_blocks_per_post', 0):.1f}")
    if heuristics.get("most_common_words"):
        summary.append(f"Most common words: {', '.join(heuristics['most_common_words'])}")
    if style_analysis.get("llm_style_summary"):
        summary.append("\nLLM Style Summary:\n" + style_analysis["llm_style_summary"])
    if style_analysis.get("llm_similarity"):
        summary.append("\nLLM Similarity to previous blogs:\n" + style_analysis["llm_similarity"])
    return '\n'.join(summary) 
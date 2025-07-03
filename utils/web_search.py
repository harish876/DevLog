from duckduckgo_search import DDGS

def search_duckduckgo(query, max_results=3):
    with DDGS() as ddgs:
        results = ddgs.text(query)
        return [r['body'] for r in results][:max_results] 
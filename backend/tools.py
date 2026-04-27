"""
tools.py — The Agent's Toolkit
================================
Think of this file like a toolbox. The agent (in agent.py) decides
WHICH tool to use and WHEN. These tools are the actual actions it takes:
  1. search_company_info   → searches the web for company info
  2. search_recent_news    → finds last 30 days of news
  3. search_financials     → looks for revenue, funding, growth data
  4. search_competitors    → finds competing companies
  5. scrape_page           → reads the actual content of a webpage

Each function is decorated with @tool so LangGraph knows it's a usable tool.
"""

import httpx                           # makes HTTP requests (like fetch in JS)
from bs4 import BeautifulSoup          # parses HTML and extracts clean text
from langchain_core.tools import tool  # decorator that turns a function into an agent tool
from tavily import TavilyClient        # Tavily search client
import os                              # to read environment variables (API keys)
from dotenv import load_dotenv         # loads .env file into environment

load_dotenv()  # loads TAVILY_API_KEY and ANTHROPIC_API_KEY from .env file

# ── Create one shared Tavily client (reused across all search tools) ───────
# Tavily is a search engine built for AI agents - it returns cleaner results
# than raw Google, and it summarizes content automatically.
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def search_company_info(company_name: str) -> str:
    """
    Searches for general company information: what they do, founding year,
    headquarters, business model, CEO, employee count, etc.

    Args:
        company_name: The name of the company to research (e.g. "Stripe")

    Returns:
        A string with summarized search results about the company
    """
    # We build a specific search query — the more specific, the better results
    query = f"{company_name} company overview business model founded headquarters CEO"

    # tavily search returns top 5 results, each with title, url, and content
    results = tavily_client.search(
        query=query,
        max_results=5,           # fetch top 5 web results
        search_depth="advanced", # "advanced" reads full page content (not just snippets)
        include_answer=True      # Tavily also gives an AI-generated summary answer
    )

    # results["answer"] is Tavily's AI summary of all search results combined
    # results["results"] is a list of individual search results
    # We combine both into one big string for the agent to read
    output = f"COMPANY OVERVIEW SEARCH RESULTS:\n\n"
    output += f"Summary: {results.get('answer', 'No summary available')}\n\n"

    # Loop through each search result and add its content to our output
    for i, result in enumerate(results.get("results", []), 1):
        output += f"Source {i}: {result['title']}\n"
        output += f"URL: {result['url']}\n"
        output += f"Content: {result['content'][:800]}\n\n"  # limit to 800 chars each
        # [:800] slices the string - only first 800 characters to avoid too much text

    return output  # the agent reads this as plain text


@tool
def search_recent_news(company_name: str) -> str:
    """
    Finds the most recent news about the company from the last 30 days.
    This shows investors: product launches, controversies, partnerships, layoffs, etc.

    Args:
        company_name: The name of the company

    Returns:
        A string with recent news headlines and summaries
    """
    query = f"{company_name} latest news 2024 2025"

    results = tavily_client.search(
        query=query,
        max_results=6,
        search_depth="basic",  # "basic" is faster, just snippets, good for news
        topic="news",          # tells Tavily to prioritize news sources
        days=30                # only results from the last 30 days
    )

    output = "RECENT NEWS:\n\n"
    output += f"Summary: {results.get('answer', 'No recent news summary')}\n\n"

    for i, result in enumerate(results.get("results", []), 1):
        output += f"News {i}: {result['title']}\n"
        output += f"  Published: {result.get('published_date', 'Unknown date')}\n"
        output += f"  Source: {result['url']}\n"
        output += f"  Details: {result['content'][:600]}\n\n"

    return output


@tool
def search_financials(company_name: str) -> str:
    """
    Searches for financial data: revenue, funding rounds, valuation, growth rate,
    profitability, IPO status, investors, etc.

    Args:
        company_name: The name of the company

    Returns:
        A string with all financial information found
    """
    # We do TWO searches - one for funding, one for revenue
    # because they often appear in different sources
    funding_query = f"{company_name} funding valuation investors Series revenue ARR"
    revenue_query = f"{company_name} annual revenue profit loss financial results 2024"

    funding_results = tavily_client.search(
        query=funding_query,
        max_results=4,
        search_depth="advanced"
    )

    revenue_results = tavily_client.search(
        query=revenue_query,
        max_results=4,
        search_depth="advanced"
    )

    output = "FINANCIAL DATA:\n\n"

    # Add funding info
    output += "=== Funding & Valuation ===\n"
    output += f"Summary: {funding_results.get('answer', 'Not found')}\n\n"
    for r in funding_results.get("results", [])[:3]:
        output += f"- {r['title']}: {r['content'][:500]}\n\n"

    # Add revenue info
    output += "=== Revenue & Profitability ===\n"
    output += f"Summary: {revenue_results.get('answer', 'Not found')}\n\n"
    for r in revenue_results.get("results", [])[:3]:
        output += f"- {r['title']}: {r['content'][:500]}\n\n"

    return output


@tool
def search_competitors(company_name: str) -> str:
    """
    Finds the company's main competitors and their comparison.

    Args:
        company_name: The name of the company

    Returns:
        A string listing competitors and their differences
    """
    query = f"{company_name} competitors alternatives vs comparison market share"

    results = tavily_client.search(
        query=query,
        max_results=5,
        search_depth="advanced",
        include_answer=True
    )

    output = "COMPETITOR ANALYSIS:\n\n"
    output += f"Summary: {results.get('answer', 'No competitor data found')}\n\n"

    for i, result in enumerate(results.get("results", []), 1):
        output += f"Source {i}: {result['title']}\n"
        output += f"  {result['content'][:700]}\n\n"

    return output


@tool
def scrape_page(url: str) -> str:
    """
    Visits a specific webpage and extracts its clean text content.
    Useful when the agent finds a relevant URL and wants to read it fully.

    Args:
        url: The full URL of the webpage to read (e.g. "https://stripe.com/about")

    Returns:
        The clean text content of the page (HTML tags removed)
    """
    try:
        # httpx.get sends a GET request to the URL (like fetch in JavaScript)
        # headers pretend we're a real browser so sites don't block us
        response = httpx.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=10,    # wait max 10 seconds before giving up
            follow_redirects=True  # follow any redirects (301, 302, etc.)
        )

        # BeautifulSoup parses the HTML - like document.querySelector in JS
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style tags - we don't want JavaScript or CSS in our text
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()  # removes the tag and all its children from the tree

        # get_text() extracts all text, separator="\n" puts each block on new line
        text = soup.get_text(separator="\n", strip=True)

        # strip=True removes leading/trailing whitespace from each line
        # We limit to 3000 chars so we don't send too much to the LLM
        return f"PAGE CONTENT from {url}:\n\n{text[:3000]}"

    except Exception as e:
        # If scraping fails (timeout, 403, etc.) return a helpful message
        return f"Could not scrape {url}: {str(e)}"


# ── Export all tools as a list so agent.py can import them easily ───────────
# The agent receives this list and knows it can call any of these functions
ALL_TOOLS = [
    search_company_info,
    search_recent_news,
    search_financials,
    search_competitors,
    scrape_page
]
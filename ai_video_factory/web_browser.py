"""Full web browsing via DuckDuckGo search + page scraping.

No API key required. Uses DuckDuckGo HTML search + requests/BeautifulSoup
to extract text, images, and video links from result pages.
"""
import logging
import re
import time
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urlparse

import requests

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def duckduckgo_search(query: str, max_results: int = 10) -> List[Dict]:
    """Search DuckDuckGo and return result snippets with URLs."""
    results = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if not r.ok:
            return results

        if not BeautifulSoup:
            logger.warning("beautifulsoup4 not installed; install with: pip install beautifulsoup4")
            return results

        soup = BeautifulSoup(r.text, "html.parser")
        for res in soup.select(".result"):
            a = res.select_one(".result__a")
            snippet = res.select_one(".result__snippet")
            if a:
                href = a.get("href", "")
                # DuckDuckGo uses redirect URLs
                if href.startswith("//"):
                    href = "https:" + href
                title = a.get_text(strip=True)
                body = snippet.get_text(strip=True) if snippet else ""
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": body,
                    "source": urlparse(href).netloc,
                })
            if len(results) >= max_results:
                break
    except Exception as e:
        logger.warning("DuckDuckGo search failed: %s", e)
    return results


def scrape_page(url: str, max_chars: int = 4000) -> Dict:
    """Scrape a single web page and extract text + images."""
    out = {"url": url, "title": "", "text": "", "images": [], "videos": []}
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if not r.ok or not BeautifulSoup:
            return out

        soup = BeautifulSoup(r.text, "html.parser")

        # Remove script/style/nav/footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        out["title"] = soup.title.get_text(strip=True) if soup.title else ""

        # Extract paragraphs
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 30]
        out["text"] = "\n\n".join(paragraphs)[:max_chars]

        # Extract images
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src", "")
            if src and not src.startswith("data:"):
                if src.startswith("/"):
                    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    src = base + src
                out["images"].append({
                    "url": src,
                    "alt": img.get("alt", ""),
                })

        # Extract video embeds (YouTube, etc.)
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if "youtube" in src or "youtu.be" in src:
                out["videos"].append(src)

    except Exception as e:
        logger.warning("Page scrape failed for %s: %s", url, e)
    return out


def deep_research(query: str, max_search: int = 8, max_scrape: int = 4) -> Dict:
    """Full research pipeline: search + scrape top pages.

    Returns a research dict with:
        - search_results: list of search snippets
        - articles: list of scraped page content
        - images: aggregated image URLs
        - videos: aggregated video URLs
        - summary_text: combined text for LLM summarization
    """
    logger.info("[WEB] Deep research: %s", query)
    search_results = duckduckgo_search(query, max_results=max_search)

    articles = []
    all_images = []
    all_videos = []
    texts = []

    for i, res in enumerate(search_results[:max_scrape]):
        time.sleep(0.5)  # be polite
        page = scrape_page(res["url"])
        if page["text"]:
            articles.append(page)
            texts.append(f"--- {page['title']} ---\n{page['text']}")
        all_images.extend(page["images"])
        all_videos.extend(page["videos"])

    summary_text = "\n\n".join(texts)

    return {
        "query": query,
        "search_results": search_results,
        "articles": articles,
        "images": all_images,
        "videos": all_videos,
        "summary_text": summary_text,
    }

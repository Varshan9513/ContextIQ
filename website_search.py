
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from urllib.parse import urlparse


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ContextIQ/1.0)"
}

BLOCKED_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "pinterest.com",
    "tiktok.com"
}


def is_valid_url(url):
    """Check whether the URL is suitable for fetching."""

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = (parsed.hostname or "").lower()

        if not hostname:
            return False

        if any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in BLOCKED_DOMAINS
        ):
            return False

        return True

    except Exception:
        return False


def extract_page_content(url):
    """Extract readable text from a webpage."""

    try:
        if not is_valid_url(url):
            return None

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
            allow_redirects=True
        )

        response.raise_for_status()

        if not is_valid_url(response.url):
            return None

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if "text/html" not in content_type:
            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove unnecessary elements
        for element in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form"
        ]):
            element.decompose()

        # Extract page title
        title = (
            soup.title.get_text(strip=True)
            if soup.title
            else "Website Result"
        )

        # Prefer main article content
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.body
            or soup
        )

        text = main_content.get_text(
            separator=" ",
            strip=True
        )

        text = " ".join(text.split())

        if not text:
            return None

        return {
            "title": title,
            "text": text[:5000],
            "url": response.url
        }

    except requests.RequestException as error:
        print(f"Website extraction error: {error}")
        return None

    except Exception as error:
        print(f"Unexpected extraction error: {error}")
        return None


def website_search(question, limit=5):
    """
    Search the web and extract content from relevant websites.

    Returns a list of documents compatible with ContextIQ.
    """

    documents = []
    visited_urls = set()

    try:

        with DDGS() as ddgs:

            search_results = ddgs.text(
                question,
                max_results=limit
            )

            for result in search_results:

                url = result.get("href")

                if not url or url in visited_urls:
                    continue

                visited_urls.add(url)

                if not is_valid_url(url):
                    continue

                page = extract_page_content(url)

                if not page:
                    continue

                documents.append({
                    "source": page["title"],
                    "filename": page["title"],
                    "title": page["title"],
                    "url": page["url"],
                    "text": page["text"],
                    "content": page["text"],
                    "source_type": "Website"
                })

    except Exception as error:
        print(f"Website search error: {error}")

    return documents


# --------------------------------------------------
# TEST THE MODULE DIRECTLY
# --------------------------------------------------

if __name__ == "__main__":

    test_question = "What is artificial intelligence?"

    results = website_search(
        test_question,
        limit=5
    )

    for index, document in enumerate(results, start=1):

        print(f"\nResult {index}")
        print("Title:", document["title"])
        print("URL:", document["url"])
        print("Content:", document["text"][:300])

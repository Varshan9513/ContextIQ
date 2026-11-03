
import requests

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

def wikipedia_search(question, limit=5):
    documents = []

    try:
        # Search Wikipedia
        params = {
            "action": "query",
            "list": "search",
            "srsearch": question,
            "format": "json",
            "srlimit": limit
        }

        response = requests.get(
            WIKIPEDIA_API,
            params=params,
            headers={"User-Agent": "ContextIQ/1.0"},
            timeout=15
        )
        response.raise_for_status()

        results = response.json().get("query", {}).get("search", [])

        for result in results:
            title = result.get("title", "")

            # Fetch page summary
            summary_params = {
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": title,
                "format": "json"
            }

            summary_response = requests.get(
                WIKIPEDIA_API,
                params=summary_params,
                headers={"User-Agent": "ContextIQ/1.0"},
                timeout=15
            )
            summary_response.raise_for_status()

            pages = summary_response.json().get(
                "query", {}
            ).get("pages", {})

            for page in pages.values():
                text = page.get("extract", "")

                if text.strip():
                    documents.append({
                        "source": title,
                        "filename": title,
                        "title": title,
                        "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                        "text": text,
                        "content": text,
                        "source_type": "Wikipedia"
                    })

    except requests.exceptions.RequestException as error:
        print(f"Wikipedia connection error: {error}")

    except Exception as error:
        print(f"Wikipedia error: {error}")

    return documents


import os
import re
import requests
from urllib.parse import quote

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

API_URL = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


ALLOWED_EXTENSIONS = {
    ".py", ".java", ".js", ".ts", ".jsx", ".tsx",
    ".cpp", ".c", ".h", ".cs", ".php", ".go",
    ".rb", ".swift", ".kt", ".rs", ".scala",
    ".html", ".css", ".sql"
}

IGNORED_FOLDERS = {
    "node_modules", "venv", ".venv", ".git",
    "__pycache__", "dist", "build", ".github",
    ".vscode", "site-packages", "vendor",
    "coverage", "docs", "assets"
}

MAX_FILE_SIZE = 100000
MAX_FILES_PER_REPO = 5


# --------------------------------------------------
# API REQUEST
# --------------------------------------------------

def github_request(url, params=None):

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=(5, 15)
        )

        if response.status_code == 403:
            print("GitHub API rate limit or access restriction.")
            print(response.text[:500])
            return None

        if response.status_code == 401:
            print("GitHub token is invalid or unauthorized.")
            return None

        if response.status_code == 404:
            return None

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        print("GitHub request timed out.")
    except requests.exceptions.RequestException as error:
        print("GitHub API error:", error)

    return None


# --------------------------------------------------
# KEYWORD EXTRACTION
# --------------------------------------------------

STOP_WORDS = {
    "what", "which", "where", "when", "why", "how",
    "does", "do", "did", "can", "could", "would",
    "should", "the", "and", "for", "from", "with",
    "this", "that", "these", "those", "are", "was",
    "were", "is", "a", "an", "to", "of", "in", "on",
    "it", "be", "by", "as", "or", "about", "using",
    "use", "used", "show", "find", "give", "explain",
    "code", "source", "project", "example", "system",
    "application", "implement", "implementation"
}


def extract_keywords(question):

    words = re.findall(r"[a-zA-Z0-9_+#.-]+", question.lower())

    keywords = []

    for word in words:

        word = word.strip(".")

        if len(word) > 1 and word not in STOP_WORDS:
            if word not in keywords:
                keywords.append(word)

    return keywords


# --------------------------------------------------
# BUILD MULTIPLE SEARCH QUERIES
# --------------------------------------------------

def make_search_queries(question):

    keywords = extract_keywords(question)

    queries = []

    if keywords:
        queries.append(" ".join(keywords[:5]))

    if len(keywords) >= 2:
        queries.append(" ".join(keywords[:2]))

    if len(keywords) >= 4:
        queries.append(" ".join(keywords[2:5]))

    # Remove duplicates
    return list(dict.fromkeys(queries))


# --------------------------------------------------
# SEARCH GITHUB REPOSITORIES
# --------------------------------------------------

def search_repositories(question, limit=5):

    queries = make_search_queries(question)

    repositories = {}

    for query in queries:

        print("Searching GitHub repositories:", query)

        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }

        data = github_request(
            f"{API_URL}/search/repositories",
            params
        )

        if not data:
            continue

        for repo in data.get("items", []):

            repo_id = repo.get("full_name")

            if repo_id:
                repositories[repo_id] = repo

    results = list(repositories.values())

    results.sort(
        key=lambda repo: repo.get("stargazers_count", 0),
        reverse=True
    )

    return results[:limit]


# --------------------------------------------------
# CHECK WHETHER A FILE IS USEFUL
# --------------------------------------------------

def is_valid_code_file(path):

    path_lower = path.lower()

    parts = path_lower.split("/")

    if any(part in IGNORED_FOLDERS for part in parts):
        return False

    filename = parts[-1]

    extension = os.path.splitext(filename)[1]

    if extension not in ALLOWED_EXTENSIONS:
        return False

    if filename.startswith("."):
        return False

    return True


# --------------------------------------------------
# FIND RELEVANT FILE PATHS
# --------------------------------------------------

def select_relevant_files(tree, question, max_files=5):

    keywords = extract_keywords(question)

    candidates = []

    for item in tree:

        if item.get("type") != "blob":
            continue

        path = item.get("path", "")

        if not is_valid_code_file(path):
            continue

        if item.get("size", 0) > MAX_FILE_SIZE:
            continue

        path_words = set(
            re.findall(r"[a-zA-Z0-9_]+", path.lower())
        )

        score = sum(
            1 for word in keywords
            if word in path_words
        )

        candidates.append((score, path))

    # Prioritize matching file paths.
    # If no paths match, still retrieve some source files.
    candidates.sort(key=lambda item: item[0], reverse=True)

    return [
        path for score, path in candidates[:max_files]
    ]


# --------------------------------------------------
# DOWNLOAD SOURCE CODE
# --------------------------------------------------

def download_file(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=(5, 15)
        )

        response.raise_for_status()

        content = response.text

        if len(content) > MAX_FILE_SIZE:
            content = content[:MAX_FILE_SIZE]

        return content

    except requests.exceptions.RequestException as error:

        print("File download failed:", error)
        return ""


# --------------------------------------------------
# FETCH CODE FILES FROM A REPOSITORY
# --------------------------------------------------

def get_repository_documents(
    repository,
    question,
    max_files=MAX_FILES_PER_REPO
):

    repo_name = repository["full_name"]

    branch = repository.get("default_branch", "main")

    print("Reading repository:", repo_name)

    tree_url = (
        f"{API_URL}/repos/{repo_name}/git/trees/{quote(branch, safe='')}"
    )

    tree_data = github_request(
        tree_url,
        params={"recursive": "1"}
    )

    if not tree_data:
        return []

    tree = tree_data.get("tree", [])

    file_paths = select_relevant_files(
        tree,
        question,
        max_files
    )

    documents = []

    for path in file_paths:

        raw_url = (
            f"https://raw.githubusercontent.com/"
            f"{repo_name}/{quote(branch, safe='')}/{quote(path, safe='/')}"
        )

        content = download_file(raw_url)

        if not content.strip():
            continue

        documents.append({
            "source": repo_name,
            "title": path.split("/")[-1],
            "filename": path.split("/")[-1],
            "path": path,
            "url": (
                f"https://github.com/{repo_name}/blob/"
                f"{quote(branch, safe='')}/{quote(path, safe='/')}"
            ),
            "text": content,
            "content": content,
            "description": repository.get("description") or "",
            "stars": repository.get("stargazers_count", 0),
            "repository": repo_name,
            "source_type": "GitHub"
        })

    return documents


# --------------------------------------------------
# MAIN GITHUB SEARCH FUNCTION
# --------------------------------------------------

def github_search(question, limit=5):

    if not question or not question.strip():
        return []

    print("\n========== GITHUB SEARCH ==========")
    print("Question:", question)

    repositories = search_repositories(
        question,
        limit=limit
    )

    print("Repositories found:", len(repositories))

    all_documents = []

    for repository in repositories:

        documents = get_repository_documents(
            repository,
            question,
            max_files=MAX_FILES_PER_REPO
        )

        all_documents.extend(documents)

    # Remove duplicate files
    unique_documents = {}

    for document in all_documents:

        key = document["url"]

        unique_documents[key] = document

    results = list(unique_documents.values())

    print("Code files found:", len(results))
    print("===================================\n")

    return results


# --------------------------------------------------
# TEST THE GITHUB SEARCH MODULE
# --------------------------------------------------

if __name__ == "__main__":

    question = input("Enter your question: ")

    results = github_search(question)

    print("\nTotal code files:", len(results))

    for index, item in enumerate(results, start=1):

        print(f"\n{index}. {item['repository']}")
        print("File:", item["path"])
        print("URL:", item["url"])
        print("Stars:", item["stars"])
        print("Content preview:")
        print(item["text"][:300])

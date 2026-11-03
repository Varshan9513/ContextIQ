
import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def connect_drive():
    creds = Credentials.from_authorized_user_file(
        "token.json", SCOPES
    )
    return build("drive", "v3", credentials=creds)


def load_documents():
    service = connect_drive()

    folders = service.files().list(
        q="name='ContextIQ_Demo' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id,name)"
    ).execute()

    folder_list = folders.get("files", [])

    if not folder_list:
        print("ContextIQ_Demo folder not found!")
        return []

    folder_id = folder_list[0]["id"]

    response = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id,name,mimeType)"
    ).execute()

    documents = []

    for file in response.get("files", []):
        if not file["name"].lower().endswith(".txt"):
            continue

        request = service.files().get_media(fileId=file["id"])
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        content = buffer.getvalue().decode(
            "utf-8", errors="replace"
        )

        documents.append({
            "source": file["name"],
            "text": content
        })

    return documents


def calculate_evidence_score(doc, relevance):
    text = doc["text"].lower()

    authority = 0.0

    if "college administration" in text:
        authority = 1.0
    elif "faculty" in text:
        authority = 0.6
    elif "student" in text:
        authority = 0.2

    directness = 1.0 if "deadline is" in text else 0.3

    supersedes = (
        1.0 if "supersedes all previous" in text else 0.0
    )

    return (
        0.35 * relevance
        + 0.25 * authority
        + 0.20 * directness
        + 0.20 * supersedes
    )


def search_documents(query, documents):
    if not documents:
        print("No documents available to search.")
        return

    texts = [doc["text"] for doc in documents]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    matrix = vectorizer.fit_transform(texts + [query])

    scores = cosine_similarity(
        matrix[-1], matrix[:-1]
    ).flatten()

    max_score = max(scores)

    results = []

    for doc, score in zip(documents, scores):
        relevance = float(score) / max_score if max_score > 0 else 0

        evidence_score = calculate_evidence_score(
            doc, relevance
        )

        results.append((doc, relevance, evidence_score))

    results.sort(
        key=lambda item: item[2],
        reverse=True
    )

    print("\nCONTEXTIQ - GOOGLE DRIVE SEARCH")
    print("=" * 50)

    for doc, relevance, evidence_score in results:
        print("\nSource:", doc["source"])
        print("Relevance:", round(relevance, 3))
        print("Evidence score:", round(evidence_score, 3))
        print("Evidence:", doc["text"].replace("\n", " "))

    best_doc = results[0][0]

    print("\n" + "=" * 50)
    print("STRONGEST EVIDENCE:")
    print("Source:", best_doc["source"])
    print("Evidence:", best_doc["text"])


if __name__ == "__main__":
    print("Connecting to Google Drive...")

    documents = load_documents()

    print("Documents loaded:", len(documents))

    question = input("\nAsk ContextIQ a question: ")

    search_documents(question, documents)

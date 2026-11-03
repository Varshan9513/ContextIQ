
import os
import io
import re

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ==========================================
# GOOGLE DRIVE SETTINGS
# ==========================================

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

FOLDER_NAME = "ContextIQ_Demo"

ALLOWED_FILES = {
    "college_announcement.txt",
    "updated_circular.txt",
    "faculty_email.txt",
    "old_notice.txt",
    "student_message.txt"
}


# ==========================================
# GOOGLE DRIVE AUTHENTICATION
# ==========================================

def get_drive_service():

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


# ==========================================
# LOAD FIVE SELECTED DOCUMENTS
# ==========================================

def load_documents():

    service = get_drive_service()

    folder_response = service.files().list(
        q=(
            f"name='{FOLDER_NAME}' "
            "and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        ),
        fields="files(id, name)",
        pageSize=100
    ).execute()

    folders = folder_response.get("files", [])

    if not folders:
        raise Exception(
            f"Google Drive folder '{FOLDER_NAME}' not found."
        )

    folder_id = folders[0]["id"]

    response = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
        pageSize=100
    ).execute()

    documents = []

    for file in response.get("files", []):

        filename = file["name"]

        if filename not in ALLOWED_FILES:
            continue

        if file["mimeType"] != "text/plain":
            continue

        request = service.files().get_media(
            fileId=file["id"]
        )

        content = io.BytesIO()

        downloader = MediaIoBaseDownload(
            content,
            request
        )

        done = False

        while not done:
            _, done = downloader.next_chunk()

        text = content.getvalue().decode(
            "utf-8-sig",
            errors="ignore"
        )

        if text.strip():
            documents.append({
                "source": filename,
                "text": text.strip()
            })

    found_files = {
        document["source"]
        for document in documents
    }

    missing_files = ALLOWED_FILES - found_files

    if missing_files:
        print("Files not found or not readable:", missing_files)

    return documents


# ==========================================
# TEXT CLEANING
# ==========================================

def clean_text(text):

    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ==========================================
# SPLIT DOCUMENT INTO SENTENCES
# ==========================================

def split_sentences(text):

    text = clean_text(text)

    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 10
    ]


# ==========================================
# DOCUMENT AUTHORITY SCORE
# ==========================================

def calculate_authority(document):

    filename = document["source"].lower()
    text = document["text"].lower()

    score = 0.0

    if "updated_circular" in filename:
        score += 0.45

    elif "college_announcement" in filename:
        score += 0.35

    elif "faculty_email" in filename:
        score += 0.20

    elif "old_notice" in filename:
        score += 0.10

    elif "student_message" in filename:
        score += 0.02

    if (
        "supersedes all previous" in text
        or "supersedes previous" in text
        or "replaces all previous" in text
    ):
        score += 0.35

    if "college administration" in text:
        score += 0.20

    return min(score, 1.0)


# ==========================================
# DOCUMENT AND SENTENCE SEARCH
# ==========================================

def search_documents(query, documents):

    if not query.strip() or not documents:
        return []

    valid_documents = [
        document for document in documents
        if document.get("text", "").strip()
    ]

    if not valid_documents:
        return []

    document_texts = [
        document["text"]
        for document in valid_documents
    ]

    corpus = document_texts + [query]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    try:
        matrix = vectorizer.fit_transform(corpus)

    except ValueError:
        return []

    query_vector = matrix[-1]
    document_vectors = matrix[:-1]

    document_similarities = cosine_similarity(
        query_vector,
        document_vectors
    )[0]

    results = []

    for index, document in enumerate(valid_documents):

        relevance = float(document_similarities[index])
        authority = calculate_authority(document)

        evidence_score = (
            0.65 * relevance
            + 0.35 * authority
        )

        sentences = split_sentences(document["text"])
        sentence_results = []

        if sentences:

            try:
                sentence_vectorizer = TfidfVectorizer(
                    stop_words="english",
                    ngram_range=(1, 2),
                    sublinear_tf=True
                )

                sentence_matrix = sentence_vectorizer.fit_transform(
                    sentences + [query]
                )

                sentence_similarities = cosine_similarity(
                    sentence_matrix[-1],
                    sentence_matrix[:-1]
                )[0]

                for sentence_index, sentence in enumerate(sentences):

                    sentence_results.append({
                        "sentence": sentence,
                        "similarity": float(
                            sentence_similarities[sentence_index]
                        )
                    })

                sentence_results.sort(
                    key=lambda item: item["similarity"],
                    reverse=True
                )

            except ValueError:
                sentence_results = []

        results.append({
            "source": document["source"],
            "text": document["text"],
            "relevance": round(relevance, 3),
            "authority": round(authority, 3),
            "evidence_score": round(evidence_score, 3),
            "sentences": sentence_results
        })

    results.sort(
        key=lambda item: item["evidence_score"],
        reverse=True
    )

    return results


# ==========================================
# EXTRACT BEST ANSWER
# ==========================================

def generate_answer(question, results):

    if not results:
        return {
            "answer": "No matching information was found.",
            "source": None,
            "confidence": 0.0,
            "evidence": []
        }

    question_words = set(
        re.findall(r"\b[a-zA-Z0-9]+\b", question.lower())
    )

    stop_words = {
        "what", "is", "the", "a", "an", "for",
        "of", "in", "on", "to", "and", "are",
        "was", "were", "when", "how", "where",
        "which", "who", "do", "does", "did",
        "my", "our", "me", "we", "i", "can",
        "you", "tell", "about", "please", "give"
    }

    question_words -= stop_words

    candidates = []

    for result in results:

        for sentence_item in result["sentences"]:

            sentence = sentence_item["sentence"]

            sentence_words = set(
                re.findall(r"\b[a-zA-Z0-9]+\b", sentence.lower())
            )

            sentence_words -= stop_words

            if not sentence_words:
                continue

            overlap = (
                len(question_words.intersection(sentence_words))
                / max(len(question_words), 1)
            )

            similarity = sentence_item["similarity"]

            answer_score = (
                0.55 * similarity
                + 0.30 * overlap
                + 0.15 * result["relevance"]
            )

            candidates.append({
                "sentence": sentence,
                "source": result["source"],
                "score": answer_score,
                "similarity": similarity
            })

    if not candidates:
        return {
            "answer": "The documents do not contain a clear answer to this question.",
            "source": None,
            "confidence": 0.0,
            "evidence": []
        }

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    best = candidates[0]

    if best["similarity"] < 0.08 or best["score"] < 0.08:
        return {
            "answer": "I could not find a sufficiently relevant answer in the five documents.",
            "source": None,
            "confidence": 0.0,
            "evidence": []
        }

    return {
        "answer": best["sentence"],
        "source": best["source"],
        "confidence": round(best["score"], 3),
        "evidence": candidates[:3]
    }

import os
import time
import uuid
import traceback
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from pypdf import PdfReader
import cohere

# --- 1. Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "aichatbot")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBED_MODEL = os.getenv("COHERE_EMBED_MODEL", "embed-english-v3.0")

# --- 2. Initialize Clients ---
if not PINECONE_API_KEY or not COHERE_API_KEY:
    print("❌ Error: Missing API Keys in .env file.")
    exit(1)

pc = Pinecone(api_key=PINECONE_API_KEY)
co = cohere.Client(COHERE_API_KEY)

def ensure_index():
    print(f"🔍 Checking Pinecone Index: '{PINECONE_INDEX}'...")
    existing_indexes = [i['name'] for i in pc.list_indexes()]
    if PINECONE_INDEX not in existing_indexes:
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
        )
        while not pc.describe_index(PINECONE_INDEX).status["ready"]:
            time.sleep(2)
    print(f"✅ Index '{PINECONE_INDEX}' is ready.")

def extract_and_chunk_data():
    """Reads both PDFs and Text files from the data folder."""
    data_path = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_path):
        os.makedirs(data_path)
        return []

    docs = []
    print(f"📂 Reading data from: {data_path}")
    
    for filename in os.listdir(data_path):
        file_path = os.path.join(data_path, filename)
        
        # --- Handle PDF files ---
        if filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(file_path)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if len(text.strip()) > 10:
                        docs.append({
                            "id": str(uuid.uuid4()),
                            "text": text.strip(),
                            "metadata": {"source": filename, "page": i + 1}
                        })
                print(f"   📄 Processed PDF: {filename}")
            except Exception as e:
                print(f"   ❌ Failed PDF {filename}: {e}")

        # --- Handle Text files (Safe Fallback) ---
        elif filename.lower().endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Chunk text files (1000 chars each)
                    chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
                    for i, chunk in enumerate(chunks):
                        docs.append({
                            "id": str(uuid.uuid4()),
                            "text": chunk.strip(),
                            "metadata": {"source": filename, "chunk": i + 1}
                        })
                print(f"   📝 Processed Text: {filename}")
            except Exception as e:
                print(f"   ❌ Failed Text {filename}: {e}")

    return docs

def embed_and_upsert(docs):
    if not docs:
        print("⚠️ No valid text found. Ingestion skipped.")
        return

    index = pc.Index(PINECONE_INDEX)
    batch_size = 96
    print(f"🚀 Embedding and Uploading {len(docs)} chunks...")

    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        texts = [d["text"] for d in batch]
        try:
            response = co.embed(texts=texts, model=EMBED_MODEL, input_type="search_document")
            embeddings = response.embeddings
            vectors = []
            for doc, emb in zip(batch, embeddings):
                vectors.append({
                    "id": doc["id"],
                    "values": emb,
                    "metadata": {"text": doc["text"], "source": doc["metadata"]["source"]}
                })
            index.upsert(vectors=vectors)
            print(f"   ✅ Uploaded batch {i//batch_size + 1}")
        except Exception:
            traceback.print_exc()

def main():
    start_time = time.time()
    ensure_index()
    documents = extract_and_chunk_data() # Updated function call
    if documents:
        embed_and_upsert(documents)
        print(f"\n🎉 Ingestion Complete in {round(time.time() - start_time, 2)}s!")
    else:
        print("\n⚠️ No data extracted. Check if your PDFs are scanned images.")

if __name__ == "__main__":
    main()
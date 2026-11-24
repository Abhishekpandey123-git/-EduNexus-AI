import os
import re
import traceback
import uuid
from pinecone import Pinecone
import cohere
from groq import Groq
from app.utils.data import (
    UNIVERSITY_DATABASE,
    MAIN_MENU_BUTTONS,
    ADMISSION_MENU_BUTTONS,
    STUDY_MENU_BUTTONS,
    CANCEL_BUTTONS,
)

# --- 1. Configuration & Clients ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX") or "aichatbot"
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBED_MODEL = os.getenv("COHERE_EMBED_MODEL", "embed-english-v3.0")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

pc = Pinecone(api_key=PINECONE_API_KEY) if PINECONE_API_KEY else None
co = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# --- 2. Helper: AI Generator ---
_CACHED_MODEL = None

def _resolve_model():
    global _CACHED_MODEL
    if _CACHED_MODEL:
        return _CACHED_MODEL
    try:
        models = [
            m.id for m in groq_client.models.list().data
            if not any(k in m.id.lower() for k in ("whisper", "guard", "tts", "playai"))
        ]
        print(f"[GROQ] Available models: {models}", flush=True)
        if models:
            _CACHED_MODEL = models[0]
            return _CACHED_MODEL
    except Exception as e:
        print(f"[GROQ] Model list error: {e}", flush=True)
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def _call_groq(prompt, system_instruction="You are a helpful Educational Assistant."):
    if not groq_client:
        return "System Error: Groq API Key missing in `.env`."
    model_to_use = _resolve_model()
    try:
        completion = groq_client.chat.completions.create(
            model=model_to_use,
            messages=[
                {"role": "system", "content": f"{system_instruction} Keep answers concise, accurate, and well-formatted."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        return completion.choices[0].message.content or "No response generated."
    except Exception as e:
        print(f"Groq API Error ({model_to_use}): {e}", flush=True)
        return f"⚠️ Groq API Error ({model_to_use}): {e}"


# --- 3. Feature: Study Mode (Learn from Notes) ---
def handle_note_upload(note_text, user_id):
    if not note_text or len(note_text.strip()) < 10:
        return "Note is too short to process."
    if not pc or not co:
        return "AI services are not configured. Check PINECONE_API_KEY and COHERE_API_KEY in `.env`."

    try:
        index = pc.Index(INDEX_NAME)
        chunks = [note_text[i : i + 1000] for i in range(0, len(note_text), 1000)]

        for chunk in chunks:
            emb_resp = co.embed(texts=[chunk], model=EMBED_MODEL, input_type="search_document")
            vector_id = str(uuid.uuid4())
            index.upsert(
                vectors=[
                    {
                        "id": vector_id,
                        "values": emb_resp.embeddings[0],
                        "metadata": {
                            "text": chunk,
                            "user_id": user_id,
                            "type": "private_note",
                        },
                    }
                ]
            )
        return "✅ I have learned your notes! You can now ask me questions about them in Study Mode."
    except Exception:
        traceback.print_exc()
        return "❌ Error uploading notes."


# --- 4. Refined RAG Logic (Mode Aware) ---
def get_rag_answer(query: str, mode="josaa", user_id="student_demo_123") -> dict:
    buttons = STUDY_MENU_BUTTONS if mode == "study" else ADMISSION_MENU_BUTTONS
    if not pc or not co:
        return {"markdown": "AI services are not configured.", "buttons": buttons}

    try:
        emb_resp = co.embed(model=EMBED_MODEL, input_type="search_query", texts=[query])
        qvec = emb_resp.embeddings[0]

        if mode == "study":
            search_filter = {"user_id": {"$eq": user_id}}
            system_role = "You are a Private AI Tutor. Answer based ONLY on the student's provided notes."
            no_context_msg = "I couldn't find information about that in your uploaded notes."
            top_k = 4
            min_score = 0.30
        else:
            search_filter = {"user_id": {"$exists": False}}
            system_role = (
                "You are a JoSAA 2025 Admission Counselor. Use ONLY the provided cutoff rows to answer. "
                "When given a rank, list matching institutes/programs whose Closing Rank is >= the student's rank "
                "(or closest to it) in a clean Markdown table with Opening and Closing Ranks."
            )
            no_context_msg = f"I couldn't find specific rank data in Pinecone index '{INDEX_NAME}' for that query."
            top_k = 5
            min_score = 0.20

        index = pc.Index(INDEX_NAME)
        res = index.query(vector=qvec, top_k=top_k, include_metadata=True, filter=search_filter)
        matches = res.get("matches", [])
        print(f"[RAG] index={INDEX_NAME} matches={len(matches)}", flush=True)

        contexts = [m["metadata"].get("text", "") for m in matches if m.get("score", 0) > min_score]

        if not contexts:
            return {"markdown": no_context_msg, "buttons": buttons}

        context_block = "\n".join(contexts)
        prompt = f"Context Data:\n{context_block}\n\nStudent Question: {query}"

        answer = _call_groq(prompt, system_role)
        return {"markdown": answer, "buttons": buttons}

    except Exception as e:
        traceback.print_exc()
        return {"markdown": f"⚠️ Error retrieving information: {e}", "buttons": buttons}


# --- 5. Study Mode Tool (Summarize Notes) ---
def get_study_tool_action(query, user_id, action="summarize") -> dict:
    if not pc or not co:
        return {"markdown": "AI services are not configured.", "buttons": STUDY_MENU_BUTTONS}

    try:
        emb_resp = co.embed(model=EMBED_MODEL, input_type="search_query", texts=["key concepts summary notes"])
        index = pc.Index(INDEX_NAME)
        res = index.query(
            vector=emb_resp.embeddings[0],
            top_k=5,
            include_metadata=True,
            filter={"user_id": {"$eq": user_id}},
        )
        contexts = [m["metadata"].get("text", "") for m in res.get("matches", []) if m.get("metadata")]

        if not contexts:
            return {
                "markdown": "I couldn't find any uploaded notes to summarize. Upload a `.pdf` or `.txt` file using 📎 first.",
                "buttons": STUDY_MENU_BUTTONS,
            }

        notes_block = "\n\n".join(contexts)
        answer = _call_groq(
            f"Summarize the following notes clearly:\n\n{notes_block}",
            "You are a Private AI Tutor summarizing the student's uploaded notes.",
        )
        return {"markdown": answer, "buttons": STUDY_MENU_BUTTONS}
    except Exception as e:
        traceback.print_exc()
        return {"markdown": f"⚠️ Error summarizing notes: {e}", "buttons": STUDY_MENU_BUTTONS}


# --- 6. Main Message Processor ---
def process_message(query: str, session: dict, mode: str = None, user_id: str = "student_demo_123") -> dict:
    state = session.get("chat_state")
    query_lower = query.lower().strip()

    if mode:
        session["mode"] = mode
    active_mode = session.get("mode", "josaa")

    if "study mode" in query_lower:
        session["mode"] = "study"
        session.pop("chat_state", None)
        return {
            "markdown": "📚 **Study Mode Active.** Upload a PDF/TXT using 📎 or ask a question about your notes.",
            "buttons": STUDY_MENU_BUTTONS,
        }

    if "admission mode" in query_lower or "josaa mode" in query_lower:
        session["mode"] = "josaa"
        session.pop("chat_state", None)
        return {
            "markdown": "🏛️ **Admission Mode Active.** Searching JoSAA 2025 Data.",
            "buttons": ADMISSION_MENU_BUTTONS,
        }

    if query_lower in ["cancel", "main menu", "menu", "⬅ menu"]:
        session.pop("chat_state", None)
        if active_mode == "study":
            return {
                "markdown": "📚 **Study Assistant Menu**\nWhat would you like to do with your notes?",
                "buttons": STUDY_MENU_BUTTONS,
            }
        return {
            "markdown": "🏛️ **JoSAA Counseling Menu**\nI can suggest colleges based on AIR, Home State, or Category.",
            "buttons": ADMISSION_MENU_BUTTONS,
        }

    if "air based" in query_lower:
        session["chat_state"] = "AWAITING_AIR"
        return {
            "markdown": "🌍 **All India Quota (AIR Based)**\nThis search ignores your state and looks at pure rank across IITs, NITs, and IIITs. Please enter your **CRL Rank**.",
            "buttons": CANCEL_BUTTONS,
        }

    if state == "AWAITING_AIR" or re.search(r"\b(crl|air|rank)\b.*\d+", query_lower):
        digits = re.findall(r"\d+", query.replace(",", ""))
        if digits:
            session.pop("chat_state", None)
            rank_val = int(digits[0])
            enriched_query = (
                f"Institute Program Category OPEN Gender-Neutral Opening Rank Closing Rank around {rank_val}. "
                f"Show programs where Closing Rank is >= {rank_val} for CRL Rank {rank_val}."
            )
            return get_rag_answer(enriched_query, mode="josaa", user_id=user_id)

    if "home state" in query_lower:
        session["chat_state"] = "AWAITING_HOME_STATE"
        return {
            "markdown": "🏠 **Home State / Domicile Quota**\nIn NITs, 50% of seats are reserved for students from that state. **Which state is your domicile?**",
            "buttons": ["Delhi", "UP", "Maharashtra", "Other", "Cancel"],
        }

    if state == "AWAITING_HOME_STATE":
        session["domicile_state"] = query.strip()
        session["chat_state"] = "AWAITING_HS_RANK"
        return {
            "markdown": (
                f"🏠 Domicile set to **{query.strip()}**.\n\n"
                "*(Note: Currently IIT All-India [AI] cutoffs from Pages 1–100 are indexed; NIT Home State [HS] pages appear later in the JoSAA PDF.)*\n\n"
                "Enter your **CRL Rank** to see available All-India programs:"
            ),
            "buttons": CANCEL_BUTTONS,
        }

    if state == "AWAITING_HS_RANK":
        digits = re.findall(r"\d+", query.replace(",", ""))
        if digits:
            session.pop("chat_state", None)
            rank_val = int(digits[0])
            domicile = session.get("domicile_state", "your state")
            enriched_query = (
                f"Student from {domicile} with CRL Rank {rank_val}. "
                f"Find programs with Opening Rank and Closing Rank >= {rank_val}."
            )
            return get_rag_answer(enriched_query, mode="josaa", user_id=user_id)

    if "category check" in query_lower:
        session["chat_state"] = "AWAITING_CATEGORY"
        return {
            "markdown": "📊 **Category Check**\nSelect or type your category (**OPEN, EWS, OBC-NCL, SC, ST**) and your category rank:",
            "buttons": ["EWS", "OBC-NCL", "SC", "ST", "Cancel"],
        }

    if state == "AWAITING_CATEGORY":
        session.pop("chat_state", None)
        return get_rag_answer(
            f"JoSAA 2025 cutoffs for Category {query.strip()} Opening Rank Closing Rank",
            mode="josaa",
            user_id=user_id,
        )

    if "check eligibility" in query_lower:
        session["chat_state"] = "ELIG_LEVEL"
        return {
            "markdown": "🎓 **University Checker**\nAre you looking for **Bachelors** or **Masters**?",
            "buttons": ["Bachelors", "Masters", "Cancel"],
        }

    if state == "ELIG_LEVEL":
        level = "Bachelors" if "bachelor" in query_lower else "Masters" if "master" in query_lower else None
        if level:
            session.pop("chat_state", None)
            unis = "\n".join(f"- {u}" for u in UNIVERSITY_DATABASE.get(level, []))
            return {
                "markdown": f"🎓 **Eligible {level} Institutes:**\n\n{unis}",
                "buttons": ADMISSION_MENU_BUTTONS,
            }
        return {
            "markdown": "Please select **Bachelors** or **Masters**.",
            "buttons": ["Bachelors", "Masters", "Cancel"],
        }

    if active_mode == "study" and len(query) > 100:
        response_text = handle_note_upload(query, user_id)
        return {"markdown": response_text, "buttons": STUDY_MENU_BUTTONS}

    if "summarize" in query_lower and active_mode == "study":
        return get_study_tool_action(query, user_id, action="summarize")

    return get_rag_answer(query, mode=active_mode, user_id=user_id)


def get_status():
    if not groq_client or not pc or not co:
        return False, ["API Clients missing"]
    return True, []

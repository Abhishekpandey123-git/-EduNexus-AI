import os
import re
import traceback
import uuid
from pinecone import Pinecone
import cohere
from groq import Groq
from app.utils.data import UNIVERSITY_DATABASE, MAIN_MENU_BUTTONS, CANCEL_BUTTONS

# --- 1. Configuration & Clients ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX", "aichatbot") # Changed to your index name
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBED_MODEL = os.getenv("COHERE_EMBED_MODEL", "embed-english-v3.0")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

pc = Pinecone(api_key=PINECONE_API_KEY) if PINECONE_API_KEY else None
co = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- 2. Helper: AI Generator ---
def _call_groq(prompt, system_instruction="You are a helpful Educational Assistant."):
    if not groq_client: return "System Error: Groq API Key missing."
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": f"{system_instruction} Keep answers concise and professional."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Groq API Error: {e}")
        return "I'm having trouble connecting to my AI brain."

# --- 3. Feature: Study Mode (Learn from Notes) ---
def handle_note_upload(note_text, user_id):
    """Chunks, embeds, and uploads private notes to Pinecone."""
    if not note_text or len(note_text) < 10:
        return "Note is too short to process."
    
    try:
        index = pc.Index(INDEX_NAME)
        # Split notes into 1000 char chunks
        chunks = [note_text[i:i+1000] for i in range(0, len(note_text), 1000)]
        
        for chunk in chunks:
            emb_resp = co.embed(texts=[chunk], model=EMBED_MODEL, input_type="search_document")
            vector_id = str(uuid.uuid4())
            index.upsert(vectors=[{
                "id": vector_id,
                "values": emb_resp.embeddings[0],
                "metadata": {
                    "text": chunk,
                    "user_id": user_id,  # Tagging as private
                    "type": "private_note"
                }
            }])
        return "✅ I have learned your notes! You can now ask me questions about them in Study Mode."
    except Exception as e:
        traceback.print_exc()
        return "❌ Error uploading notes."

# --- 4. Refined RAG Logic (Mode Aware) ---
def get_rag_answer(query: str, mode="josaa", user_id="default") -> dict:
    if not pc or not co: 
        return {"markdown": "AI services are not configured.", "buttons": MAIN_MENU_BUTTONS}
    
    try:
        # 1. Embed Query
        emb_resp = co.embed(model=EMBED_MODEL, input_type="search_query", texts=[query])
        qvec = emb_resp.embeddings[0]
        
        # 2. Setup Filter based on Mode
        if mode == "study":
            search_filter = {"user_id": {"$eq": user_id}}
            system_role = "You are a Private AI Tutor. Answer based ONLY on the student's provided notes."
            no_context_msg = "I couldn't find information about that in your uploaded notes."
        else:
            # Global Mode (JoSAA) - looks for data with specific source or 'global' type
            search_filter = {"user_id": {"$exists": False}} # Or {"source": {"$eq": "nsdshg.pdf"}}
            system_role = "You are an Admission Assistant. Use the JoSAA rank data to answer questions."
            no_context_msg = "I couldn't find specific rank data for that query."

        # 3. Search Pinecone
        index = pc.Index(INDEX_NAME)
        res = index.query(vector=qvec, top_k=4, include_metadata=True, filter=search_filter)
        
        contexts = [m["metadata"].get("text", "") for m in res["matches"] if m["score"] > 0.40]
        
        if not contexts:
            return {"markdown": no_context_msg, "buttons": MAIN_MENU_BUTTONS}

        # 4. Generate Response
        context_block = "\n".join(contexts)
        prompt = f"Context Data:\n{context_block}\n\nStudent Question: {query}"
        
        answer = _call_groq(prompt, system_role)
        return {"markdown": answer, "buttons": MAIN_MENU_BUTTONS}
        
    except Exception:
        traceback.print_exc()
        return {"markdown": "Error retrieving information.", "buttons": MAIN_MENU_BUTTONS}

# --- 5. Main Message Processor ---
def process_message(query: str, session: dict) -> dict:
    state = session.get("chat_state")
    query_lower = query.lower().strip()
    
    # Track mode in session (default to JoSAA)
    mode = session.get("mode", "josaa")
    user_id = "user_123" # In production, this would come from login

    # --- Mode Switching Commands ---
    if "study mode" in query_lower:
        session["mode"] = "study"
        return {"markdown": "📚 **Study Mode Active.** Paste your notes here for me to learn them, or ask a question about previously uploaded notes.", "buttons": ["Main Menu"]}
    
    if "admission mode" in query_lower or "josaa mode" in query_lower:
        session["mode"] = "josaa"
        return {"markdown": "🏛️ **Admission Mode Active.** I will now answer based on JoSAA 2025 Rank data.", "buttons": ["Main Menu"]}

    # --- Global Commands ---
    if query_lower in ["cancel", "main menu", "⬅ menu"]:
        session.clear()
        return {"markdown": "How can I assist you today?", "buttons": ["Admission Mode 🏛️", "Study Mode 📚", "Check Eligibility 🎓"]}

    # --- Feature: Note Upload Detection (In Study Mode) ---
    if mode == "study" and len(query) > 100:
        response_text = handle_note_upload(query, user_id)
        return {"markdown": response_text, "buttons": ["Main Menu"]}

    # --- Feature: Eligibility Flow (Existing) ---
    if query_lower == "check eligibility 🎓":
        session["chat_state"] = "ELIG_LEVEL"
        return {"markdown": "🎓 **University Checker**\nAre you looking for **Bachelors** or **Masters**?", "buttons": ["Bachelors", "Masters", "Cancel"]}

    # ... (Keep your existing state-based eligibility logic here) ...

    # --- Fallback to RAG (Uses the active mode) ---
    return get_rag_answer(query, mode=mode, user_id=user_id)

def process_message(query: str, session: dict) -> dict:
    state = session.get("chat_state")
    query_lower = query.lower().strip()
    mode = session.get("mode", "josaa")
    user_id = "user_123"

    # --- Mode Switching ---
    if "study mode" in query_lower:
        session["mode"] = "study"
        return {"markdown": "📚 **Study Mode Active.** How can I help with your learning?", "buttons": STUDY_MENU_BUTTONS}
    
    if "admission mode" in query_lower or "josaa mode" in query_lower:
        session["mode"] = "josaa"
        return {"markdown": "🏛️ **Admission Mode Active.** Searching JoSAA 2025 Data.", "buttons": ADMISSION_MENU_BUTTONS}

    # --- Dynamic Main Menu Logic ---
    if query_lower in ["cancel", "main menu", "menu"]:
        session.pop("chat_state", None) # Clear sub-states
        if mode == "study":
            return {"markdown": "📚 **Study Assistant Menu**\nWhat would you like to do with your notes?", "buttons": STUDY_MENU_BUTTONS}
        else:
            return {"markdown": "🏛️ **JoSAA Counseling Menu**\nI can suggest colleges based on AIR, Home State, or Category.", "buttons": ADMISSION_MENU_BUTTONS}

    # --- Feature: Admission Insights ---
    if "air based" in query_lower:
        return {"markdown": "🌍 **All India Quota (AIR Based)**\nThis search ignores your state and looks at pure rank across IITs, NITs, and IIITs. Please enter your **CRL Rank**.", "buttons": CANCEL_BUTTONS}

    if "home state" in query_lower:
        return {"markdown": "🏠 **Home State / Domicile Quota**\nIn NITs, 50% of seats are reserved for students from that state. **Which state is your domicile?**", "buttons": ["Delhi", "UP", "Maharashtra", "Other", "Cancel"]}

    # --- Feature: Summarize Notes (Study Mode) ---
    if "summarize" in query_lower and mode == "study":
        return get_study_tool_action(query, user_id, action="summarize")

    # ... (Rest of your existing RAG and Eligibility code) ...

def get_study_tool_action(query, user_id, action="summarize"):
    """Specific tool for Study Mode to summarize or quiz."""
    # This calls Pinecone to get the notes and then Groq to summarize
    # (Implementation similar to your RAG function but with a 'summarize' prompt)
    pass

def get_status():
    if not groq_client or not pc or not co:
        return False, ["API Clients missing"]
    return True, []
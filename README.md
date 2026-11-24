# 🎓 EduNexus AI

EduNexus AI is a dual-mode AI Admission Counselor and Study Assistant built with **Flask**, **Pinecone**, **Cohere**, and **Groq**.

## 🚀 Features

- **Admission Mode 🏛️ (JoSAA 2025 RAG)**: Search Opening & Closing Ranks by AIR/CRL Rank, Home State Quota, Category, or Eligibility across ingested JoSAA cutoff datasets (Pages 1–100 included in `data/`).
- **Study Mode 📚**: Upload `.pdf` or `.txt` study notes via the attachment button (`📎`) or paste text directly to embed private notes into Pinecone and ask questions or generate summaries.
- **Full-Viewport Web UI**: Clean, full-screen chat interface served directly from Flask (`http://127.0.0.1:5000/`) with Markdown table rendering and quick-action buttons.

## 📁 Project Structure

```text
EduNexus-AI/
├── app/
│   ├── chatbot/
│   │   ├── __init__.py
│   │   └── core.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── health.py
│   │   └── upload.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── data.py
│   ├── __init__.py
│   └── main.py
├── data/
│   ├── JoSAA_2025_Round1_Pages_1_to_10.xlsx
│   ├── JoSAA_2025_Round1_Pages_11_to_50.xlsx
│   └── JoSAA_2025_Round1_Pages_51_to_100.xlsx
├── uploads/
├── .env.example
├── .gitignore
├── index.html
├── ingest.py
├── LICENSE
├── README.md
├── requirements.txt
├── style.css
└── wsgi.py
```

## ⚙️ Setup & Run (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Add your PINECONE_API_KEY, COHERE_API_KEY, and GROQ_API_KEY in .env
python ingest.py
python wsgi.py
```

Open **`http://127.0.0.1:5000/`** in your browser.

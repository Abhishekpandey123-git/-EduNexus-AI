# 🎓 EduNexus AI

EduNexus AI is an AI-powered college recommendation platform designed to help JEE aspirants find suitable engineering colleges based on their JEE rank, category, and other admission-related criteria.

The system analyzes student information and provides relevant college recommendations, making the college selection process easier and more personalized.

## 🚀 Features

- 🎯 College recommendations based on JEE rank
- 👤 Category-based recommendations (General, OBC, SC, ST, etc.)
- 🏫 Helps students discover suitable engineering colleges
- 🤖 AI-powered chatbot for student queries
- 📄 College and admission data processing
- 📊 Uses JEE and college-related data for recommendations
- 💬 Simple and interactive user interface
- ⚡ FastAPI-based backend

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** HTML, CSS
- **AI/Chatbot:** Python-based AI chatbot
- **Data Processing:** Python
- **Server:** Uvicorn

## 📁 Project Structure

    EduNexus-AI/
    │
    ├── app/
    │   ├── chatbot/
    │   │   └── core.py
    │   ├── routes/
    │   │   ├── chat.py
    │   │   ├── health.py
    │   │   └── upload.py
    │   ├── utils/
    │   │   └── data.py
    │   └── main.py
    │
    ├── data/
    ├── index.html
    ├── style.css
    ├── ingest.py
    ├── requirements.txt
    ├── wsgi.py
    └── README.md

## ⚙️ Installation

### 1. Clone the repository

    git clone <your-repository-url>

### 2. Navigate to the project

    cd EduNexus-AI

### 3. Create a virtual environment

    python -m venv venv

### 4. Activate the virtual environment

Windows:

    venv\Scripts\activate

### 5. Install dependencies

    pip install -r requirements.txt

### 6. Configure environment variables

Create a `.env` file and add the required API keys and configuration.

> Never upload your `.env` file to GitHub.

### 7. Run the application

    uvicorn app.main:app --reload

## 💡 How It Works

1. The student enters their JEE rank and category.
2. The system processes the student's details.
3. College admission data and previous cutoff information are analyzed.
4. The system identifies colleges suitable for the student's rank and category.
5. Relevant college recommendations are presented to the student.
6. Students can interact with the AI chatbot for additional guidance.

## 🎯 Project Objective

The objective of EduNexus AI is to simplify the college selection process for JEE aspirants. Instead of manually searching through large amounts of cutoff and admission data, students can use the platform to quickly identify colleges that match their rank and category.

## 🔮 Future Improvements

- JEE Main and JEE Advanced support
- JoSAA cutoff integration
- Branch-wise college recommendations
- State and gender-based filtering
- College comparison feature
- Personalized preference-based recommendations
- Real-time cutoff updates
- Improved AI-powered counselling
- College prediction probability

## 👨‍💻 Author

**Abhishek Pandey**

## 📜 Disclaimer

College recommendations provided by EduNexus AI are for informational and guidance purposes only. Actual admission results may vary depending on official cutoffs, seat availability, counselling rounds, category, and admission policies.

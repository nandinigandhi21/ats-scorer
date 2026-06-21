# ATS Resume Scorer

A web app that scores how well a resume matches a job description and returns actionable feedback. Built with FastAPI + Streamlit, using spaCy and Sentence Transformers for NLP and the Groq API for LLM-generated suggestions.

## What it does

1. Upload a resume (PDF / DOC / DOCX) and paste a job description.
2. The backend parses the resume, extracts skills and experience, and compares them to the JD using semantic similarity.
3. You get an ATS score, a breakdown by category (formatting, keywords, content, skill validation, ATS compatibility), and LLM-written suggestions for what to improve.
4. Past analyses are saved to your account so you can revisit them.

## Tech stack

- **Frontend:** Streamlit
- **Backend:** FastAPI (Python)
- **NLP:** spaCy (`en_core_web_md`), Sentence Transformers (`all-MiniLM-L6-v2`)
- **LLM:** Groq API (Llama 3)
- **Auth + Database:** Supabase (email/password and Google OAuth)
- **PDF report export:** WeasyPrint + Jinja2

## Project structure

```
ai-resume-ats/
├── backend/              FastAPI app, NLP services, API routes
├── frontend/             Streamlit app, views, components
├── jupyter notebooks/    Research and dataset prep (not used at runtime)
├── requirements.txt      Combined backend + frontend dependencies
├── .env.example          Template for environment variables
└── run.ps1               PowerShell startup script (Windows)
```

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd ai-resume-ats
python -m venv ai-resume
```

Activate the environment:
- **Windows**: `ai-resume\Scripts\activate` (or `. .\ai-resume\Scripts\activate.ps1` in PowerShell)
- **macOS / Linux**: `source ai-resume/bin/activate`

### 2. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

WeasyPrint needs system libraries on Linux/macOS. For details, see the [WeasyPrint installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation).

For Linux:
```bash
# Fedora
sudo dnf install -y cairo pango gdk-pixbuf2 libffi

# Debian / Ubuntu
sudo apt install -y libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libffi-dev
```

### 3. Configure environment variables and secrets

Copy the `.env` template and fill in your keys:

```bash
cp .env.example .env
```

You need:
- A **Supabase** project — grab `SUPABASE_URL`, `SUPABASE_KEY` (service role), and `SUPABASE_ANON_KEY` from Project Settings → API.
- A **Groq** API key from [console.groq.com](https://console.groq.com).
- (Optional) Google OAuth set up in the Supabase dashboard if you want Google sign-in.

#### Streamlit Secrets (Optional)
The Streamlit frontend can also read configuration from `frontend/.streamlit/secrets.toml`. If you want to use this instead of a global `.env` file, copy the template and fill it in:

```bash
cp frontend/.streamlit/secrets.toml.example frontend/.streamlit/secrets.toml
```

### 4. Run the application

#### On Windows (Auto-start both)
If you are on Windows, you can start both the backend and frontend servers with a single command using the provided script:
```powershell
.\run.ps1
```

#### Running manually (Any OS)
If you prefer to start the servers separately:

**Run the backend**:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
The API is now running at `http://localhost:8000`.

**Run the frontend**:
Open a new terminal window, activate your virtual environment, and run:
```bash
streamlit run frontend/streamlit_app.py
```
The Streamlit app opens at `http://localhost:8501`.

## Notes for users/developers

- **Never commit `.env` or `secrets.toml`** — they contain sensitive API keys. Both are listed in `.gitignore` to prevent leaks.
- The first run downloads the Sentence Transformer model (~80 MB) and the spaCy language model. They are cached locally afterward.
- If you don't have a Groq key yet, the scoring still works — only the LLM-generated feedback section will be empty.
- `jupyter notebooks/` are for research and dataset exploration and aren't required to run the application.


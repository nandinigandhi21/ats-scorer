import os
from pathlib import Path

# Force HuggingFace / Transformers to offline mode by default to prevent
# startup crashes/delays when loading SentenceTransformer models in sandbox environments.
if os.getenv("HF_HUB_OFFLINE") is None:
    os.environ["HF_HUB_OFFLINE"] = "1"
if os.getenv("TRANSFORMERS_OFFLINE") is None:
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Load .env from the project root explicitly —
# load_dotenv() with no args relies on caller-frame inspection that can fail
# silently under uvicorn reload, leaving env vars unset.
try:
    from dotenv import load_dotenv
    # Check current working directory first, fallback to module-relative path
    _ENV_PATH = Path.cwd() / '.env'
    if not _ENV_PATH.exists():
        _ENV_PATH = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(_ENV_PATH)
except ImportError:
    pass

#api metadata
APP_TITLE='ATS RESUME ANALYZER API'
APP_VERSION='1.0.0'
APP_DESCRIPTION='analyse resumes against job description using nlp + ml'

# Allowed origins can be overridden via ALLOWED_ORIGINS env var (comma-separated).
_origins = os.getenv('ALLOWED_ORIGINS')
ALLOWED_ORIGINS = (
    [origin.strip() for origin in _origins.split(',')] if _origins else [
        'https://appapppy-ktwxupi73vqhjzweksze9d.streamlit.app/',
        'http://localhost:8501',
        'http://127.0.0.1:8501',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]
)

#file 
MAX_FILE_SIZE_MB=5
MAX_FILE_SIZE_BYTES=MAX_FILE_SIZE_MB*1024*1024

#Supported MIME types and their short names
SUPPORTED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
}

SUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx'}

SPACY_MODEL_PRIMARY="en_core_web_md" #better accuracy
SPACY_MODEL_SECONDARY='en_core_web_sm' 
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

# Score component weights — this is business logic treated as config
SCORE_WEIGHTS = {
    "formatting": 20, "keywords": 25, "content": 25,
    "skill_validation": 15, "ats_compatibility": 15,
}

JD_KEYWORD_WEIGHT=0.6
JD_SEMANTIC_WEIGHT=0.4

SUPABASE_URL       = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY       = os.getenv('SUPABASE_KEY', '')          # service_role — DB writes (bypasses RLS)
SUPABASE_ANON_KEY  = os.getenv('SUPABASE_ANON_KEY', '')     # public anon — frontend auth calls
SUPABASE_JWT_SECRET= os.getenv('SUPABASE_JWT_SECRET', '')   # used by backend to verify access tokens
GROQ_API_KEY       = os.getenv('GROQ_API_KEY', '')

# Fast failure for missing critical configuration in production
if not SUPABASE_JWT_SECRET and os.getenv('ENV') == 'production':
    raise RuntimeError("SUPABASE_JWT_SECRET is required in production environment.")



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from routers.extract import router as extract_router

load_dotenv()

app = FastAPI(title="InvoiceAI API", version="1.0.0")

default_origins = [
    "http://localhost:5173",
    "https://ai-invoice-document-extraction-tool.vercel.app",
]

env_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
allow_origins = list(dict.fromkeys(default_origins + env_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract_router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "InvoiceAI backend is running"}
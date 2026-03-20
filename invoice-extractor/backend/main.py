from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers.extract import router as extract_router

load_dotenv()

app = FastAPI(title="InvoiceAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ai-invoice-document-extraction-tool.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract_router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "InvoiceAI backend is running"}
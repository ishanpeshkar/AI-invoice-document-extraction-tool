# Automated Invoice & Document Data Extraction Tool

An end-to-end AI-powered tool that automatically extracts structured data from vendor invoices and documents. Upload a PDF, image, Word document, or paste raw text — the tool extracts key fields like vendor name, GSTIN, invoice number, line items, and tax breakdown, stores them in a database, and displays a summary dashboard.

Built as part of an AI internship at EmergeFlow Technologies.

---

## Features

- **Multi-format input** — PDF, JPG, PNG, DOCX, or plain text
- **Dual extraction modes**
  - AI Direct (Groq LLaMA 4 Scout) — vision-based, handles any invoice layout
  - OCR Pipeline (EasyOCR) — classic OCR → LLM structured extraction
- **Human-in-the-loop review** — extracted fields are editable before saving
- **Supabase storage** — original documents stored in bucket, extracted data in PostgreSQL
- **Dashboard** — total payments, GST breakdown, vendor-wise summary
- **CSV export** — download all confirmed invoices

---

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend | React 18 + Tailwind CSS + Vite |
| Backend | Python FastAPI |
| AI Extraction | Groq API — LLaMA 4 Scout (vision) |
| OCR | EasyOCR |
| Database | Supabase (PostgreSQL) |
| File Storage | Supabase Storage Bucket |

---

## Project Structure
```
Data-Extraction-Tool/
├── README.md
├── requirements.txt
├── TestImagePDF/               # Sample test files
└── invoice-extractor/
  ├── backend/                # Python FastAPI API layer
  │   ├── main.py             # App entry point + CORS
  │   ├── requirements.txt
  │   ├── runtime.txt
  │   ├── Procfile
  │   ├── nixpacks.toml
  │   ├── routers/
  │   │   └── extract.py      # /extract, /extract-text, /confirm, /reject, /invoices
  │   └── utils/
  │       ├── file_handler.py     # PDF/image/DOCX preparation
  │       ├── ai_extractor.py     # Groq vision + text extraction
  │       ├── ocr_extractor.py    # OCR pipeline
  │       └── supabase_service.py # DB and file storage operations
  └── frontend/               # React + Vite UI
    ├── package.json
    ├── index.html
    └── src/
      ├── pages/          # UploadPage, ReviewPage, DashboardPage
      ├── components/
      │   └── layout/     # Layout shell
      └── services/
        └── api.js      # API calls
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- Groq API key (free at [console.groq.com](https://console.groq.com))
- Supabase project (free at [supabase.com](https://supabase.com))

---

### 1. Clone the repo
```bash
git clone https://github.com/your-username/automated-invoice-document-data-extraction-tool.git
cd Data-Extraction-Tool
```

### 2. Backend setup
```bash
cd invoice-extractor/backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

Create `invoice-extractor/backend/.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
DATABASE_URL=postgresql://postgres.your-project:[PASSWORD]@aws-0-region.pooler.supabase.com:6543/postgres
```

Run the backend:
```bash
uvicorn main:app --reload
```

API runs at `http://localhost:8000` — docs at `http://localhost:8000/docs`

---

### 3. Supabase setup

Run this in your Supabase SQL Editor:
```sql
CREATE TABLE invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_name TEXT,
  file_url TEXT,
  file_type TEXT,
  uploaded_at TIMESTAMPTZ DEFAULT now(),
  extraction_mode TEXT,
  vendor_name TEXT,
  gstin TEXT,
  invoice_number TEXT,
  invoice_date TEXT,
  line_items JSONB,
  subtotal NUMERIC,
  total_amount NUMERIC,
  cgst NUMERIC,
  sgst NUMERIC,
  igst NUMERIC,
  pan_number TEXT,
  payment_terms TEXT,
  raw_extracted_json JSONB,
  status TEXT DEFAULT 'pending',
  confirmed_at TIMESTAMPTZ
);
```

Also create a storage bucket named `invoices` and set it to public.

---

### 4. Frontend setup
```bash
cd invoice-extractor/frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## Extraction Fields

| Field | Description |
|---|---|
| Vendor Name | Name of the vendor/supplier |
| GSTIN | GST Identification Number |
| Invoice Number | Unique invoice reference |
| Invoice Date | Date of invoice |
| PAN Number | PAN (if present) |
| Payment Terms | Payment due terms |
| Line Items | Description, quantity, rate, amount |
| Subtotal | Pre-tax amount |
| CGST / SGST / IGST | Tax breakdown |
| Total Amount | Final payable amount |

---

## Future Roadmap

- [ ] Fix Supabase storage bucket policy for file uploads
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Railway or Render
- [ ] Integration with ClearESG BRSR portal (RAG pipeline)
- [ ] Support for more Indian invoice formats
- [ ] Batch upload multiple invoices

---

## Built By

Ishan Peshkar — AI Intern, EmergeFlow Technologies  
March 2026

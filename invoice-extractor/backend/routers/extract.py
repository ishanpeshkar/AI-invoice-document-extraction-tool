import csv
import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from utils.document_classifier import classify_document
from utils.file_handler import prepare_file_for_extraction, get_file_type
from utils.ai_extractor import extract_from_images, extract_from_text, extract_multipage
from utils.supabase_service import (
    upload_file_to_storage,
    save_invoice_record,
    confirm_invoice,
    reject_invoice,
    get_all_invoices,
)

router = APIRouter()


class TextExtractRequest(BaseModel):
    text: str
    extraction_mode: str = "ai"


class ConfirmRequest(BaseModel):
    invoice_id: str
    updated_data: dict


class RejectRequest(BaseModel):
    invoice_id: str


@router.post("/extract")
async def extract_from_file(
    file: UploadFile = File(...),
    extraction_mode: str = Form("ai")
):
    file_type = get_file_type(file.content_type)
    if file_type == "unknown":
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    file_bytes = await file.read()

    try:
        # Step 1 — Classify document
        classification = classify_document(file_bytes, file.content_type)

        # Step 2 — Prepare file for extraction
        prepared = prepare_file_for_extraction(file_bytes, file.content_type)

        # Step 3 — Extract based on doc type and mode
        if extraction_mode == "ocr":
            try:
                from utils.ocr_extractor import extract_via_ocr
                extracted = extract_via_ocr(file_bytes, file.content_type)
            except (ImportError, ValueError) as e:
                raise HTTPException(
                    status_code=400,
                    detail="OCR mode is not available in production. Please use AI Direct mode."
                )
        else:
            # AI extraction — handle multipage vs single
            if prepared["type"] == "image_chunks":
                if len(prepared["data"]) > 1:
                    # Multipage — process all chunks and merge
                    extracted = extract_multipage(prepared["data"])
                else:
                    # Single chunk
                    extracted = extract_from_images(prepared["data"][0])
            elif prepared["type"] == "images":
                extracted = extract_from_images(prepared["data"])
            else:
                extracted = extract_from_text(prepared["data"])

        # Step 4 — Upload file to storage
        file_url = upload_file_to_storage(file_bytes, file.filename, file.content_type)

        # Step 5 — Save to DB
        record = save_invoice_record(
            file_name=file.filename,
            file_url=file_url,
            file_type=file_type,
            extraction_mode=extraction_mode,
            extracted=extracted
        )

        return {
            "status": "success",
            "invoice_id": record["id"],
            "extraction_mode": extraction_mode,
            "file_name": file.filename,
            "file_type": file_type,
            "file_url": file_url,
            "page_count": prepared.get("page_count", 1),
            "pages_processed": prepared.get("page_count", 1),
            "doc_classification": classification,
            "data": extracted
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-text")
async def extract_from_raw_text(request: TextExtractRequest):
    try:
        extracted = extract_from_text(request.text)
        record = save_invoice_record(
            file_name="text_input",
            file_url=None,
            file_type="text",
            extraction_mode=request.extraction_mode,
            extracted=extracted
        )
        return {
            "status": "success",
            "invoice_id": record["id"],
            "extraction_mode": request.extraction_mode,
            "file_name": None,
            "file_type": "text",
            "page_count": 1,
            "doc_classification": {
                "doc_type": "text",
                "route_to": "text_llm",
                "confidence": "high",
                "notes": "Plain text input"
            },
            "data": extracted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm")
async def confirm(request: ConfirmRequest):
    try:
        record = confirm_invoice(request.invoice_id, request.updated_data)
        return {"status": "confirmed", "record": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject")
async def reject(request: RejectRequest):
    try:
        record = reject_invoice(request.invoice_id)
        return {"status": "rejected", "record": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices")
async def list_invoices():
    try:
        invoices = get_all_invoices()
        return {"status": "success", "invoices": invoices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/export/csv")
async def export_invoices_csv():
    try:
        invoices = get_all_invoices()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Invoice ID", "Vendor Name", "GSTIN", "Invoice Number",
            "Invoice Date", "PAN Number", "Payment Terms",
            "Subtotal", "CGST", "SGST", "IGST", "Total Amount",
            "Extraction Mode", "File Name", "File Type",
            "Uploaded At", "Confirmed At"
        ])
        for inv in invoices:
            writer.writerow([
                inv.get("id"), inv.get("vendor_name"), inv.get("gstin"),
                inv.get("invoice_number"), inv.get("invoice_date"),
                inv.get("pan_number"), inv.get("payment_terms"),
                inv.get("subtotal"), inv.get("cgst"), inv.get("sgst"),
                inv.get("igst"), inv.get("total_amount"),
                inv.get("extraction_mode"), inv.get("file_name"),
                inv.get("file_type"), inv.get("uploaded_at"), inv.get("confirmed_at"),
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=invoices_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
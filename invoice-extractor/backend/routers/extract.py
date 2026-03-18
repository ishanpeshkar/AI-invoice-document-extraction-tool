from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from utils.file_handler import prepare_file_for_extraction, get_file_type
from utils.ai_extractor import extract_from_images, extract_from_text
from utils.ocr_extractor import extract_via_ocr
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
        # Step 1 — Extract
        if extraction_mode == "ocr":
            if file_type == "docx":
                raise HTTPException(status_code=400, detail="OCR mode not supported for DOCX. Use AI mode.")
            extracted = extract_via_ocr(file_bytes, file.content_type)
        else:
            prepared = prepare_file_for_extraction(file_bytes, file.content_type)
            if prepared["type"] == "images":
                extracted = extract_from_images(prepared["data"])
            else:
                extracted = extract_from_text(prepared["data"])

        # Step 2/3 — Persist to Supabase when available.
        # If Supabase is not installed/configured, still return extraction result.
        file_url = None
        record = None
        warning = None
        try:
            file_url = upload_file_to_storage(file_bytes, file.filename, file.content_type)
            record = save_invoice_record(
                file_name=file.filename,
                file_url=file_url,
                file_type=file_type,
                extraction_mode=extraction_mode,
                extracted=extracted
            )
        except RuntimeError as e:
            warning = str(e)

        response = {
            "status": "success",
            "invoice_id": record["id"] if record else None,
            "extraction_mode": extraction_mode,
            "file_name": file.filename,
            "file_type": file_type,
            "file_url": file_url,
            "data": extracted
        }
        if warning:
            response["warning"] = warning
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-text")
async def extract_from_raw_text(request: TextExtractRequest):
    try:
        extracted = extract_from_text(request.text)

        record = None
        warning = None
        try:
            record = save_invoice_record(
                file_name="text_input",
                file_url=None,
                file_type="text",
                extraction_mode=request.extraction_mode,
                extracted=extracted
            )
        except RuntimeError as e:
            warning = str(e)

        response = {
            "status": "success",
            "invoice_id": record["id"] if record else None,
            "extraction_mode": request.extraction_mode,
            "file_name": None,
            "file_type": "text",
            "data": extracted
        }
        if warning:
            response["warning"] = warning
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm")
async def confirm(request: ConfirmRequest):
    try:
        if not request.invoice_id:
            raise HTTPException(
                status_code=400,
                detail="invoice_id is required to confirm. Supabase persistence may be unavailable."
            )
        record = confirm_invoice(request.invoice_id, request.updated_data)
        return {"status": "confirmed", "record": record}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject")
async def reject(request: RejectRequest):
    try:
        if not request.invoice_id:
            raise HTTPException(
                status_code=400,
                detail="invoice_id is required to reject. Supabase persistence may be unavailable."
            )
        record = reject_invoice(request.invoice_id)
        return {"status": "rejected", "record": record}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices")
async def list_invoices():
    try:
        invoices = get_all_invoices()
        return {"status": "success", "invoices": invoices}
    except RuntimeError as e:
        return {"status": "success", "invoices": [], "warning": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




import csv
import io
from fastapi.responses import StreamingResponse

@router.get("/invoices/export/csv")
async def export_invoices_csv():
    try:
        invoices = get_all_invoices()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "Invoice ID", "Vendor Name", "GSTIN", "Invoice Number",
            "Invoice Date", "PAN Number", "Payment Terms",
            "Subtotal", "CGST", "SGST", "IGST", "Total Amount",
            "Extraction Mode", "File Name", "File Type",
            "Uploaded At", "Confirmed At"
        ])

        # Data rows
        for inv in invoices:
            writer.writerow([
                inv.get("id"),
                inv.get("vendor_name"),
                inv.get("gstin"),
                inv.get("invoice_number"),
                inv.get("invoice_date"),
                inv.get("pan_number"),
                inv.get("payment_terms"),
                inv.get("subtotal"),
                inv.get("cgst"),
                inv.get("sgst"),
                inv.get("igst"),
                inv.get("total_amount"),
                inv.get("extraction_mode"),
                inv.get("file_name"),
                inv.get("file_type"),
                inv.get("uploaded_at"),
                inv.get("confirmed_at"),
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=invoices_export.csv"}
        )

    except RuntimeError:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Invoice ID", "Vendor Name", "GSTIN", "Invoice Number",
            "Invoice Date", "PAN Number", "Payment Terms",
            "Subtotal", "CGST", "SGST", "IGST", "Total Amount",
            "Extraction Mode", "File Name", "File Type",
            "Uploaded At", "Confirmed At"
        ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=invoices_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
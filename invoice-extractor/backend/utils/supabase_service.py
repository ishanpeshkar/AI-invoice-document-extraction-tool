import os
import uuid
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "invoices"


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def upload_file_to_storage(file_bytes: bytes, file_name: str, content_type: str) -> str | None:
    """Upload file to Supabase storage. Returns URL or None if upload fails."""
    try:
        unique_name = f"{uuid.uuid4()}_{file_name}"
        url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{unique_name}"

        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": content_type,
        }

        response = requests.post(url, headers=headers, data=file_bytes)
        response.raise_for_status()

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{unique_name}"
        return public_url
    except Exception as e:
        print(f"[WARNING] File storage upload failed: {e} — continuing without file URL")
        return None


def save_invoice_record(
    file_name: str,
    file_url: str,
    file_type: str,
    extraction_mode: str,
    extracted: dict
) -> dict:
    """Insert extracted invoice data into PostgreSQL. Returns saved record."""

    def safe_numeric(value):
        if value is None:
            return None
        try:
            return float(str(value).replace(",", "").strip())
        except (ValueError, AttributeError):
            return None

    record_id = str(uuid.uuid4())

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO invoices (
                    id, file_name, file_url, file_type, extraction_mode,
                    vendor_name, gstin, invoice_number, invoice_date,
                    pan_number, payment_terms, line_items,
                    subtotal, total_amount, cgst, sgst, igst,
                    raw_extracted_json, status
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s
                ) RETURNING *
            """, (
                record_id,
                file_name, file_url, file_type, extraction_mode,
                extracted.get("vendor_name"),
                extracted.get("gstin"),
                extracted.get("invoice_number"),
                extracted.get("invoice_date"),
                extracted.get("pan_number"),
                extracted.get("payment_terms"),
                psycopg2.extras.Json(extracted.get("line_items", [])),
                safe_numeric(extracted.get("subtotal")),
                safe_numeric(extracted.get("total_amount")),
                safe_numeric(extracted.get("cgst")),
                safe_numeric(extracted.get("sgst")),
                safe_numeric(extracted.get("igst")),
                psycopg2.extras.Json(extracted),
                "pending"
            ))
            record = dict(cur.fetchone())
            conn.commit()
            return record
    finally:
        conn.close()


def confirm_invoice(invoice_id: str, updated_data: dict) -> dict:
    """Mark invoice as confirmed and update fields after human review."""

    def safe_numeric(value):
        if value is None:
            return None
        try:
            return float(str(value).replace(",", "").strip())
        except (ValueError, AttributeError):
            return None

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                UPDATE invoices SET
                    status = 'confirmed',
                    confirmed_at = %s,
                    vendor_name = %s,
                    gstin = %s,
                    invoice_number = %s,
                    invoice_date = %s,
                    pan_number = %s,
                    payment_terms = %s,
                    line_items = %s,
                    subtotal = %s,
                    total_amount = %s,
                    cgst = %s,
                    sgst = %s,
                    igst = %s
                WHERE id = %s
                RETURNING *
            """, (
                datetime.now(timezone.utc),
                updated_data.get("vendor_name"),
                updated_data.get("gstin"),
                updated_data.get("invoice_number"),
                updated_data.get("invoice_date"),
                updated_data.get("pan_number"),
                updated_data.get("payment_terms"),
                psycopg2.extras.Json(updated_data.get("line_items", [])),
                safe_numeric(updated_data.get("subtotal")),
                safe_numeric(updated_data.get("total_amount")),
                safe_numeric(updated_data.get("cgst")),
                safe_numeric(updated_data.get("sgst")),
                safe_numeric(updated_data.get("igst")),
                invoice_id
            ))
            record = dict(cur.fetchone())
            conn.commit()
            return record
    finally:
        conn.close()


def reject_invoice(invoice_id: str) -> dict:
    """Mark invoice as rejected."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "UPDATE invoices SET status = 'rejected' WHERE id = %s RETURNING *",
                (invoice_id,)
            )
            record = dict(cur.fetchone())
            conn.commit()
            return record
    finally:
        conn.close()


def get_all_invoices() -> list:
    """Fetch all confirmed invoices for dashboard."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM invoices
                WHERE status = 'confirmed'
                ORDER BY confirmed_at DESC
            """)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
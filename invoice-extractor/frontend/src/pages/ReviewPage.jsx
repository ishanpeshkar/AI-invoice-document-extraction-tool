import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  CheckCircle,
  XCircle,
  Pencil,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { confirmInvoice, rejectInvoice } from "../services/api";

function Field({ label, value, onChange }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
        {label}
      </label>
      <input
        type="text"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  );
}

function LineItemsTable({ items, onChange }) {
  function updateItem(index, key, value) {
    const updated = items.map((item, i) =>
      i === index ? { ...item, [key]: value } : item,
    );
    onChange(updated);
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
        <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
          <tr>
            <th className="px-3 py-2 text-left">Description</th>
            <th className="px-3 py-2 text-right">Qty</th>
            <th className="px-3 py-2 text-right">Rate</th>
            <th className="px-3 py-2 text-right">Amount</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, i) => (
            <tr key={i} className="border-t border-gray-100">
              <td className="px-3 py-2">
                <input
                  value={item.description ?? ""}
                  onChange={(e) => updateItem(i, "description", e.target.value)}
                  className="w-full text-sm focus:outline-none"
                />
              </td>
              <td className="px-3 py-2">
                <input
                  value={item.quantity ?? ""}
                  onChange={(e) => updateItem(i, "quantity", e.target.value)}
                  className="w-16 text-sm text-right focus:outline-none"
                />
              </td>
              <td className="px-3 py-2">
                <input
                  value={item.rate ?? ""}
                  onChange={(e) => updateItem(i, "rate", e.target.value)}
                  className="w-24 text-sm text-right focus:outline-none"
                />
              </td>
              <td className="px-3 py-2">
                <input
                  value={item.amount ?? ""}
                  onChange={(e) => updateItem(i, "amount", e.target.value)}
                  className="w-24 text-sm text-right focus:outline-none"
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ReviewPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const raw =
    location.state?.extracted?.data ?? location.state?.extracted ?? {};
  const invoiceId = location.state?.extracted?.invoice_id ?? null;

  const [data, setData] = useState({
    vendor_name: raw.vendor_name ?? "",
    gstin: raw.gstin ?? "",
    invoice_number: raw.invoice_number ?? "",
    invoice_date: raw.invoice_date ?? "",
    pan_number: raw.pan_number ?? "",
    payment_terms: raw.payment_terms ?? "",
    subtotal: raw.subtotal ?? "",
    cgst: raw.cgst ?? "",
    sgst: raw.sgst ?? "",
    igst: raw.igst ?? "",
    total_amount: raw.total_amount ?? "",
    line_items: raw.line_items ?? [],
  });

  const [showRaw, setShowRaw] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  function update(key, value) {
    setData((prev) => ({ ...prev, [key]: value }));
  }

  async function handleConfirm() {
    setSaving(true);
    try {
      await confirmInvoice(invoiceId, data);
      setSaved(true);
      setTimeout(() => navigate("/dashboard"), 1200);
    } catch (err) {
      console.error("Confirm failed:", err);
    } finally {
      setSaving(false);
    }
  }

  function handleReject() {
    if (invoiceId) {
      rejectInvoice(invoiceId).catch(console.error);
    }
    navigate("/upload");
  }

  if (saved) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full">
        <CheckCircle size={48} className="text-green-500 mb-4" />
        <h2 className="text-xl font-bold text-gray-800">Saved Successfully</h2>
        <p className="text-sm text-gray-500 mt-1">
          Redirecting to dashboard...
        </p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Review Extracted Data
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Check and edit the fields below before saving.
          </p>
          {/* Document Classification Badge */}
          {location.state?.extracted?.doc_classification && (
            <div className="mb-6 flex items-center gap-3 flex-wrap">
              <span className="px-3 py-1 bg-blue-50 border border-blue-200 rounded-full text-xs font-medium text-blue-700">
                📄{" "}
                {location.state.extracted.doc_classification.doc_type
                  .replace("_", " ")
                  .toUpperCase()}
              </span>
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium border ${
                  location.state.extracted.doc_classification.confidence ===
                  "high"
                    ? "bg-green-50 border-green-200 text-green-700"
                    : location.state.extracted.doc_classification.confidence ===
                        "medium"
                      ? "bg-yellow-50 border-yellow-200 text-yellow-700"
                      : "bg-red-50 border-red-200 text-red-700"
                }`}
              >
                {location.state.extracted.doc_classification.confidence ===
                "high"
                  ? "✅"
                  : location.state.extracted.doc_classification.confidence ===
                      "medium"
                    ? "⚠️"
                    : "🔴"}{" "}
                Confidence:{" "}
                {location.state.extracted.doc_classification.confidence}
              </span>
              {location.state.extracted.page_count > 1 && (
                <span className="px-3 py-1 bg-purple-50 border border-purple-200 rounded-full text-xs font-medium text-purple-700">
                  📑 {location.state.extracted.page_count} pages processed
                </span>
              )}
              <p className="text-xs text-gray-400 w-full">
                {location.state.extracted.doc_classification.notes}
              </p>
            </div>
          )}
          {location.state?.extracted?.pages_skipped > 0 && (
            <div className="mt-3 mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-700">
              Warning: This document has {location.state.extracted.page_count}{" "}
              pages - only {location.state.extracted.pages_processed} were
              processed. For full extraction, split the document into smaller
              files.
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReject}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <XCircle size={16} />
            Reject
          </button>
          <button
            onClick={handleConfirm}
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors disabled:opacity-60"
          >
            <CheckCircle size={16} />
            {saving ? "Saving..." : "Confirm & Save"}
          </button>
        </div>
      </div>

      {/* Vendor Details */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-4">
        <h2 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
          <Pencil size={14} /> Vendor Details
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <Field
            label="Vendor Name"
            value={data.vendor_name}
            onChange={(v) => update("vendor_name", v)}
          />
          <Field
            label="GSTIN"
            value={data.gstin}
            onChange={(v) => update("gstin", v)}
          />
          <Field
            label="Invoice Number"
            value={data.invoice_number}
            onChange={(v) => update("invoice_number", v)}
          />
          <Field
            label="Invoice Date"
            value={data.invoice_date}
            onChange={(v) => update("invoice_date", v)}
          />
          <Field
            label="PAN Number"
            value={data.pan_number}
            onChange={(v) => update("pan_number", v)}
          />
          <Field
            label="Payment Terms"
            value={data.payment_terms}
            onChange={(v) => update("payment_terms", v)}
          />
        </div>
      </div>

      {/* Line Items */}
      {data.line_items.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-4">
          <h2 className="text-sm font-bold text-gray-700 mb-4">Line Items</h2>
          <LineItemsTable
            items={data.line_items}
            onChange={(items) => update("line_items", items)}
          />
        </div>
      )}

      {/* Tax & Totals */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-4">
        <h2 className="text-sm font-bold text-gray-700 mb-4">Tax & Totals</h2>
        <div className="grid grid-cols-3 gap-4">
          <Field
            label="Subtotal"
            value={data.subtotal}
            onChange={(v) => update("subtotal", v)}
          />
          <Field
            label="CGST"
            value={data.cgst}
            onChange={(v) => update("cgst", v)}
          />
          <Field
            label="SGST"
            value={data.sgst}
            onChange={(v) => update("sgst", v)}
          />
          <Field
            label="IGST"
            value={data.igst}
            onChange={(v) => update("igst", v)}
          />
          <Field
            label="Total Amount"
            value={data.total_amount}
            onChange={(v) => update("total_amount", v)}
          />
        </div>
      </div>

      {/* Raw JSON Toggle */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl overflow-hidden">
        <button
          onClick={() => setShowRaw(!showRaw)}
          className="w-full flex items-center justify-between px-6 py-3 text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
        >
          View Raw Extracted JSON
          {showRaw ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
        {showRaw && (
          <pre className="px-6 py-4 text-xs text-gray-600 overflow-x-auto border-t border-gray-200">
            {JSON.stringify(raw, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

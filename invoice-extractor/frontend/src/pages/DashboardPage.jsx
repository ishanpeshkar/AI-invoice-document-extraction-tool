import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchInvoices } from "../services/api";
import { downloadInvoicesCSV } from "../services/api";
import { UploadCloud, FileText, TrendingUp, Receipt } from "lucide-react";

function KPICard({ label, value, icon: Icon, color }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <p className="text-xs text-gray-500 font-medium">{label}</p>
        <p className="text-xl font-bold text-gray-900 mt-0.5">{value}</p>
      </div>
    </div>
  );
}

function formatCurrency(value) {
  const num = parseFloat(value) || 0;
  return `₹${num.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchInvoices()
      .then((res) => setInvoices(res.invoices || []))
      .catch(() => setError("Failed to load invoices."))
      .finally(() => setLoading(false));
  }, []);

  // KPI calculations
  const totalPayments = invoices.reduce(
    (sum, inv) => sum + (parseFloat(inv.total_amount) || 0),
    0,
  );
  const totalGST = invoices.reduce((sum, inv) => {
    return (
      sum +
      (parseFloat(inv.cgst) || 0) +
      (parseFloat(inv.sgst) || 0) +
      (parseFloat(inv.igst) || 0)
    );
  }, 0);
  const uniqueVendors = new Set(
    invoices.map((inv) => inv.vendor_name).filter(Boolean),
  ).size;

  // Monthly totals
  const monthlyMap = {};
  invoices.forEach((inv) => {
    if (!inv.confirmed_at) return;
    const month = new Date(inv.confirmed_at).toLocaleString("en-IN", {
      month: "short",
      year: "2-digit",
    });
    monthlyMap[month] =
      (monthlyMap[month] || 0) + (parseFloat(inv.total_amount) || 0);
  });
  const monthlyData = Object.entries(monthlyMap).slice(-6);

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            All confirmed invoices and vendor summaries.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => downloadInvoicesCSV().catch(console.error)}
            disabled={invoices.length === 0}
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 text-gray-600 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ⬇ Export CSV
          </button>
          <button
            onClick={() => navigate("/upload")}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <UploadCloud size={16} />
            Upload New
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <KPICard
          label="Total Vendor Payments"
          value={formatCurrency(totalPayments)}
          icon={TrendingUp}
          color="bg-blue-500"
        />
        <KPICard
          label="Total GST Paid"
          value={formatCurrency(totalGST)}
          icon={Receipt}
          color="bg-purple-500"
        />
        <KPICard
          label="Unique Vendors"
          value={uniqueVendors}
          icon={FileText}
          color="bg-green-500"
        />
      </div>

      {/* Loading / Error */}
      {loading && (
        <p className="text-sm text-gray-400 text-center py-12">
          Loading invoices...
        </p>
      )}
      {error && (
        <p className="text-sm text-red-500 text-center py-12">{error}</p>
      )}

      {/* Invoice Table */}
      {!loading && !error && invoices.length === 0 && (
        <div className="text-center py-16 border-2 border-dashed border-gray-200 rounded-xl">
          <UploadCloud size={36} className="mx-auto text-gray-300 mb-3" />
          <p className="text-sm font-medium text-gray-500">
            No confirmed invoices yet
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Upload an invoice and confirm it to see it here.
          </p>
          <button
            onClick={() => navigate("/upload")}
            className="mt-4 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            Upload Invoice
          </button>
        </div>
      )}

      {!loading && invoices.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-sm font-bold text-gray-700">Invoice Records</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Vendor</th>
                  <th className="px-4 py-3 text-left">GSTIN</th>
                  <th className="px-4 py-3 text-left">Invoice No.</th>
                  <th className="px-4 py-3 text-left">Date</th>
                  <th className="px-4 py-3 text-right">CGST</th>
                  <th className="px-4 py-3 text-right">SGST</th>
                  <th className="px-4 py-3 text-right">IGST</th>
                  <th className="px-4 py-3 text-right">Total</th>
                  <th className="px-4 py-3 text-left">Mode</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {invoices.map((inv) => (
                  <tr
                    key={inv.id}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-4 py-3 font-medium text-gray-800">
                      {inv.vendor_name || "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-mono text-xs">
                      {inv.gstin || "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {inv.invoice_number || "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {inv.invoice_date || "—"}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {formatCurrency(inv.cgst)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {formatCurrency(inv.sgst)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {formatCurrency(inv.igst)}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-800">
                      {formatCurrency(inv.total_amount)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          inv.extraction_mode === "ocr"
                            ? "bg-orange-100 text-orange-600"
                            : "bg-blue-100 text-blue-600"
                        }`}
                      >
                        {inv.extraction_mode === "ocr" ? "OCR" : "AI"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

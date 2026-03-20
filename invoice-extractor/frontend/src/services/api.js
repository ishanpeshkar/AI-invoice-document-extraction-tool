import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function extractInvoice(file, extractionMode) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('extraction_mode', extractionMode)

  const response = await axios.post(`${BASE_URL}/extract`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function extractFromText(text, extractionMode) {
  const response = await axios.post(`${BASE_URL}/extract-text`, {
    text,
    extraction_mode: extractionMode,
  })
  return response.data
}

export async function confirmInvoice(invoiceId, updatedData) {
  const response = await axios.post(`${BASE_URL}/confirm`, {
    invoice_id: invoiceId,
    updated_data: updatedData,
  })
  return response.data
}

export async function rejectInvoice(invoiceId) {
  const response = await axios.post(`${BASE_URL}/reject`, {
    invoice_id: invoiceId,
  })
  return response.data
}

export async function fetchInvoices() {
  const response = await axios.get(`${BASE_URL}/invoices`)
  return response.data
}

export async function downloadInvoicesCSV() {
  const response = await axios.get(`${BASE_URL}/invoices/export/csv`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'invoices_export.csv')
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
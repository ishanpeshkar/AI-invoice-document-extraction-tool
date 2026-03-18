import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, FileText, Image, File, X, Loader2 } from 'lucide-react'
import { extractInvoice, extractFromText } from '../services/api'

const ACCEPTED_TYPES = {
  'application/pdf': 'PDF',
  'image/jpeg': 'Image',
  'image/jpg': 'Image',
  'image/png': 'Image',
  'application/msword': 'DOC',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
}

function getFileIcon(type) {
  if (type.startsWith('image/')) return <Image size={20} className="text-blue-500" />
  if (type === 'application/pdf') return <FileText size={20} className="text-red-500" />
  return <File size={20} className="text-gray-500" />
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function UploadPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('file')
  const [dragOver, setDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [textInput, setTextInput] = useState('')
  const [extractionMode, setExtractionMode] = useState('ai')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file && ACCEPTED_TYPES[file.type]) setSelectedFile(file)
  }

  function handleFileChange(e) {
    const file = e.target.files[0]
    if (file && ACCEPTED_TYPES[file.type]) setSelectedFile(file)
  }

  function clearFile() {
    setSelectedFile(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function handleSubmit() {
    setError(null)
    setLoading(true)
    try {
      let result
      if (activeTab === 'file') {
        result = await extractInvoice(selectedFile, extractionMode)
      } else {
        result = await extractFromText(textInput, extractionMode)
      }
      // Navigate to review page with extracted data
      navigate('/review/new', { state: { extracted: result } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Extraction failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const canSubmit = !loading && (activeTab === 'file' ? !!selectedFile : textInput.trim().length > 0)

  return (
    <div className="p-8 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Upload Document</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload an invoice or paste text to extract structured data automatically.
        </p>
      </div>

      {/* Extraction Mode Toggle */}
      <div className="mb-6">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Extraction Mode
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => setExtractionMode('ai')}
            className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
              extractionMode === 'ai'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
            }`}
          >
            🤖 AI Direct (Groq)
          </button>
          <button
            onClick={() => setExtractionMode('ocr')}
            className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
              extractionMode === 'ocr'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
            }`}
          >
            🔍 OCR Pipeline
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => { setActiveTab('file'); setError(null) }}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'file'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          File Upload
        </button>
        <button
          onClick={() => { setActiveTab('text'); setError(null) }}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'text'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Paste Text
        </button>
      </div>

      {/* File Upload Tab */}
      {activeTab === 'file' && (
        <div>
          {!selectedFile ? (
            <div
              onDrop={handleDrop}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
                dragOver
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
              }`}
            >
              <UploadCloud size={36} className="mx-auto text-gray-400 mb-3" />
              <p className="text-sm font-medium text-gray-700">Drag & drop your file here</p>
              <p className="text-xs text-gray-400 mt-1">or click to browse</p>
              <p className="text-xs text-gray-400 mt-3">Supported: PDF, JPG, PNG, DOC, DOCX</p>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                onChange={handleFileChange}
              />
            </div>
          ) : (
            <div className="border border-gray-200 rounded-xl p-4 flex items-center gap-4 bg-white">
              {getFileIcon(selectedFile.type)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{selectedFile.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {ACCEPTED_TYPES[selectedFile.type]} · {formatSize(selectedFile.size)}
                </p>
              </div>
              <button onClick={clearFile} className="text-gray-400 hover:text-red-500 transition-colors">
                <X size={18} />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Paste Text Tab */}
      {activeTab === 'text' && (
        <textarea
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Paste your invoice text here..."
          className="w-full h-48 border border-gray-200 rounded-xl p-4 text-sm text-gray-700 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      )}

      {/* Error */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={`mt-6 w-full py-3 rounded-xl text-sm font-semibold transition-colors flex items-center justify-center gap-2 ${
          canSubmit
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
        }`}
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Extracting...
          </>
        ) : (
          'Extract Data →'
        )}
      </button>
    </div>
  )
}
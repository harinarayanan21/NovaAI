import { useState, useEffect, useCallback, useRef } from "react";
import { ragApi } from "../services/api";

const FILE_TYPE_ICONS = {
  pdf: "M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z",
  docx: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  txt: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  md: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
};

const FILE_TYPE_COLORS = {
  pdf: "bg-red-500/20 text-red-400",
  docx: "bg-blue-500/20 text-blue-400",
  txt: "bg-green-500/20 text-green-400",
  md: "bg-purple-500/20 text-purple-400",
};

function KnowledgeBasePage() {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(null);
  const fileInputRef = useRef(null);

  const [question, setQuestion] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);

  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [docsRes, statsRes] = await Promise.all([
        ragApi.documents(),
        ragApi.stats(),
      ]);
      setDocuments(docsRes.data);
      setStats(statsRes.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFile = async (file) => {
    if (!file) return;
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx", "txt", "md"].includes(ext)) {
      setError("Unsupported file type. Use PDF, DOCX, TXT, or MD.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setError("File too large. Max size: 20MB.");
      return;
    }

    setUploading(true);
    setUploadProgress(`Uploading ${file.name}...`);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      await ragApi.upload(formData);
      setUploadProgress(`Processing ${file.name}...`);
      await loadData();
      setUploadProgress(null);
    } catch (err) {
      setError(err.message);
      setUploadProgress(null);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDelete = async (docId) => {
    try {
      await ragApi.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      setDeleteConfirm(null);
      const { data } = await ragApi.stats();
      setStats(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleQuery = async () => {
    if (!question.trim() || isQuerying) return;
    setIsQuerying(true);
    setError(null);
    try {
      const { data } = await ragApi.query(question.trim());
      const entry = { question: question.trim(), ...data, timestamp: Date.now() };
      setQueryResult(entry);
      setQueryHistory((prev) => [entry, ...prev.slice(0, 9)]);
      setQuestion("");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsQuerying(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div className="min-h-screen bg-chat-bg">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Knowledge Base</h1>
          <p className="text-neutral-400 text-sm">
            Upload documents and ask questions about them using RAG.
          </p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4">
              <p className="text-2xl font-bold text-white">{stats.total_documents}</p>
              <p className="text-xs text-neutral-400 mt-1">Documents</p>
            </div>
            <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4">
              <p className="text-2xl font-bold text-white">{stats.total_chunks}</p>
              <p className="text-xs text-neutral-400 mt-1">Chunks Indexed</p>
            </div>
            <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4">
              <p className="text-2xl font-bold text-white">{Object.keys(stats.by_type).length}</p>
              <p className="text-xs text-neutral-400 mt-1">File Types</p>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Upload Area */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !uploading && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all mb-8 ${
            isDragging
              ? "border-accent bg-accent/5"
              : "border-neutral-600 hover:border-neutral-500 hover:bg-neutral-800/50"
          } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            onChange={(e) => handleFile(e.target.files[0])}
            className="hidden"
          />
          {uploadProgress ? (
            <div>
              <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm text-accent">{uploadProgress}</p>
            </div>
          ) : (
            <div>
              <svg className="w-12 h-12 text-neutral-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-sm text-neutral-300 mb-1">
                <span className="text-accent font-medium">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-neutral-500">PDF, DOCX, TXT, or MD — Max 20MB</p>
            </div>
          )}
        </div>

        {/* Ask Question */}
        <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4 mb-8">
          <h3 className="text-sm font-medium text-white mb-3">Ask a Question</h3>
          <div className="flex gap-3">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleQuery()}
              placeholder="Ask anything about your uploaded documents..."
              disabled={isQuerying}
              className="flex-1 px-4 py-2.5 bg-neutral-900 border border-neutral-600 rounded-xl text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
            />
            <button
              onClick={handleQuery}
              disabled={isQuerying || !question.trim()}
              className="px-4 py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-50 rounded-xl text-sm text-white font-medium transition-colors"
            >
              {isQuerying ? "Thinking..." : "Ask"}
            </button>
          </div>

          {queryResult && (
            <div className="mt-4 p-4 bg-neutral-900 border border-neutral-600 rounded-xl">
              <p className="text-xs text-neutral-500 mb-2">Q: {queryResult.question}</p>
              <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">{queryResult.answer}</p>
              {queryResult.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-neutral-700/50">
                  <p className="text-xs text-neutral-500 mb-2">Sources:</p>
                  <div className="flex flex-wrap gap-2">
                    {queryResult.sources.map((s, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 px-2 py-1 bg-neutral-800 border border-neutral-600 rounded-md text-xs text-neutral-300"
                      >
                        <span className="text-neutral-500">{s.filename}</span>
                        <span className="text-accent">{Math.round(s.similarity * 100)}%</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Query History */}
        {queryHistory.length > 1 && (
          <div className="mb-8">
            <h3 className="text-sm font-medium text-neutral-400 mb-3">Recent Questions</h3>
            <div className="space-y-2">
              {queryHistory.slice(1, 6).map((entry) => (
                <button
                  key={entry.timestamp}
                  onClick={() => setQueryResult(entry)}
                  className="w-full text-left p-3 bg-neutral-800/50 border border-neutral-700/30 rounded-xl hover:bg-neutral-800 transition-colors"
                >
                  <p className="text-xs text-neutral-500 mb-1">{entry.question}</p>
                  <p className="text-xs text-neutral-400 truncate">{entry.answer.substring(0, 120)}...</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Document List */}
        {!isLoading && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-neutral-400">Uploaded Documents</h3>
            {documents.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-12 h-12 text-neutral-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-neutral-400 text-sm">No documents uploaded yet.</p>
                <p className="text-neutral-500 text-xs mt-1">Upload a PDF, DOCX, TXT, or MD file to get started.</p>
              </div>
            ) : (
              documents.map((doc) => {
                const colorClass = FILE_TYPE_COLORS[doc.file_type] || FILE_TYPE_COLORS.txt;
                const iconPath = FILE_TYPE_ICONS[doc.file_type] || FILE_TYPE_ICONS.txt;

                return (
                  <div
                    key={doc.id}
                    className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4 hover:border-neutral-600 transition-colors group"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${colorClass}`}>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={iconPath} />
                          </svg>
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-white font-medium truncate">{doc.filename}</p>
                          <div className="flex items-center gap-3 mt-1">
                            <span className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium ${colorClass}`}>
                              {doc.file_type.toUpperCase()}
                            </span>
                            <span className="text-xs text-neutral-500">{formatFileSize(doc.file_size)}</span>
                            {doc.status === "ready" ? (
                              <span className="text-xs text-green-400">{doc.chunk_count} chunks</span>
                            ) : doc.status === "failed" ? (
                              <span className="text-xs text-red-400">Failed</span>
                            ) : (
                              <span className="text-xs text-yellow-400">Processing...</span>
                            )}
                            {doc.created_at && (
                              <span className="text-xs text-neutral-500">
                                {new Date(doc.created_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                          {doc.error_message && (
                            <p className="text-xs text-red-400 mt-1">{doc.error_message}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {deleteConfirm === doc.id ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleDelete(doc.id)}
                              className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white"
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(null)}
                              className="px-2 py-1 bg-neutral-600 hover:bg-neutral-500 rounded text-xs text-white"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirm(doc.id)}
                            className="p-1.5 rounded-lg hover:bg-red-900/50 text-neutral-400 hover:text-red-400 transition-colors"
                            title="Delete document"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default KnowledgeBasePage;

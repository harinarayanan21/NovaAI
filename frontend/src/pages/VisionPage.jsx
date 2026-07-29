import { useState, useRef, useCallback, useEffect } from "react";
import { visionApi } from "../services/api";

const TABS = [
  { id: "upload", label: "Upload & Analyze" },
  { id: "ocr", label: "OCR" },
  { id: "qa", label: "Ask Questions" },
  { id: "chart", label: "Chart Analysis" },
  { id: "ui", label: "UI Analysis" },
  { id: "history", label: "History" },
];

function VisionPage() {
  const [activeTab, setActiveTab] = useState("upload");
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [question, setQuestion] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const fileInputRef = useRef(null);

  const loadHistory = useCallback(async () => {
    try {
      const { data } = await visionApi.history();
      setHistory(data.images || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const handleFileSelect = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setResult(null);
    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    handleFileSelect(file);
  };

  const handleDragOver = (e) => e.preventDefault();

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const { data } = await visionApi.upload(formData);
      setResult(data);
      loadHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOcr = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const { data } = await visionApi.ocr(formData);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleQuestion = async () => {
    if (!selectedFile || !question.trim()) return;
    setIsProcessing(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("question", question);
      const { data } = await visionApi.question(formData);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleChartAnalysis = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const { data } = await visionApi.chart(formData);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUiAnalysis = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const { data } = await visionApi.uiAnalysis(formData);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append("query", searchQuery);
      const { data } = await visionApi.search(formData);
      setSearchResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await visionApi.deleteImage(id);
      loadHistory();
    } catch (err) {
      setError(err.message);
    }
  };

  const downloadOcr = () => {
    if (!result?.text) return;
    const blob = new Blob([result.text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ocr-result.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-[#212121] text-white p-4 lg:ml-64">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-1">Vision & Multimodal AI</h1>
        <p className="text-sm text-neutral-400 mb-6">
          Upload images for OCR, captioning, chart analysis, UI review, and Q&A
        </p>

        {/* Tabs */}
        <div className="flex flex-wrap gap-1 mb-6 border-b border-neutral-700/50 pb-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setResult(null); setError(null); }}
              className={`px-4 py-2 rounded-t-lg text-sm transition-colors ${
                activeTab === tab.id
                  ? "bg-accent/10 text-accent border-b-2 border-accent"
                  : "text-neutral-400 hover:text-neutral-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Upload Area */}
        {activeTab !== "history" && (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-neutral-600 hover:border-accent/50 rounded-xl p-8 text-center cursor-pointer transition-colors mb-6"
          >
            {preview ? (
              <div className="max-w-md mx-auto">
                <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-lg mb-3" />
                <p className="text-sm text-neutral-400">{selectedFile?.name}</p>
                <button
                  onClick={(e) => { e.stopPropagation(); setSelectedFile(null); setPreview(null); setResult(null); }}
                  className="text-xs text-red-400 hover:text-red-300 mt-1"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div>
                <svg className="w-12 h-12 mx-auto text-neutral-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="text-neutral-400">Drop an image here or click to browse</p>
                <p className="text-xs text-neutral-500 mt-1">PNG, JPG, WebP up to 20MB</p>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="hidden"
              onChange={(e) => handleFileSelect(e.target.files?.[0])}
            />
          </div>
        )}

        {/* Tab Content */}
        <div className="space-y-4">
          {activeTab === "upload" && (
            <div>
              <button
                onClick={handleUpload}
                disabled={!selectedFile || isProcessing}
                className="px-6 py-2.5 bg-accent hover:bg-accent/90 disabled:opacity-50 text-white rounded-lg text-sm transition-colors"
              >
                {isProcessing ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Processing...
                  </span>
                ) : "Upload & Analyze"}
              </button>
              {result && (
                <div className="mt-4 space-y-4">
                  {result.analysis?.caption?.description && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <h3 className="text-sm font-medium text-accent mb-2">Description</h3>
                      <p className="text-sm text-neutral-300">{result.analysis.caption.description}</p>
                    </div>
                  )}
                  {result.analysis?.ocr?.text && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-accent">OCR Text</h3>
                        <button onClick={downloadOcr} className="text-xs text-accent hover:underline">Download</button>
                      </div>
                      <pre className="text-sm text-neutral-300 whitespace-pre-wrap font-sans max-h-60 overflow-y-auto">
                        {result.analysis.ocr.text}
                      </pre>
                    </div>
                  )}
                  {result.metadata && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <h3 className="text-sm font-medium text-accent mb-2">Metadata</h3>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        {Object.entries(result.metadata).map(([k, v]) => (
                          <div key={k}>
                            <span className="text-neutral-500">{k}: </span>
                            <span className="text-neutral-300">{String(v).slice(0, 60)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === "ocr" && (
            <div>
              <button
                onClick={handleOcr}
                disabled={!selectedFile || isProcessing}
                className="px-6 py-2.5 bg-accent hover:bg-accent/90 disabled:opacity-50 text-white rounded-lg text-sm transition-colors"
              >
                {isProcessing ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Extracting...
                  </span>
                ) : "Extract Text"}
              </button>
              {result && (
                <div className="mt-4 space-y-3">
                  {result.confidence > 0 && (
                    <div className="flex items-center gap-2 text-xs text-neutral-400">
                      <span>Confidence: {result.confidence}%</span>
                      <span>Blocks: {result.total_blocks}</span>
                      <span>Method: {result.method}</span>
                      <button onClick={downloadOcr} className="text-accent hover:underline">Download</button>
                    </div>
                  )}
                  <pre className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50 text-sm text-neutral-300 whitespace-pre-wrap font-sans max-h-96 overflow-y-auto">
                    {result.text || "No text detected"}
                  </pre>
                  {result.tables?.length > 0 && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <h3 className="text-sm font-medium text-accent mb-2">Detected Tables</h3>
                      <p className="text-xs text-neutral-400">{result.tables.length} table(s) found</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === "qa" && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about the image..."
                  className="flex-1 bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
                  onKeyDown={(e) => e.key === "Enter" && handleQuestion()}
                />
                <button
                  onClick={handleQuestion}
                  disabled={!selectedFile || !question.trim() || isProcessing}
                  className="px-6 py-2.5 bg-accent hover:bg-accent/90 disabled:opacity-50 text-white rounded-lg text-sm transition-colors"
                >
                  {isProcessing ? (
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Asking...
                    </span>
                  ) : "Ask"}
                </button>
              </div>
              {result && (
                <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                  <p className="text-xs text-neutral-500 mb-1">Question: {result.question}</p>
                  <p className="text-sm text-neutral-200">{result.answer}</p>
                  {result.confidence && (
                    <p className="text-xs text-neutral-500 mt-2">Confidence: {result.confidence}</p>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === "chart" && (
            <div>
              <button
                onClick={handleChartAnalysis}
                disabled={!selectedFile || isProcessing}
                className="px-6 py-2.5 bg-accent hover:bg-accent/90 disabled:opacity-50 text-white rounded-lg text-sm transition-colors"
              >
                {isProcessing ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Analyzing...
                  </span>
                ) : "Analyze Chart"}
              </button>
              {result && (
                <div className="mt-4 space-y-4">
                  {result.chart_type && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <p className="text-xs text-neutral-500 mb-1">Chart Type</p>
                      <p className="text-sm font-medium text-accent">{result.chart_type}</p>
                    </div>
                  )}
                  {result.summary && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <h3 className="text-sm font-medium text-accent mb-2">Summary</h3>
                      <p className="text-sm text-neutral-300">{result.summary}</p>
                    </div>
                  )}
                  {result.key_insights?.length > 0 && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <h3 className="text-sm font-medium text-accent mb-2">Key Insights</h3>
                      <ul className="list-disc list-inside space-y-1">
                        {result.key_insights.map((insight, i) => (
                          <li key={i} className="text-sm text-neutral-300">{insight}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result.data_points?.length > 0 && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <h3 className="text-sm font-medium text-accent mb-2">Data Points</h3>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {result.data_points.map((dp, i) => (
                          <div key={i} className="bg-neutral-700/30 rounded-lg p-2 text-xs">
                            <span className="text-neutral-400">{dp.label}: </span>
                            <span className="text-neutral-200 font-medium">{dp.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === "ui" && (
            <div>
              <button
                onClick={handleUiAnalysis}
                disabled={!selectedFile || isProcessing}
                className="px-6 py-2.5 bg-accent hover:bg-accent/90 disabled:opacity-50 text-white rounded-lg text-sm transition-colors"
              >
                {isProcessing ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Analyzing...
                  </span>
                ) : "Analyze UI"}
              </button>
              {result && (
                <div className="mt-4 space-y-4">
                  {result.overall_assessment && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <h3 className="text-sm font-medium text-accent mb-2">Assessment</h3>
                      <p className="text-sm text-neutral-300">{result.overall_assessment}</p>
                    </div>
                  )}
                  {result.observations?.length > 0 && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
                      <h3 className="text-sm font-medium text-amber-400 mb-2">Observations</h3>
                      <ul className="list-disc list-inside space-y-1">
                        {result.observations.map((obs, i) => (
                          <li key={i} className="text-sm text-neutral-300">{obs}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result.possible_issues?.length > 0 && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-red-500/20">
                      <h3 className="text-sm font-medium text-red-400 mb-2">Possible Issues</h3>
                      <ul className="list-disc list-inside space-y-1">
                        {result.possible_issues.map((issue, i) => (
                          <li key={i} className="text-sm text-neutral-300">{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result.suggestions?.length > 0 && (
                    <div className="bg-neutral-800/50 rounded-xl p-4 border border-green-500/20">
                      <h3 className="text-sm font-medium text-green-400 mb-2">Suggestions</h3>
                      <ul className="list-disc list-inside space-y-1">
                        {result.suggestions.map((sug, i) => (
                          <li key={i} className="text-sm text-neutral-300">{sug}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === "history" && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search images by content..."
                  className="flex-1 bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
                <button
                  onClick={handleSearch}
                  disabled={!searchQuery.trim() || isProcessing}
                  className="px-4 py-2.5 bg-neutral-700 hover:bg-neutral-600 disabled:opacity-50 text-white rounded-lg text-sm transition-colors"
                >
                  {isProcessing ? "Searching..." : "Search"}
                </button>
                <button onClick={loadHistory} className="px-4 py-2.5 bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg text-sm transition-colors">
                  Refresh
                </button>
              </div>

              {searchResults && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-accent mb-2">Search Results ({searchResults.length})</h3>
                  <div className="space-y-2">
                    {searchResults.map((r, i) => (
                      <div key={i} className="bg-neutral-800/50 rounded-lg p-3 border border-neutral-700/50 text-sm">
                        <span className="text-accent text-xs">{r.type}</span>
                        <p className="text-neutral-300 mt-1">{r.content}</p>
                        <p className="text-xs text-neutral-500 mt-1">Similarity: {r.similarity}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {history.length === 0 ? (
                <div className="bg-neutral-800/50 rounded-xl p-8 text-center border border-neutral-700/50">
                  <p className="text-neutral-400">No images uploaded yet</p>
                </div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {history.map((img) => (
                    <div key={img.id} className="bg-neutral-800/50 rounded-lg p-4 border border-neutral-700/50">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="text-sm font-medium truncate">{img.filename}</p>
                          <p className="text-xs text-neutral-500">
                            {img.width}x{img.height} &middot; {Math.round(img.file_size / 1024)}KB
                          </p>
                        </div>
                        <button
                          onClick={() => handleDelete(img.id)}
                          className="p-1 rounded hover:bg-red-900/50 text-neutral-500 hover:text-red-400"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                      {img.caption && (
                        <p className="text-xs text-neutral-400 line-clamp-2">{img.caption}</p>
                      )}
                      <p className="text-xs text-neutral-600 mt-2">
                        {new Date(img.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {error && (
          <div className="fixed bottom-4 right-4 bg-red-500/20 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm max-w-md">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default VisionPage;

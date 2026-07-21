import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useVoice } from "../hooks/useVoice";

function VoicePage() {
  const navigate = useNavigate();
  const {
    isRecording,
    isProcessing,
    isSpeaking,
    error,
    transcript,
    responseText,
    audioUrl,
    conversationId,
    settings,
    startRecording,
    stopRecording,
    sendVoice,
    stopSpeaking,
    speakText,
    clearConversation,
    loadSettings,
  } = useVoice();

  const [history, setHistory] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [speechRate, setSpeechRate] = useState("+0%");
  const [autoPlay, setAutoPlay] = useState(true);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    if (settings) {
      setSelectedVoice(settings.tts_voice);
      setSpeechRate(settings.tts_rate);
    }
  }, [settings]);

  // Add to history when we get a response
  useEffect(() => {
    if (transcript && responseText) {
      setHistory((prev) => [
        ...prev,
        { user: transcript, assistant: responseText, timestamp: new Date() },
      ]);
    }
  }, [transcript, responseText]);

  const handleRecordToggle = async () => {
    if (isRecording) {
      const blob = await stopRecording();
      if (blob) {
        await sendVoice(blob, {
          voice: selectedVoice,
          rate: speechRate,
          auto_play: autoPlay,
        });
      }
    } else {
      await startRecording();
    }
  };

  const handleKeyDown = (e) => {
    if (e.code === "Space" && !isProcessing && !isSpeaking) {
      e.preventDefault();
      handleRecordToggle();
    }
    if (e.code === "Escape") {
      if (isRecording) stopRecording();
      if (isSpeaking) stopSpeaking();
    }
  };

  return (
    <div
      className="min-h-screen bg-chat-bg flex flex-col"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-700/50">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/")}
            className="p-2 rounded-lg hover:bg-sidebar-hover text-neutral-400 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-lg font-semibold text-white">Voice Assistant</h1>
            <p className="text-xs text-neutral-500">Speak naturally, get responses</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`p-2 rounded-lg transition-colors ${
              showSettings ? "bg-accent/20 text-accent" : "hover:bg-sidebar-hover text-neutral-400"
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <button
            onClick={clearConversation}
            className="p-2 rounded-lg hover:bg-sidebar-hover text-neutral-400 transition-colors"
            title="New conversation"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && settings && (
        <div className="border-b border-neutral-700/50 bg-neutral-800/50 p-4">
          <div className="max-w-2xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-neutral-400 mb-1">Voice</label>
              <select
                value={selectedVoice || ""}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-sm text-white focus:outline-none focus:border-accent"
              >
                {settings.available_voices?.map((v) => (
                  <option key={v.name} value={v.name}>
                    {v.display_name} ({v.gender})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-neutral-400 mb-1">Speed</label>
              <select
                value={speechRate}
                onChange={(e) => setSpeechRate(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-sm text-white focus:outline-none focus:border-accent"
              >
                <option value="-50%">Very Slow</option>
                <option value="-25%">Slow</option>
                <option value="+0%">Normal</option>
                <option value="+25%">Fast</option>
                <option value="+50%">Very Fast</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-neutral-400 mb-1">Auto-play</label>
              <button
                onClick={() => setAutoPlay(!autoPlay)}
                className={`w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  autoPlay
                    ? "bg-accent/20 text-accent border border-accent/30"
                    : "bg-neutral-700 text-neutral-400 border border-neutral-600"
                }`}
              >
                {autoPlay ? "Enabled" : "Disabled"}
              </button>
            </div>
          </div>
          <div className="max-w-2xl mx-auto mt-3 flex gap-4 text-xs text-neutral-500">
            <span>STT: {settings.stt_model} ({settings.stt_device})</span>
            <span>TTS: {settings.tts_engine || "edge-tts"}</span>
            <span>Max: {settings.max_audio_size_mb}MB / {settings.max_audio_duration_sec}s</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-4 py-8">
          {/* Conversation History */}
          {history.length > 0 && (
            <div className="space-y-4 mb-8">
              {history.map((item, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-end">
                    <div className="bg-accent text-white rounded-2xl px-4 py-3 max-w-[80%]">
                      <p className="text-sm">{item.user}</p>
                    </div>
                  </div>
                  <div className="flex justify-start">
                    <div className="bg-chat-ai border border-neutral-700/50 text-neutral-100 rounded-2xl px-4 py-3 max-w-[80%]">
                      <p className="text-sm">{item.assistant}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Status Messages */}
          {transcript && !responseText && (
            <div className="text-center mb-4">
              <p className="text-neutral-400 text-sm">Transcribed:</p>
              <p className="text-white text-lg">{transcript}</p>
            </div>
          )}

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Empty State */}
          {history.length === 0 && !isRecording && !isProcessing && (
            <div className="text-center py-16">
              <div className="w-24 h-24 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-6">
                <svg className="w-12 h-12 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Voice Assistant</h2>
              <p className="text-neutral-400 text-sm max-w-md mx-auto mb-6">
                Click the microphone or press <kbd className="px-1.5 py-0.5 bg-neutral-700 rounded text-xs">Space</kbd> to start speaking.
                The AI will listen, think, and respond with voice.
              </p>
              <div className="flex items-center justify-center gap-6 text-xs text-neutral-500">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <span>STT: Faster-Whisper</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                  <span>TTS: Edge TTS</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-purple-500" />
                  <span>Memory: Active</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recording Controls */}
      <div className="border-t border-neutral-700/50 bg-chat-bg p-6">
        <div className="max-w-2xl mx-auto flex flex-col items-center gap-4">
          {/* Status Text */}
          <p className="text-sm text-neutral-400 h-5">
            {isRecording
              ? "Recording... Press Space or click to stop"
              : isProcessing
              ? "Processing your voice..."
              : isSpeaking
              ? "Speaking... Press Escape to stop"
              : "Ready to listen"}
          </p>

          {/* Main Record Button */}
          <div className="relative">
            {/* Pulse animation when recording */}
            {isRecording && (
              <div className="absolute inset-0 rounded-full bg-red-500/30 animate-ping" />
            )}
            <button
              onClick={handleRecordToggle}
              disabled={isProcessing}
              className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${
                isRecording
                  ? "bg-red-500 hover:bg-red-600 scale-110"
                  : isProcessing
                  ? "bg-neutral-600 cursor-not-allowed"
                  : "bg-accent hover:bg-accent-hover hover:scale-105"
              }`}
            >
              {isProcessing ? (
                <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : isRecording ? (
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              ) : (
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>
          </div>

          {/* Secondary Controls */}
          <div className="flex items-center gap-4">
            {isSpeaking && (
              <button
                onClick={stopSpeaking}
                className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 rounded-xl text-sm text-red-400 transition-colors"
              >
                Stop Speaking
              </button>
            )}
            {audioUrl && !isSpeaking && (
              <button
                onClick={() => {
                  const audio = new Audio(audioUrl);
                  audio.play();
                }}
                className="px-4 py-2 bg-neutral-700 hover:bg-neutral-600 rounded-xl text-sm text-white transition-colors"
              >
                Replay Response
              </button>
            )}
          </div>

          {/* Keyboard Shortcuts */}
          <p className="text-xs text-neutral-600">
            <kbd className="px-1 py-0.5 bg-neutral-800 rounded">Space</kbd> Record/Stop
            {" · "}
            <kbd className="px-1 py-0.5 bg-neutral-800 rounded">Esc</kbd> Stop speaking
          </p>
        </div>
      </div>
    </div>
  );
}

export default VoicePage;

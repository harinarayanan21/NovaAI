import { useState, useCallback, useRef, useEffect } from "react";
import { voiceApi } from "../services/api";

export function useVoice() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState(null);
  const [transcript, setTranscript] = useState("");
  const [responseText, setResponseText] = useState("");
  const [audioUrl, setAudioUrl] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [settings, setSettings] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioElementRef = useRef(null);
  const streamRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, []);

  // Load voice settings
  const loadSettings = useCallback(async () => {
    try {
      const { data } = await voiceApi.settings();
      setSettings(data);
    } catch (err) {
      console.error("Failed to load voice settings:", err);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const startRecording = useCallback(async () => {
    setError(null);
    setTranscript("");
    setResponseText("");
    setAudioUrl(null);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
    } catch (err) {
      setError("Microphone access denied. Please allow microphone access.");
      console.error("Recording error:", err);
    }
  }, []);

  const stopRecording = useCallback(async () => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === "inactive") {
        resolve(null);
        return;
      }

      mediaRecorderRef.current.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setIsRecording(false);

        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }

        resolve(blob);
      };

      mediaRecorderRef.current.stop();
    });
  }, []);

  const sendVoice = useCallback(
    async (audioBlob, options = {}) => {
      if (!audioBlob) return;
      setIsProcessing(true);
      setError(null);

      try {
        // Convert blob to base64
        const reader = new FileReader();
        const base64Promise = new Promise((resolve) => {
          reader.onloadend = () => {
            const base64 = reader.result.split(",")[1];
            resolve(base64);
          };
          reader.readAsDataURL(audioBlob);
        });
        const audioBase64 = await base64Promise;

        // Send to backend
        const { data } = await voiceApi.chat(audioBase64, {
          filename: "recording.webm",
          conversation_id: conversationId,
          voice: options.voice || settings?.tts_voice,
          rate: options.rate || settings?.tts_rate,
          auto_play: options.auto_play !== false,
          ...options,
        });

        setTranscript(data.transcription?.text || "");
        setResponseText(data.response_text || "");
        setConversationId(data.conversation_id);

        // Play audio response
        if (data.response_audio) {
          const binaryString = atob(data.response_audio);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const audioBlob = new Blob([bytes], { type: "audio/mp3" });
          const url = URL.createObjectURL(audioBlob);
          setAudioUrl(url);

          // Auto-play
          if (options.auto_play !== false) {
            const audio = new Audio(url);
            audioElementRef.current = audio;
            audio.onplay = () => setIsSpeaking(true);
            audio.onended = () => setIsSpeaking(false);
            audio.onerror = () => setIsSpeaking(false);
            await audio.play();
          }
        }

        return data;
      } catch (err) {
        setError(err.message);
        console.error("Voice chat error:", err);
      } finally {
        setIsProcessing(false);
      }
    },
    [conversationId, settings]
  );

  const stopSpeaking = useCallback(() => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current.currentTime = 0;
      setIsSpeaking(false);
    }
  }, []);

  const speakText = useCallback(
    async (text, options = {}) => {
      try {
        setIsSpeaking(true);
        const { data } = await voiceApi.speak(
          text,
          options.voice || settings?.tts_voice,
          options.rate || settings?.tts_rate
        );

        if (data.audio) {
          const binaryString = atob(data.audio);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const audioBlob = new Blob([bytes], { type: "audio/mp3" });
          const url = URL.createObjectURL(audioBlob);
          setAudioUrl(url);

          const audio = new Audio(url);
          audioElementRef.current = audio;
          audio.onended = () => setIsSpeaking(false);
          audio.onerror = () => setIsSpeaking(false);
          await audio.play();
        }
      } catch (err) {
        setIsSpeaking(false);
        console.error("TTS error:", err);
      }
    },
    [settings]
  );

  const clearConversation = useCallback(() => {
    setConversationId(null);
    setTranscript("");
    setResponseText("");
    setAudioUrl(null);
    setError(null);
    stopSpeaking();
  }, [stopSpeaking]);

  return {
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
  };
}

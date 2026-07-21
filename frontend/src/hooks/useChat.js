import { useState, useCallback } from "react";
import { sendMessage, conversationApi } from "../services/api";

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);

  const loadMessages = useCallback(async (convId) => {
    setConversationId(convId);
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await conversationApi.getMessages(convId);
      setMessages(data);
    } catch (err) {
      setError(err.message);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const send = useCallback(async (text) => {
    const userMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const data = await sendMessage(text, conversationId);
      const aiMessage = { role: "assistant", content: data.response };
      setMessages((prev) => [...prev, aiMessage]);
      setConversationId(data.conversation_id);
      return data.conversation_id;
    } catch (err) {
      setError(err.message);
      const errorMessage = {
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }, []);

  return { messages, isLoading, error, conversationId, send, loadMessages, clearChat };
}

import { useState, useEffect, useCallback } from "react";
import { conversationApi } from "../services/api";

export function useConversations() {
  const [conversations, setConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchConversations = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await conversationApi.list();
      setConversations(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const rename = useCallback(async (id, title) => {
    const { data } = await conversationApi.update(id, title);
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? data : c))
    );
    return data;
  }, []);

  const remove = useCallback(async (id) => {
    await conversationApi.delete(id);
    setConversations((prev) => prev.filter((c) => c.id !== id));
  }, []);

  const addConversation = useCallback((conv) => {
    setConversations((prev) => [conv, ...prev]);
  }, []);

  const refresh = useCallback(() => {
    fetchConversations();
  }, [fetchConversations]);

  return { conversations, isLoading, error, addConversation, rename, remove, refresh };
}

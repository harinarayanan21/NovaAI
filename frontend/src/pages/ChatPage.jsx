import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";
import { useChat } from "../hooks/useChat";
import { useConversations } from "../hooks/useConversations";

function ChatPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { messages, isLoading, conversationId: activeId, send, loadMessages, clearChat } = useChat();
  const { conversations, addConversation, rename, remove } = useConversations();

  useEffect(() => {
    if (conversationId) {
      loadMessages(Number(conversationId));
    }
  }, [conversationId, loadMessages]);

  const toggleSidebar = () => setSidebarOpen((prev) => !prev);

  const handleNewChat = () => {
    clearChat();
    navigate("/");
  };

  const handleSelectConversation = (id) => {
    loadMessages(id);
    navigate(`/c/${id}`);
    setSidebarOpen(false);
  };

  const handleSend = async (text) => {
    const convId = await send(text);
    if (convId && !conversationId) {
      const conv = conversations.find((c) => c.id === convId);
      if (!conv) {
        addConversation({ id: convId, title: text.length > 50 ? text.slice(0, 50).trim() + "..." : text, created_at: new Date().toISOString(), updated_at: new Date().toISOString() });
      }
      navigate(`/c/${convId}`, { replace: true });
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={toggleSidebar}
        conversations={conversations}
        activeId={conversationId ? Number(conversationId) : activeId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onRename={rename}
        onDelete={remove}
      />

      <main className="flex-1 flex flex-col min-w-0 lg:ml-64">
        <Header onToggleSidebar={toggleSidebar} />
        <ChatWindow messages={messages} isLoading={isLoading} />
        <ChatInput onSend={handleSend} isLoading={isLoading} />
      </main>
    </div>
  );
}

export default ChatPage;

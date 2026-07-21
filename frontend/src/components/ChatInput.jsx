import { useState, useRef, useEffect } from "react";

function ChatInput({ onSend, isLoading }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-neutral-700/50 bg-chat-bg p-4">
      <form
        onSubmit={handleSubmit}
        className="max-w-3xl mx-auto flex items-end gap-3"
      >
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            rows={1}
            disabled={isLoading}
            className="w-full resize-none rounded-xl bg-neutral-800 border border-neutral-600 px-4 py-3 pr-12 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
          />
        </div>
        <button
          type="submit"
          disabled={!text.trim() || isLoading}
          className="p-3 rounded-xl bg-accent hover:bg-accent-hover disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200"
        >
          <svg
            className="w-5 h-5 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </form>
      <p className="text-center text-xs text-neutral-600 mt-2">
        AI can make mistakes. Verify important information.
      </p>
    </div>
  );
}

export default ChatInput;

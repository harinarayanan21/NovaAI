import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import LoadingIndicator from "./LoadingIndicator";

function ChatWindow({ messages, isLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center px-4">
          <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center mb-4">
            <svg
              className="w-8 h-8 text-accent"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">
            How can I help you today?
          </h2>
          <p className="text-neutral-400 text-sm max-w-md">
            Ask me anything. I am powered by Groq for fast, intelligent
            responses.
          </p>
        </div>
      ) : (
        <div className="max-w-3xl mx-auto px-4 py-6">
          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}
          {isLoading && <LoadingIndicator />}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}

export default ChatWindow;

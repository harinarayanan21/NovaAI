function LoadingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-chat-ai border border-neutral-700/50 rounded-2xl px-4 py-3">
        <div className="flex items-center gap-2 mb-1.5">
          <div className="w-5 h-5 rounded-full bg-accent flex items-center justify-center">
            <svg
              className="w-3 h-3 text-white"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
            </svg>
          </div>
          <span className="text-xs font-medium text-neutral-400">
            Thinking...
          </span>
        </div>
        <div className="flex items-center gap-1.5 px-1 py-1">
          <div className="w-2 h-2 bg-neutral-500 rounded-full animate-pulse-dot" style={{ animationDelay: "0s" }} />
          <div className="w-2 h-2 bg-neutral-500 rounded-full animate-pulse-dot" style={{ animationDelay: "0.2s" }} />
          <div className="w-2 h-2 bg-neutral-500 rounded-full animate-pulse-dot" style={{ animationDelay: "0.4s" }} />
        </div>
      </div>
    </div>
  );
}

export default LoadingIndicator;

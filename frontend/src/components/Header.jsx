function Header({ onToggleSidebar }) {
  return (
    <header className="flex items-center gap-3 px-4 py-3 border-b border-neutral-700/50 bg-chat-bg lg:hidden">
      <button
        onClick={onToggleSidebar}
        className="p-1.5 rounded-lg hover:bg-sidebar-hover text-neutral-400"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>
      <h1 className="text-sm font-medium text-white">AI Assistant</h1>
    </header>
  );
}

export default Header;

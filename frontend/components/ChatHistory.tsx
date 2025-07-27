import React, { useState, useEffect } from 'react';
import { type ChatSession } from '../types';

interface ChatHistoryProps {
  onLoadChat: (sessionId: string) => void;
  user?: any;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ onLoadChat, user }) => {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSessions, setSelectedSessions] = useState<string[]>([]);

  useEffect(() => {
    const savedSessions = localStorage.getItem('chatSessions');
    if (savedSessions) {
      setChatSessions(JSON.parse(savedSessions));
    }
  }, []);

  const deleteChatSession = (sessionId: string) => {
    const updatedSessions = chatSessions.filter(s => s.id !== sessionId);
    setChatSessions(updatedSessions);
    localStorage.setItem('chatSessions', JSON.stringify(updatedSessions));
  };

  const deleteSelectedSessions = () => {
    const updatedSessions = chatSessions.filter(s => !selectedSessions.includes(s.id));
    setChatSessions(updatedSessions);
    localStorage.setItem('chatSessions', JSON.stringify(updatedSessions));
    setSelectedSessions([]);
  };

  const toggleSessionSelection = (sessionId: string) => {
    setSelectedSessions(prev => 
      prev.includes(sessionId) 
        ? prev.filter(id => id !== sessionId)
        : [...prev, sessionId]
    );
  };

  const filteredSessions = chatSessions.filter(session => 
    session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    session.messages.some(msg => msg.text.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="h-full rounded-3xl flex flex-col shadow-2xl backdrop-blur-2xl bg-gradient-to-br from-slate-900/80 via-gray-800/60 to-slate-900/80 border border-blue-500/20">
      <header className="p-6 border-b border-blue-400/20 shrink-0 bg-gradient-to-r from-blue-500/10 via-slate-500/5 to-gray-500/10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {user?.photoURL ? (
              <img src={user.photoURL} alt="Profile" className="w-10 h-10 rounded-full object-cover" />
            ) : (
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                {user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'}
              </div>
            )}
            <div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-white via-blue-200 to-slate-200 bg-clip-text text-transparent">Chat History</h2>
              <p className="text-sm text-gray-400 mt-1">{filteredSessions.length} conversations</p>
            </div>
          </div>
          {selectedSessions.length > 0 && (
            <button
              onClick={deleteSelectedSessions}
              className="px-4 py-2 bg-red-600/50 text-white rounded-lg hover:bg-red-500/50 transition-all duration-300 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete ({selectedSessions.length})
            </button>
          )}
        </div>
        <div className="relative">
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-500/30 rounded-lg py-2 pl-10 pr-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400/50"
          />
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </header>
      
      <div className="flex-1 overflow-y-auto p-6">
        {filteredSessions.length === 0 ? (
          <div className="text-center text-gray-500 py-16">
            <div className="text-6xl mb-4">💬</div>
            <p className="text-lg mb-2">{searchTerm ? 'No matching conversations' : 'No chat history yet'}</p>
            <p className="text-sm">{searchTerm ? 'Try a different search term' : 'Start a conversation to see your chat history here'}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredSessions.map((session) => (
              <div
                key={session.id}
                className={`bg-gradient-to-r from-slate-700/50 to-gray-700/50 rounded-2xl p-6 border transition-all duration-300 hover:scale-105 ${
                  selectedSessions.includes(session.id) 
                    ? 'border-blue-400/60 bg-blue-500/10' 
                    : 'border-slate-500/30 hover:border-blue-400/40'
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-3 flex-1">
                    <input
                      type="checkbox"
                      checked={selectedSessions.includes(session.id)}
                      onChange={() => toggleSessionSelection(session.id)}
                      className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-500 rounded focus:ring-blue-500"
                    />
                    <h3 className="text-lg font-semibold text-white truncate">{session.title}</h3>
                  </div>
                  <button
                    onClick={() => deleteChatSession(session.id)}
                    className="text-gray-400 hover:text-red-400 transition-colors p-1"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                <div className="text-sm text-gray-400 mb-4">
                  <div>Created: {new Date(session.createdAt).toLocaleDateString()}</div>
                  <div>Messages: {session.messages.length}</div>
                </div>
                <button
                  onClick={() => onLoadChat(session.id)}
                  className="w-full px-4 py-2 bg-gradient-to-r from-blue-600/50 to-indigo-600/50 text-white rounded-lg hover:from-blue-500/50 hover:to-indigo-500/50 transition-all duration-300"
                >
                  Load Conversation
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatHistory;
import React, { useState, useEffect } from 'react';
import { LogoIcon, ChatBubbleIcon, DashboardIcon, AnalyticsIcon, BillIcon, ProfileIcon, LogoutIcon } from './IconComponents';
import { type View, type ChatSession } from '../types';
import FiMoneyConfig from './FiMoneyConfig';
import { User } from 'firebase/auth';

const TypingText: React.FC = () => {
    const [displayText, setDisplayText] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showCursor, setShowCursor] = useState(true);
    const fullText = 'Let me speak to your money';

    useEffect(() => {
        if (currentIndex < fullText.length) {
            const timeout = setTimeout(() => {
                setDisplayText(fullText.slice(0, currentIndex + 1));
                setCurrentIndex(currentIndex + 1);
            }, 100);
            return () => clearTimeout(timeout);
        } else {
            // Start blinking cursor after typing is done
            const cursorInterval = setInterval(() => {
                setShowCursor(prev => !prev);
            }, 500);
            return () => clearInterval(cursorInterval);
        }
    }, [currentIndex, fullText]);

    return (
        <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
            {displayText}
            <span className={`ml-0.5 ${showCursor ? 'opacity-100' : 'opacity-0'} transition-opacity`}>|</span>
        </span>
    );
};

const HistoryIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

interface NavItemProps {
    icon: React.ElementType;
    label: View;
    isActive: boolean;
    onClick: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ icon: Icon, label, isActive, onClick }) => {
    const displayLabel = label === 'ChatHistory' ? 'Chat History' : label;
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-colors ${isActive ? 'bg-[rgb(var(--color-accent-rgb),0.15)] text-[rgb(var(--color-accent-rgb))]' : 'text-zinc-400 hover:bg-zinc-700 hover:text-white'}`}
        >
            <Icon className="w-6 h-6" />
            <span className="font-semibold">{displayLabel}</span>
        </button>
    );
};

interface SidebarProps {
    activeView: View;
    setActiveView: (view: View) => void;
    onLogout: () => void;
    onLoadChat?: (sessionId: string) => void;
    user: User | null;
}

const Sidebar: React.FC<SidebarProps> = ({ activeView, setActiveView, onLogout, onLoadChat, user }) => {
    const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
    const [showDashboardDropdown, setShowDashboardDropdown] = useState(false);
    const [showFiMoneyConfig, setShowFiMoneyConfig] = useState(false);

    useEffect(() => {
        const loadSessions = () => {
            const savedSessions = localStorage.getItem('chatSessions');
            if (savedSessions) {
                setChatSessions(JSON.parse(savedSessions));
            }
        };
        
        loadSessions();
        
        // Listen for storage changes to update chat sessions
        const handleStorageChange = () => loadSessions();
        window.addEventListener('storage', handleStorageChange);
        
        // Custom event for when chat sessions are updated
        const handleChatUpdate = () => loadSessions();
        window.addEventListener('chatSessionsUpdated', handleChatUpdate);
        
        return () => {
            window.removeEventListener('storage', handleStorageChange);
            window.removeEventListener('chatSessionsUpdated', handleChatUpdate);
        };
    }, []);

    const handleLoadChat = (sessionId: string) => {
        if (onLoadChat) {
            onLoadChat(sessionId);
        }
        setActiveView('Chat');
    };

    const deleteChatSession = (sessionId: string) => {
        const updatedSessions = chatSessions.filter(s => s.id !== sessionId);
        setChatSessions(updatedSessions);
        localStorage.setItem('chatSessions', JSON.stringify(updatedSessions));
        window.dispatchEvent(new CustomEvent('chatSessionsUpdated'));
    };

    return (
        <aside className="w-64 bg-white dark:bg-gray-900 p-4 flex flex-col h-screen shrink-0 border-r border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3 mb-1 px-2">
                <img src="/arthasashtri.png" alt="Arthasashtri" className="w-8 h-8 object-contain" />
                <span className="font-bold text-xl text-gray-900 dark:text-white">Arthasashtri</span>
            </div>

            <div className="mb-2 px-3 text-center">
                <TypingText />
            </div>

            <div className="flex-1 overflow-hidden flex flex-col">
                <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3 px-2">Recent Chats</h3>
                <div className="flex-1 overflow-y-auto space-y-1">
                    {chatSessions.map((session) => (
                        <div key={session.id} className="flex items-center gap-1 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group">
                            <button
                                onClick={() => handleLoadChat(session.id)}
                                className="flex-1 flex items-center gap-2 text-left text-sm text-gray-700 dark:text-gray-300"
                            >
                                <ChatBubbleIcon className="w-4 h-4 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300" />
                                <span className="truncate">{session.title}</span>
                            </button>
                            <button
                                onClick={() => deleteChatSession(session.id)}
                                className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        </div>
                    ))}
                    {chatSessions.length === 0 && (
                        <div className="text-center text-gray-500 py-4">
                            <p className="text-xs text-gray-500 dark:text-gray-400">No chats yet</p>
                        </div>
                    )}
                </div>
            </div>



            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex flex-col space-y-2 mb-4">
                    <button
                        onClick={() => setActiveView('ChatHistory')}
                        className={`w-full flex items-center space-x-3 p-2 rounded-lg transition-colors text-sm ${activeView === 'ChatHistory' ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
                    >
                        <HistoryIcon className="w-4 h-4" />
                        <span>Chat History</span>
                    </button>
                    <button
                        onClick={() => setActiveView('Profile')}
                        className={`w-full flex items-center space-x-3 p-2 rounded-lg transition-colors text-sm ${activeView === 'Profile' ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
                    >
                        <ProfileIcon className="w-4 h-4" />
                        <span>Profile</span>
                    </button>
                </div>
                {user && (
                    <div className="flex items-center space-x-3 p-3 mb-2">
                        {user.photoURL ? (
                            <img src={user.photoURL} alt="Profile" className="w-8 h-8 rounded-full" />
                        ) : (
                            <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                {user.displayName?.charAt(0) || user.email?.charAt(0) || 'U'}
                            </div>
                        )}
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                {user.displayName || 'User'}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                                {user.email}
                            </p>
                        </div>
                    </div>
                )}
                <button
                    onClick={onLogout}
                    className="w-full flex items-center space-x-3 p-3 rounded-lg transition-colors text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white"
                >
                    <LogoutIcon className="w-6 h-6" />
                    <span className="font-semibold">Logout</span>
                </button>
            </div>
            
            <FiMoneyConfig 
                isOpen={showFiMoneyConfig} 
                onClose={() => setShowFiMoneyConfig(false)} 
            />
        </aside>
    );
};

export default Sidebar;
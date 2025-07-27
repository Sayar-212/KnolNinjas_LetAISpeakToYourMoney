
import React, { useState } from 'react';
import { UserCircleIcon } from './IconComponents';

interface HeaderProps {
    title: string;
    user?: any;
    onNavigate?: (view: string) => void;
    onLogout?: () => void;
}

const Header: React.FC<HeaderProps> = ({ title, user, onNavigate, onLogout }) => {
    const [showDropdown, setShowDropdown] = useState(false);
    return (
        <header className="flex items-center justify-between p-4 px-8 border-b border-zinc-800 bg-[#131314] sticky top-0 z-50">
            <h1 className="text-xl font-bold text-white">{title}</h1>
            <div className="flex items-center space-x-4">
                <div className="relative">
                    <button 
                        onClick={() => setShowDropdown(!showDropdown)}
                        className="flex items-center space-x-2 p-1 rounded-md hover:bg-zinc-800"
                    >
                        {user?.photoURL ? (
                            <img src={user.photoURL} alt="Profile" className="w-8 h-8 rounded-full object-cover" />
                        ) : (
                            <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                {user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'}
                            </div>
                        )}
                        <span className="text-sm font-medium text-zinc-300">{user?.displayName || user?.email?.split('@')[0] || 'User'}</span>
                        <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 text-zinc-500 transition-transform ${showDropdown ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </button>
                    {showDropdown && (
                        <div className="absolute right-0 top-full mt-2 w-56 bg-gradient-to-br from-zinc-800 to-zinc-900 border border-zinc-600 rounded-xl shadow-2xl backdrop-blur-sm z-[9999]" style={{boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)'}}>
                            <div className="p-3">
                                <button
                                    onClick={() => {
                                        setShowDropdown(false);
                                        onNavigate?.('Dashboard');
                                    }}
                                    className="w-full text-left px-4 py-3 text-sm text-zinc-200 hover:bg-gradient-to-r hover:from-blue-600/20 hover:to-purple-600/20 rounded-lg transition-all duration-200 flex items-center gap-3 hover:text-white"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H9a2 2 0 01-2-2z" />
                                    </svg>
                                    Dashboard
                                </button>
                                <button
                                    onClick={() => {
                                        setShowDropdown(false);
                                        // Trigger Fi Money Config modal
                                        window.dispatchEvent(new CustomEvent('openFiMoneyConfig'));
                                    }}
                                    className="w-full text-left px-4 py-3 text-sm text-zinc-200 hover:bg-gradient-to-r hover:from-blue-600/20 hover:to-purple-600/20 rounded-lg transition-all duration-200 flex items-center gap-3 hover:text-white"
                                >
                                    <img src="https://oppositehq.com/static/300b53dd22c264422230289be857bbb0/b2704/Logo_Fi_3c4ebbcf42.png" alt="Fi" className="w-4 h-4 object-contain" onError={(e) => {
                                        e.currentTarget.src = '/arthasashtri.png';
                                    }} />
                                    Configure Fi Money MCP
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
};

export default Header;

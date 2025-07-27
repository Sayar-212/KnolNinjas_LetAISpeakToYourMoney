import React, { useState, useEffect, useRef } from 'react';
import { SendIcon, SparklesIcon, MicrophoneIcon } from './IconComponents';
import { type ChatMessage, type ChatSession } from '../types';
import { startChatSession } from '../services/geminiService';
import { memoryService, getConversationSummariesForAI } from '../services/memoryService';
import type { Chat } from '@google/genai';
import FiMoneyConfig from './FiMoneyConfig';

// Simple markdown renderer component
const MarkdownRenderer: React.FC<{ content: string }> = ({ content }) => {
    const renderMarkdown = (text: string) => {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code class="bg-gray-200 dark:bg-gray-700 px-1 rounded text-sm">$1</code>')
            .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg overflow-x-auto my-2"><code>$1</code></pre>')
            .replace(/!\[([^\]]*)\]\(([^\)]+)\)/g, '<img src="$2" alt="$1" class="max-w-full h-auto rounded-lg my-2" />')
            .replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" class="text-blue-600 dark:text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">$1</a>')
            .replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
            .replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold mt-4 mb-2">$1</h2>')
            .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>')
            .replace(/^- (.*$)/gm, '<li class="ml-4">• $1</li>')
            .replace(/\n/g, '<br />');
    };

    return (
        <div 
            className="prose prose-sm max-w-none dark:prose-invert"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
        />
    );
};

// Helper to check for speech recognition API
const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

const ChatPanel = React.forwardRef<any, { user?: any }>((props, ref) => {
    const { user } = props;
    const [chat, setChat] = useState<Chat | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [isVisible, setIsVisible] = useState(false);

    const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [showUserDropdown, setShowUserDropdown] = useState(false);
    const [showFiMoneyConfig, setShowFiMoneyConfig] = useState(false);
    const [attachments, setAttachments] = useState<File[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const recognitionRef = useRef<any>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const savedSessions = localStorage.getItem('chatSessions');
        if (savedSessions) {
            setChatSessions(JSON.parse(savedSessions));
        }
        startNewChat();
        setTimeout(() => setIsVisible(true), 100);

        const handleNewChat = () => {
            startNewChat();
        };
        window.addEventListener('startNewChat', handleNewChat);
        
        const handleSetActiveView = (event: any) => {
            if (event.detail === 'Dashboard') {
                window.dispatchEvent(new CustomEvent('navigateToDashboard'));
            }
        };
        window.addEventListener('setActiveView', handleSetActiveView);
        
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript;
                setInput(prev => (prev ? prev + ' ' : '') + transcript);
                setIsListening(false);
            };
            recognition.onerror = (event: any) => {
                console.error('Speech recognition error:', event.error);
                setIsListening(false);
            };
            recognition.onend = () => {
                setIsListening(false);
            };
            recognitionRef.current = recognition;
        }

        return () => {
            // Auto-save when component unmounts or view changes
            if (currentSessionId && messages.length > 1) {
                const hasUserMessages = messages.some(m => m.sender === 'user');
                if (hasUserMessages) {
                    saveCurrentSession();
                }
            }
            window.removeEventListener('startNewChat', handleNewChat);
            window.removeEventListener('setActiveView', handleSetActiveView);
        };
    }, []);

    const startNewChat = () => {
        // Save current chat before starting new one
        if (currentSessionId && messages.length > 1) {
            const hasUserMessages = messages.some(m => m.sender === 'user');
            if (hasUserMessages) {
                saveCurrentSession();
            }
        }
        
        const chatSession = startChatSession();
        setChat(chatSession);
        const newSessionId = Date.now().toString();
        setCurrentSessionId(newSessionId);
        const initialMessage: ChatMessage = {
            id: 'initial',
            text: "Hello! I'm your AI Financial Co-pilot, Arthasashtri. How can I help you optimize your finances today?",
            sender: 'ai',
            timestamp: Date.now()
        };
        setMessages([initialMessage]);
    };

    const generateChatTitle = (firstMessage: string): string => {
        const words = firstMessage.toLowerCase().split(' ');
        const keywords = ['portfolio', 'investment', 'budget', 'expense', 'income', 'savings', 'loan', 'credit', 'debt', 'financial', 'money', 'bank', 'stock', 'crypto', 'tax', 'insurance', 'retirement', 'goal', 'plan', 'analysis'];
        
        // Find relevant keywords
        const relevantWords = words.filter(word => keywords.includes(word) || word.length > 4);
        
        if (relevantWords.length >= 2) {
            return relevantWords.slice(0, 2).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        } else if (relevantWords.length === 1) {
            return relevantWords[0].charAt(0).toUpperCase() + relevantWords[0].slice(1) + ' Chat';
        } else {
            return words.slice(0, 2).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        }
    };

    const saveCurrentSession = () => {
        if (!currentSessionId || messages.length <= 1) return;
        
        const firstUserMessage = messages.find(m => m.sender === 'user');
        const sessionTitle = firstUserMessage ? 
            generateChatTitle(firstUserMessage.text) : 'New Chat';
            
        const newSession: ChatSession = {
            id: currentSessionId,
            title: sessionTitle,
            messages,
            createdAt: parseInt(currentSessionId),
            updatedAt: Date.now()
        };
        
        const savedSessions = localStorage.getItem('chatSessions');
        const existingSessions = savedSessions ? JSON.parse(savedSessions) : [];
        const updatedSessions = [newSession, ...existingSessions.filter((s: ChatSession) => s.id !== currentSessionId)];
        
        setChatSessions(updatedSessions);
        localStorage.setItem('chatSessions', JSON.stringify(updatedSessions));
        window.dispatchEvent(new CustomEvent('chatSessionsUpdated'));
    };

    const loadChatSession = (sessionId: string) => {
        const session = chatSessions.find(s => s.id === sessionId);
        if (session) {
            setMessages(session.messages);
            setCurrentSessionId(sessionId);
            const chatSession = startChatSession();
            setChat(chatSession);
        }
    };

    React.useImperativeHandle(ref, () => ({
        loadChatSession
    }));

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || !chat || isLoading) return;

        const userMessage: ChatMessage = { id: Date.now().toString(), text: input, sender: 'user', timestamp: Date.now() };
        
        // Add to memory for RAG
        if (currentSessionId) {
            memoryService.addMemory(userMessage, currentSessionId);
        }
        
        setMessages(prev => [...prev, userMessage]);
        const userInput = input;
        setInput('');
        setIsLoading(true);

        try {
            let contextualInput = userInput;
            
            // Check if user is asking for conversation summaries
            const isSummaryRequest = userInput.toLowerCase().includes('conversation') && 
                                   (userInput.toLowerCase().includes('summary') || 
                                    userInput.toLowerCase().includes('summarize') ||
                                    userInput.toLowerCase().includes('last') ||
                                    userInput.toLowerCase().includes('previous'));
            
            if (isSummaryRequest) {
                const summaries = getConversationSummariesForAI();
                contextualInput = `${summaries}\n\nUser request: ${userInput}`;
            } else {
                // Get conversation history and memories for regular questions
                const relevantMemories = memoryService.getRelevantMemories(userInput);
                const allSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
                const recentSessions = allSessions.slice(0, 3);
                
                // Add system context about conversation history
                if (recentSessions.length > 0 || relevantMemories.length > 0) {
                    let systemContext = 'SYSTEM CONTEXT (you have access to this information):\n';
                    
                    // Add user information
                    if (user) {
                        systemContext += `User Information:\n`;
                        systemContext += `- Name: ${user.displayName || 'User'}\n`;
                        systemContext += `- Email: ${user.email || 'Not provided'}\n\n`;
                    }
                    
                    if (recentSessions.length > 0) {
                        systemContext += 'Recent conversation summaries:\n';
                        recentSessions.forEach((session, index) => {
                            const userMessages = session.messages.filter(m => m.sender === 'user').slice(0, 2);
                            const aiMessages = session.messages.filter(m => m.sender === 'ai').slice(0, 2);
                            systemContext += `${index + 1}. "${session.title}" - User asked: ${userMessages.map(m => m.text).join(', ')}. AI responded about: ${aiMessages.map(m => m.text.slice(0, 100)).join(', ')}\n`;
                        });
                    }
                    
                    if (relevantMemories.length > 0) {
                        systemContext += `\nRelevant previous topics: ${relevantMemories.join('; ')}\n`;
                    }
                    
                    systemContext += `\nIMPORTANT: Always respond in markdown format. Use **bold**, *italic*, \`code\`, lists, headers, and other markdown features to make responses well-formatted and readable. For images, use ![alt text](url) format.\n`;
                    
                    contextualInput = `${systemContext}\nCURRENT USER QUESTION: ${userInput}`;
                }
            }
            
            const stream = await chat.sendMessageStream({ message: contextualInput });
            let streamedText = '';
            let aiMessageAdded = false;
            
            for await (const chunk of stream) {
                const chunkText = chunk.text;
                streamedText += chunkText;
                
                if (!aiMessageAdded) {
                    const aiMessageId = Date.now().toString();
                    setMessages(prev => [...prev, { id: aiMessageId, text: streamedText, sender: 'ai', timestamp: Date.now() }]);
                    aiMessageAdded = true;
                } else {
                    setMessages(prev => prev.map((msg, index) => 
                        index === prev.length - 1 && msg.sender === 'ai' ? { ...msg, text: streamedText } : msg
                    ));
                }
            }
        } catch (error) {
            console.error('Gemini API error:', error);
            const errorMessage: ChatMessage = {
                id: Date.now().toString(),
                text: "I'm having trouble connecting right now. Please try again later.",
                sender: 'ai',
                timestamp: Date.now()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleMicClick = () => {
        if (!recognitionRef.current) {
            alert("Speech recognition is not supported by your browser.");
            return;
        }
        if (isListening) {
            recognitionRef.current.stop();
        } else {
            recognitionRef.current.start();
            setIsListening(true);
        }
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);
        setAttachments(prev => [...prev, ...files]);
    };

    const removeAttachment = (index: number) => {
        setAttachments(prev => prev.filter((_, i) => i !== index));
    };
    
    return (
        <div className={`h-full flex flex-col bg-white dark:bg-gray-900 transition-all duration-500 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
            <header className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 shrink-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 via-purple-600 to-cyan-500 flex items-center justify-center shadow-lg">
                            <img src="/arthasashtri.png" alt="Arthasashtri" className="w-8 h-8 object-contain filter brightness-0 invert" />
                        </div>
                        <div className="absolute -inset-1 bg-gradient-to-br from-blue-600/20 via-purple-600/20 to-cyan-500/20 rounded-xl blur-sm"></div>
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Arthasashtri</h2>
                        <p className="text-xs text-gray-500 dark:text-gray-400">AI Financial Co-pilot</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={startNewChat}
                        className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200 flex items-center gap-2"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        New Chat
                    </button>
                    <div className="relative">
                        <button
                            onClick={() => setShowUserDropdown(!showUserDropdown)}
                            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors duration-200"
                        >
                            {user?.photoURL ? (
                                <img src={user.photoURL} alt="Profile" className="w-8 h-8 rounded-full object-cover" />
                            ) : (
                                <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                    {user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'}
                                </div>
                            )}
                            <span className="text-gray-700 dark:text-gray-300">{user?.displayName || user?.email?.split('@')[0] || 'User'}</span>
                            <svg className={`w-4 h-4 transition-transform ${showUserDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>
                        {showUserDropdown && (
                            <div className="absolute right-0 top-full mt-2 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50">
                                <div className="p-2">
                                    <button
                                        onClick={() => {
                                            setShowUserDropdown(false);
                                            window.dispatchEvent(new CustomEvent('setActiveView', { detail: 'Dashboard' }));
                                        }}
                                        className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H9a2 2 0 01-2-2z" />
                                        </svg>
                                        Dashboard
                                    </button>
                                    <button
                                        onClick={() => {
                                            setShowUserDropdown(false);
                                            setShowFiMoneyConfig(true);
                                        }}
                                        className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
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
            
            <div className="flex-1 overflow-y-auto p-4 bg-white dark:bg-gray-900">
                <div className="max-w-4xl mx-auto space-y-3">
                    {messages.map((message, index) => (
                        <div key={message.id} className={`flex gap-3 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {message.sender === 'ai' && (
                                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center shrink-0">
                                    <img src="/arthasashtri.png" alt="AI" className="w-5 h-5 object-contain" />
                                </div>
                            )}
                            <div className={`max-w-xs md:max-w-md rounded-lg px-3 py-2 ${message.sender === 'user' 
                                ? 'bg-blue-600 text-white' 
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'}`}>
                                <MarkdownRenderer content={message.text} />
                            </div>
                            {message.sender === 'user' && (
                                user?.photoURL ? (
                                    <img src={user.photoURL} alt="User" className="w-8 h-8 rounded-full object-cover shrink-0" />
                                ) : (
                                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center shrink-0 text-white font-bold text-xs">
                                        {user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'}
                                    </div>
                                )
                            )}
                        </div>
                    ))}
                    
                    {isLoading && (
                        <div className="flex gap-3 justify-start">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center shrink-0">
                                <img src="/arthasashtri.png" alt="AI" className="w-5 h-5 object-contain" />
                            </div>
                            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-2">
                                <div className="flex items-center gap-2">
                                    <div className="flex gap-1">
                                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0s'}}></div>
                                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
                                    </div>
                                    <span className="text-xs text-gray-500 dark:text-gray-400">Typing...</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                <div ref={messagesEndRef} />
            </div>
            
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 shrink-0 bg-white dark:bg-gray-900">
                <div className="max-w-3xl mx-auto">
                    <form onSubmit={handleSend} className="relative">
                        <div className="relative flex items-center">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder={isListening ? "🎤 Listening..." : "Ask about your finances..."}
                                disabled={isLoading}
                                className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-xl py-3 pl-4 pr-20 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                            />
                            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                                <button 
                                    type="button" 
                                    onClick={handleMicClick} 
                                    disabled={!SpeechRecognition} 
                                    className={`p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                                        isListening 
                                            ? 'bg-red-500 text-white' 
                                            : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                                    }`}
                                >
                                    <MicrophoneIcon className="w-4 h-4" />
                                </button>
                                <button 
                                    type="submit" 
                                    disabled={isLoading || !input.trim()} 
                                    className="p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                                >
                                    <SendIcon className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </form>
                    
                    <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500 dark:text-gray-400">Quick:</span>
                            {['💰 Portfolio', '📊 Analytics', '💳 Expenses', '🎯 Goals'].map((action, index) => (
                                <button 
                                    key={index}
                                    onClick={() => setInput(action.split(' ')[1])}
                                    className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                                >
                                    {action}
                                </button>
                            ))}
                        </div>
                        <div className="flex items-center gap-1 text-xs text-green-500">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                            <span>Memory</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <FiMoneyConfig 
                isOpen={showFiMoneyConfig} 
                onClose={() => setShowFiMoneyConfig(false)} 
            />
        </div>
    );
});

export default ChatPanel;
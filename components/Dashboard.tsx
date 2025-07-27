import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './ChatMessage'; // Using ChatMessage file for Sidebar component
import Header from './Header';
import AnalyticsChart from './AnalyticsChart';
import UpcomingBills from './UpcomingBills';
import ChatPanel from './ChatPanel';
import ChatHistory from './ChatHistory';

import AgentsStatus from './HealthScore'; // Using HealthScore file for AgentsStatus component
import ProfileSettings from './ProfileSettings';
import InsightCard from './InsightCard';
import { type View } from '../types';
import { User } from 'firebase/auth';

interface DashboardProps {
    onLogout: () => void;
    user: User | null;
}

const DashboardContent = () => (
    <div className="space-y-8 animate-fade-in">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="lg:col-span-1 transform hover:scale-105 transition-all duration-500">
                <AgentsStatus />
            </div>
            <div className="lg:col-span-1 transform hover:scale-105 transition-all duration-500">
                <InsightCard />
            </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="lg:col-span-1 transform hover:scale-105 transition-all duration-500">
                <AnalyticsChart />
            </div>
            <div className="lg:col-span-1 transform hover:scale-105 transition-all duration-500">
                <UpcomingBills />
            </div>
        </div>
    </div>
);

const Dashboard: React.FC<DashboardProps> = ({ onLogout, user }) => {
    const [activeView, setActiveView] = useState<View>('Chat');
    const [isLoaded, setIsLoaded] = useState(false);
    const chatPanelRef = useRef<any>(null);

    useEffect(() => {
        setIsLoaded(true);
        
        const handleNavigateToDashboard = () => {
            setActiveView('Dashboard');
        };
        window.addEventListener('navigateToDashboard', handleNavigateToDashboard);
        
        return () => {
            window.removeEventListener('navigateToDashboard', handleNavigateToDashboard);
        };
    }, []);

    const handleLoadChat = (sessionId: string) => {
        setActiveView('Chat');
        // This will be handled by ChatPanel's loadChatSession function
        setTimeout(() => {
            if (chatPanelRef.current?.loadChatSession) {
                chatPanelRef.current.loadChatSession(sessionId);
            }
        }, 100);
    };

    const renderContent = () => {
        switch(activeView) {
            case 'Chat':
                return <ChatPanel ref={chatPanelRef} user={user} />;
            case 'Dashboard':
                return <DashboardContent />;
            case 'Profile':
                return <ProfileSettings onLogout={onLogout} user={user} />;
            case 'ChatHistory':
                return <ChatHistory onLoadChat={handleLoadChat} user={user} />;
            default:
                return <div className="text-white flex items-center justify-center h-full text-xl">Select a view</div>;
        }
    };

    return (
        <div className="flex h-screen bg-gradient-to-br from-slate-950 via-gray-900 to-slate-800 overflow-hidden relative">
            {/* Premium Background Effects */}
            <div className="absolute inset-0">
                <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-gray-900 to-slate-800">
                    <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-blue-500/3 to-slate-500/5"></div>
                    <div className="absolute inset-0 bg-gradient-to-bl from-gray-500/3 via-transparent to-blue-500/3"></div>
                </div>
                
                {/* Floating Orbs */}
                <div className="absolute top-20 left-20 w-96 h-96 bg-gradient-conic from-blue-500/8 via-slate-500/8 to-gray-500/8 rounded-full blur-3xl animate-pulse-slow"></div>
                <div className="absolute bottom-20 right-20 w-80 h-80 bg-gradient-radial from-slate-500/6 via-gray-500/4 to-transparent rounded-full blur-3xl animate-pulse-slow delay-1000"></div>
                
                {/* Floating Particles */}
                {[...Array(20)].map((_, i) => (
                    <div
                        key={i}
                        className="absolute animate-float opacity-30"
                        style={{
                            width: `${2 + Math.random() * 4}px`,
                            height: `${2 + Math.random() * 4}px`,
                            background: `radial-gradient(circle, ${['#3b82f6', '#6366f1', '#8b5cf6'][Math.floor(Math.random() * 3)]}, transparent)`,
                            left: `${Math.random() * 100}%`,
                            top: `${Math.random() * 100}%`,
                            animationDelay: `${Math.random() * 10}s`,
                            animationDuration: `${6 + Math.random() * 8}s`,
                        }}
                    />
                ))}
            </div>
            
            <div className={`relative z-10 flex w-full transition-all duration-1000 ${isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                <Sidebar activeView={activeView} setActiveView={setActiveView} onLogout={onLogout} onLoadChat={handleLoadChat} user={user} />
                <div className="flex-1 flex flex-col overflow-hidden backdrop-blur-sm">
                    {activeView !== 'Chat' && <Header title={activeView} user={user} onNavigate={setActiveView} onLogout={onLogout} />}
                    <main className={`flex-1 overflow-y-auto relative ${activeView !== 'Chat' ? 'p-8' : ''}`}>
                        <div className="relative z-10">
                            {renderContent()}
                        </div>
                    </main>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
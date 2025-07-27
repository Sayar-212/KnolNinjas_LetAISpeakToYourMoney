
import React, { useState, useEffect } from 'react';
import LandingPage from './components/LandingPage';
import LoginScreen from './components/LoginScreen';
import Dashboard from './components/Dashboard';
import SignUpScreen from './components/SignUpScreen';
import ForgotPasswordScreen from './components/ForgotPasswordScreen';
import { useAuth } from './useAuth';
import { logOut } from './firebase.config';

type AuthState = 'landing' | 'login' | 'signup' | 'forgot' | 'loggedIn';

const App: React.FC = () => {
  const [authState, setAuthState] = useState<AuthState>('landing');
  const { user, loading } = useAuth();

  useEffect(() => {
    if (user) {
      setAuthState('loggedIn');
    } else if (!loading) {
      // Show landing page for new users when not loading
      setAuthState('landing');
    }
  }, [user, loading]);

  const handleLogin = () => {
    setAuthState('loggedIn');
  };
  
  const handleLogout = async () => {
    try {
      await logOut();
      setAuthState('login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const renderAuthContent = () => {
    switch (authState) {
      case 'landing':
        return <LandingPage onGetStarted={() => setAuthState('login')} />;
      case 'signup':
        return <SignUpScreen onSignUp={handleLogin} onNavigateToLogin={() => setAuthState('login')} onBack={() => setAuthState('landing')} />;
      case 'forgot':
        return <ForgotPasswordScreen onNavigateToLogin={() => setAuthState('login')} />;
      case 'loggedIn':
        return <Dashboard onLogout={handleLogout} user={user} />;
      case 'login':
        return <LoginScreen onLogin={handleLogin} onNavigateToSignup={() => setAuthState('signup')} onNavigateToForgotPassword={() => setAuthState('forgot')} onBack={() => setAuthState('landing')} />;
      case 'landing':
      default:
        return <LandingPage onGetStarted={() => setAuthState('login')} />;
    }
  }

  if (loading) {
    return (
      <div className="bg-[#131314] text-gray-200 min-h-screen font-sans flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="bg-[#131314] text-gray-200 min-h-screen font-sans">
      {renderAuthContent()}
    </div>
  );
};

export default App;

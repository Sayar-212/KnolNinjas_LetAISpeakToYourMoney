import React, { useState } from 'react';
import { LogoIcon } from './IconComponents';

interface ForgotPasswordScreenProps {
  onNavigateToLogin: () => void;
}

const ForgotPasswordScreen: React.FC<ForgotPasswordScreenProps> = ({ onNavigateToLogin }) => {
  const [isSent, setIsSent] = useState(false);

  const handleSendLinkClick = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSent(true);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="w-full max-w-sm text-center">
        <div className="flex justify-center items-center mb-6">
          <LogoIcon className="w-12 h-12 accent-color" />
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">Forgot Password?</h1>
        <p className="text-zinc-400 mb-8">No worries, we'll send you reset instructions.</p>

        {isSent ? (
            <div className="bg-green-500/20 text-green-300 p-4 rounded-md">
                <p>If an account with this email exists, a password reset link has been sent.</p>
            </div>
        ) : (
            <form onSubmit={handleSendLinkClick} className="space-y-4">
              <div>
                <input 
                  type="email" 
                  placeholder="Enter your email"
                  required
                  className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-md focus:outline-none focus:ring-2 ring-accent transition-all"
                />
              </div>
              <button 
                type="submit"
                className="w-full px-4 py-3 bg-accent text-white font-semibold rounded-md hover:opacity-90 focus:outline-none focus:ring-2 ring-accent focus:ring-offset-2 focus:ring-offset-zinc-900 transition-all"
              >
                Send Reset Link
              </button>
            </form>
        )}
        <div className="text-sm text-zinc-500 mt-6">
          <button onClick={onNavigateToLogin} className="hover:accent-color">&larr; Back to Sign In</button>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordScreen;
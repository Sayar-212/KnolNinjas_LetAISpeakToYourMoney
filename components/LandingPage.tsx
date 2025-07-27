import React, { useState, useEffect } from 'react';
import { LogoIcon } from './IconComponents';

interface LandingPageProps {
  onGetStarted: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [currentFeature, setCurrentFeature] = useState(0);
  const [scrollY, setScrollY] = useState(0);
  const [mouseX, setMouseX] = useState(0);
  const [currentView, setCurrentView] = useState<'home' | 'team'>('home');

  useEffect(() => {
    setIsVisible(true);
    
    const interval = setInterval(() => {
      setCurrentFeature((prev) => (prev + 1) % 3);
    }, 4000);
    
    const handleScroll = () => setScrollY(window.scrollY);
    const handleMouseMove = (e: MouseEvent) => setMouseX(e.clientX);
    
    window.addEventListener('scroll', handleScroll);
    window.addEventListener('mousemove', handleMouseMove);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  const features = [
    { 
      title: "Google Gemini AI", 
      desc: "Powered by Google's most advanced multimodal AI model, Gemini analyzes complex financial data with unprecedented accuracy and reasoning capabilities", 
      icon: "🤖",
      logo: "https://upload.wikimedia.org/wikipedia/commons/8/8a/Google_Gemini_logo.svg"
    },
    { 
      title: "Fi Money\nMCP", 
      desc: "Seamlessly integrated with Fi Money's Model Context Protocol for real-time financial data processing and intelligent banking insights", 
      icon: "💳",
      logo: "https://oppositehq.com/static/300b53dd22c264422230289be857bbb0/b2704/Logo_Fi_3c4ebbcf42.png"
    },
    { 
      title: "Multi Agent Agentic AI", 
      desc: "Advanced multi-agent AI system that collaborates intelligently to provide comprehensive financial analysis and personalized recommendations", 
      icon: "🧠",
      logo: "/arthasashtri.png"
    }
  ];

  if (currentView === 'team') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-gray-900 to-slate-800 overflow-hidden relative">
        {/* Team Page Background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-gray-900 to-slate-800">
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-blue-500/3 to-slate-500/5"></div>
          </div>
        </div>

        {/* Back Button */}
        <div className="relative z-10 p-6">
          <button 
            onClick={() => setCurrentView('home')}
            className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white transition-all duration-300 hover:scale-105"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
        </div>

        {/* Team Content */}
        <div className="relative z-10 flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
          <h1 className="text-5xl md:text-7xl font-black text-white mb-12 animate-burden-lift">
            Meet Our Team
          </h1>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              'Sayar Basu',
              'Pradip Maity',
              'Soutrik Das',
              'Arnab Santra',
              'Subhobroto Sasmal'
            ].map((name, index) => (
              <div 
                key={name}
                className="bg-gradient-to-br from-blue-500/10 via-slate-500/5 to-gray-500/10 backdrop-blur-xl border border-blue-400/20 rounded-2xl p-8 hover:border-blue-400/40 transition-all duration-500 hover:scale-105 animate-burden-lift"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="w-20 h-20 bg-gradient-to-r from-blue-400 to-slate-400 rounded-full mx-auto mb-4 flex items-center justify-center text-2xl font-bold text-white">
                  {name.split(' ').map(n => n[0]).join('')}
                </div>
                <h3 className="text-xl font-bold text-white mb-2">{name}</h3>
                <p className="text-gray-400 text-sm">KnolNinjas Team Member</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-gray-900 to-slate-800 overflow-hidden relative">
      {/* Premium Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-gray-900 to-slate-800">
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-blue-500/3 to-slate-500/5"></div>
          <div className="absolute inset-0 bg-gradient-to-bl from-gray-500/3 via-transparent to-blue-500/3"></div>
        </div>

        {/* Soothing Background Orbs */}
        <div className="absolute top-10 left-10 w-[500px] h-[500px] bg-gradient-conic from-blue-500/8 via-slate-500/8 to-gray-500/8 rounded-full blur-3xl animate-pulse-slow transform-gpu"></div>
        <div className="absolute bottom-10 right-10 w-[600px] h-[600px] bg-gradient-radial from-slate-500/6 via-gray-500/4 to-transparent rounded-full blur-3xl animate-pulse-slow delay-1000 transform-gpu"></div>
        <div className="absolute top-1/4 right-1/3 w-96 h-96 bg-gradient-to-r from-gray-500/6 to-blue-500/6 rounded-full blur-2xl animate-pulse-slow delay-2000 transform-gpu"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-gradient-conic from-blue-500/4 via-slate-500/4 to-gray-500/4 rounded-full animate-spin-slow transform-gpu"></div>
        
        {/* Soothing Mesh Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/2 via-transparent to-slate-500/2 animate-pulse-slow"></div>
        <div className="absolute inset-0 bg-gradient-to-tl from-gray-500/1 via-transparent to-blue-500/1 animate-pulse-slow delay-3000"></div>
        
        {/* Premium Floating Elements */}
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="absolute animate-float opacity-40 transform-gpu"
            style={{
              width: `${2 + Math.random() * 6}px`,
              height: `${2 + Math.random() * 6}px`,
              background: `radial-gradient(circle, ${['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#06b6d4', '#10b981'][Math.floor(Math.random() * 6)]}, transparent)`,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 12}s`,
              animationDuration: `${8 + Math.random() * 12}s`,
              boxShadow: `0 0 ${4 + Math.random() * 8}px ${['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7'][Math.floor(Math.random() * 4)]}`
            }}
          />
        ))}
        
        {/* Logo Particles */}
        {[...Array(5)].map((_, i) => (
          <div
            key={`logo-${i}`}
            className="absolute opacity-10 animate-float transform-gpu"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 15}s`,
              animationDuration: `${15 + Math.random() * 20}s`
            }}
          >
            <img 
              src="/arthasashtri.png" 
              alt="Arthasashtri" 
              className="w-4 h-4 object-contain filter blur-sm"
            />
          </div>
        ))}
      </div>

      {/* Navigation */}
      <nav className={`relative z-10 flex justify-between items-center p-6 transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : '-translate-y-10 opacity-0'}`}>
        <div className="flex items-center space-x-4 group cursor-pointer">
          <div className="relative">
            <img 
              src="/arthasashtri.png" 
              alt="Arthasashtri Logo" 
              className="w-10 h-10 object-contain group-hover:scale-110 transition-all duration-500 filter drop-shadow-lg group-hover:drop-shadow-2xl"
            />
            <div className="absolute inset-0 bg-blue-400/30 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500 animate-pulse-slow"></div>
            <div className="absolute -inset-2 bg-gradient-to-r from-blue-400/20 to-slate-400/20 rounded-full blur-lg opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
          </div>
          <span className="text-2xl font-black bg-gradient-to-r from-white via-blue-200 to-slate-200 bg-clip-text text-transparent group-hover:from-blue-300 group-hover:to-slate-300 transition-all duration-500">Arthasashtri</span>
        </div>
        <div className="flex items-center gap-4">
          <button className="px-6 py-2 text-gray-300 hover:text-white transition-all duration-300 hover:scale-105">
            Demo
          </button>
          <button 
            onClick={onGetStarted}
            className="px-6 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full text-white hover:bg-white/20 transition-all duration-300 hover:scale-105"
          >
            Sign In
          </button>
        </div>
      </nav>

      {/* Team Button */}
      <div className="relative z-10 flex justify-center pt-6">
        <button 
          onClick={() => setCurrentView('team')}
          className="px-8 py-3 bg-gradient-to-r from-blue-600/20 to-indigo-600/20 backdrop-blur-sm border border-blue-400/40 rounded-full text-white font-semibold hover:from-blue-600/30 hover:to-indigo-600/30 transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-blue-500/25"
        >
          Team
        </button>
      </div>

      {/* KnolNinjas Presents */}
      <div className="relative z-10 flex justify-center pt-4">
        <div className={`transition-all duration-1000 delay-100 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
          <div className="text-base md:text-lg text-gray-400 font-bold tracking-wider animate-pulse-slow">
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.1s' }}>K</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.15s' }}>n</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.2s' }}>o</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.25s' }}>l</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.3s' }}>N</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.35s' }}>i</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.4s' }}>n</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.45s' }}>j</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.5s' }}>a</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.55s' }}>s</span>
            <span className="inline-block animate-letter-zoom mx-1" style={{ animationDelay: '0.6s' }}></span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.65s' }}>P</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.7s' }}>r</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.75s' }}>e</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.8s' }}>s</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.85s' }}>e</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.9s' }}>n</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.95s' }}>t</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1s' }}>s</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1.05s' }}>.</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1.1s' }}>.</span>
            <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1.15s' }}>.</span>
          </div>
        </div>
      </div>

      {/* Enhanced Smart Logo with 3D Movement */}
      <div className="relative z-10 flex justify-center pt-4">
        <div className={`transition-all duration-2000 delay-200 ${isVisible ? 'translate-y-0 opacity-100 scale-100' : 'translate-y-10 opacity-0 scale-95'}`}>
          <div className="relative group perspective-1000">
            <div 
              className="relative transform-gpu transition-all duration-300 ease-out"
              style={{
                transform: `
                  rotateY(${(mouseX - window.innerWidth / 2) * 0.02}deg)
                  rotateX(${(mouseX - window.innerWidth / 2) * 0.01}deg)
                  translateX(${(mouseX - window.innerWidth / 2) * 0.03}px)
                  translateZ(${Math.abs(mouseX - window.innerWidth / 2) * 0.1}px)
                `,
                transformStyle: 'preserve-3d'
              }}
            >
              <img 
                src="/arthasashtri.png" 
                alt="Arthasashtri" 
                className="w-24 h-24 md:w-32 md:h-32 object-contain mx-auto filter drop-shadow-2xl group-hover:scale-110 transition-all duration-700"
              />
              
              {/* 3D Shadow Layer */}
              <div 
                className="absolute inset-0 bg-black/20 blur-md rounded-full"
                style={{
                  transform: `translateZ(-20px) translateX(${(mouseX - window.innerWidth / 2) * 0.01}px)`,
                  opacity: Math.abs(mouseX - window.innerWidth / 2) * 0.0005
                }}
              ></div>
            </div>
            
            {/* Enhanced Glow Effects */}
            <div 
              className="absolute inset-0 bg-gradient-to-r from-blue-400/40 via-slate-400/40 to-gray-400/40 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-all duration-700 animate-pulse-slow"
              style={{
                transform: `rotateY(${(mouseX - window.innerWidth / 2) * 0.01}deg)`
              }}
            ></div>
            <div className="absolute -inset-8 bg-gradient-to-r from-blue-400/20 via-slate-400/20 to-gray-400/20 rounded-full blur-2xl opacity-60 animate-pulse-slow"></div>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-[70vh] px-6 text-center">
        <div 
          className={`transition-all duration-1500 delay-300 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'}`}
        >
          <h1 className="text-6xl md:text-8xl font-black mb-6 leading-tight">
            <span className="block animate-burden-lift" style={{ animationDelay: '0.2s' }}>
              <span className="text-white">Your </span>
              <span className="text-yellow-400 relative">
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.3s' }}>U</span>
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.35s' }}>l</span>
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.4s' }}>t</span>
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.45s' }}>i</span>
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.5s' }}>m</span>
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.55s' }}>a</span>
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.6s' }}>t</span>
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.65s' }}>e</span>
                <div className="absolute inset-0 bg-yellow-400 blur-2xl opacity-20 animate-pulse"></div>
              </span>
              <span className="text-white"> </span>
              <span className="text-cyan-400 relative">
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.7s' }}>A</span>
                <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.75s' }}>I</span>
                <div className="absolute inset-0 bg-cyan-400 blur-2xl opacity-20 animate-pulse"></div>
              </span>
            </span>
            <span className="block text-blue-400 relative animate-burden-lift" style={{ animationDelay: '0.8s' }}>
              <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.85s' }}>F</span>
              <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.9s' }}>i</span>
              <span className="inline-block animate-letter-zoom" style={{ animationDelay: '0.95s' }}>n</span>
              <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1s' }}>a</span>
              <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1.05s' }}>n</span>
              <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1.1s' }}>c</span>
              <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1.15s' }}>i</span>
              <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1.2s' }}>a</span>
              <span className="inline-block animate-letter-zoom" style={{ animationDelay: '1.25s' }}>l</span>
              <div className="absolute inset-0 bg-blue-400 blur-2xl opacity-20 animate-pulse"></div>
            </span>
            <span className="block text-gray-300 animate-burden-lift" style={{ animationDelay: '1.3s' }}>
              Co-pilot
            </span>
          </h1>
        </div>

        <div 
          className={`transition-all duration-1500 delay-500 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'}`}
        >
          <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-4xl leading-relaxed animate-relief-fade" style={{ animationDelay: '0.8s' }}>
            Transform your financial journey with <span className="text-blue-200 font-medium">Google Gemini AI</span>, <span className="text-slate-200 font-medium">Google Cloud Analytics</span>, and <span className="text-gray-200 font-medium">Google AI Studio</span> integration for <span className="text-green-300 font-medium">intelligent financial decisions</span>.
          </p>
        </div>

        <div 
          className={`flex flex-col sm:flex-row gap-4 justify-center items-center transition-all duration-1500 delay-700 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'}`}
        >
          <button 
            onClick={onGetStarted}
            className="group relative px-16 py-5 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-2xl text-white font-bold text-xl hover:shadow-[0_0_80px_rgba(59,130,246,0.6)] transition-all duration-700 hover:scale-110 overflow-hidden transform-gpu animate-pulse hover:animate-none"
          >
            <span className="relative z-10 flex items-center gap-3">
              <img 
                src="/arthasashtri.png" 
                alt="Arthasashtri" 
                className="w-6 h-6 object-contain group-hover:scale-110 transition-transform duration-500"
              />
              Get Started
              <svg className="w-6 h-6 group-hover:translate-x-2 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 blur-2xl opacity-40 group-hover:opacity-70 transition-opacity duration-700 animate-pulse"></div>
            <div className="absolute -inset-4 bg-gradient-to-r from-blue-400/30 via-indigo-400/30 to-purple-400/30 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
          </button>
          
          <button className="px-12 py-5 border border-blue-400/40 rounded-2xl text-white font-semibold text-lg hover:bg-gradient-to-r hover:from-blue-500/20 hover:to-indigo-500/20 transition-all duration-500 hover:scale-110 hover:border-blue-400/60 hover:shadow-[0_0_50px_rgba(59,130,246,0.3)] backdrop-blur-sm transform-gpu">
            <span className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
              Watch Demo
            </span>
          </button>
        </div>

        {/* Premium Features Grid */}
        <div 
          className={`mt-24 transition-all duration-1500 delay-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'}`}
        >
          <div className="max-w-7xl mx-auto">
            <h2 className="text-4xl md:text-5xl font-black text-center text-white mb-16 animate-burden-lift">
              Powered by <a href="https://ai.google/" target="_blank" rel="noopener noreferrer" className="font-extrabold hover:scale-105 transition-all duration-300 inline-block">
                <span style={{color: '#4285F4'}} className="drop-shadow-lg">G</span>
                <span style={{color: '#DB4437'}} className="drop-shadow-lg">o</span>
                <span style={{color: '#F4B400'}} className="drop-shadow-lg">o</span>
                <span style={{color: '#4285F4'}} className="drop-shadow-lg">g</span>
                <span style={{color: '#0F9D58'}} className="drop-shadow-lg">l</span>
                <span style={{color: '#DB4437'}} className="drop-shadow-lg">e</span>
                <span className="text-white ml-2">AI</span>
              </a>
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <div 
                  key={feature.title}
                  className="relative bg-gradient-to-br from-blue-500/10 via-slate-500/5 to-gray-500/10 backdrop-blur-2xl border border-blue-400/20 rounded-3xl p-8 hover:border-blue-400/40 transition-all duration-700 group hover:shadow-[0_0_60px_rgba(59,130,246,0.2)] hover:scale-105 transform-gpu animate-burden-lift"
                  style={{ animationDelay: `${1.2 + index * 0.2}s` }}
                >
                  {/* Feature Icon */}
                  <div className="text-center mb-6">
                    {index === 0 ? (
                      <img 
                        src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/768px-Google_%22G%22_logo.svg.png" 
                        alt="Google" 
                        className="w-12 h-12 object-contain mx-auto mb-4 group-hover:scale-125 transition-all duration-700 filter drop-shadow-2xl animate-float"
                        onError={(e) => {
                          e.currentTarget.src = '/arthasashtri.png';
                        }}
                      />
                    ) : index === 1 ? (
                      <img 
                        src="https://oppositehq.com/static/300b53dd22c264422230289be857bbb0/b2704/Logo_Fi_3c4ebbcf42.png" 
                        alt="Fi Money" 
                        className="w-12 h-12 object-contain mx-auto mb-4 group-hover:scale-125 transition-all duration-700 filter drop-shadow-2xl animate-float"
                        onError={(e) => {
                          e.currentTarget.src = '/arthasashtri.png';
                        }}
                      />
                    ) : (
                      <div className="text-5xl mb-4 group-hover:scale-125 transition-all duration-700 filter drop-shadow-2xl animate-float">
                        {feature.icon}
                      </div>
                    )}
                    {index === 1 ? (
                      <img 
                        src="https://fi.money/_next/image?url=https%3A%2F%2Fdza2kd7rioahk.cloudfront.net%2Fassets%2Fwealth-mcp%2Fwebp%2Ffi-mcp-getting-started.webp&w=1920&q=75" 
                        alt="Fi MCP" 
                        className="w-16 h-10 object-contain mx-auto opacity-60 group-hover:opacity-100 group-hover:scale-110 transition-all duration-700"
                        onError={(e) => {
                          e.currentTarget.src = '/arthasashtri.png';
                        }}
                      />
                    ) : index !== 1 && (
                      <img 
                        src={feature.logo} 
                        alt={feature.title} 
                        className="w-8 h-8 object-contain mx-auto opacity-60 group-hover:opacity-100 group-hover:scale-110 transition-all duration-700"
                        onError={(e) => {
                          e.currentTarget.src = '/arthasashtri.png';
                        }}
                      />
                    )}
                  </div>
                  
                  {/* Feature Content */}
                  <div className="text-center">
                    <h3 className="text-2xl font-bold text-white mb-4 group-hover:text-blue-300 transition-colors duration-500 whitespace-pre-line">
                      {feature.title}
                    </h3>
                    <p className="text-gray-300 leading-relaxed text-sm group-hover:text-gray-200 transition-colors duration-500">
                      {feature.desc}
                    </p>
                  </div>
                  
                  {/* Card Glow Effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400/5 to-indigo-400/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                  
                  {/* Floating Accent */}
                  <div className={`absolute -top-2 -right-2 w-4 h-4 bg-gradient-to-r ${index === 0 ? 'from-blue-400 to-cyan-400' : index === 1 ? 'from-indigo-400 to-purple-400' : 'from-purple-400 to-pink-400'} rounded-full opacity-60 animate-pulse`}></div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Premium Stats Section */}
        <div 
          className={`mt-20 transition-all duration-1500 delay-1200 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'}`}
        >
          <div className="flex justify-center space-x-16 text-center">
            {[
              { number: "1M+", label: "Active Users", color: "from-blue-400 via-cyan-400 to-teal-400", icon: "👥" },
              { number: "$100B+", label: "Assets Managed", color: "from-indigo-400 via-purple-400 to-pink-400", icon: "💰" },
              { number: "99.99%", label: "Uptime SLA", color: "from-purple-400 via-blue-400 to-indigo-400", icon: "⚡" }
            ].map((stat, index) => (
              <div key={index} className="group cursor-pointer relative transform-gpu hover:scale-110 transition-all duration-700">
                {/* Background Glow */}
                <div className={`absolute -inset-8 bg-gradient-to-r ${stat.color}/10 blur-2xl rounded-full opacity-0 group-hover:opacity-100 transition-all duration-700`}></div>
                
                {/* Icon */}
                <div className="text-4xl mb-3 opacity-80 group-hover:scale-125 transition-all duration-700 animate-float">
                  {stat.icon}
                </div>
                
                {/* Number */}
                <div className={`text-5xl font-black bg-gradient-to-r ${stat.color} bg-clip-text text-transparent group-hover:scale-125 transition-all duration-700 relative`}>
                  {stat.number}
                  <div className={`absolute inset-0 bg-gradient-to-r ${stat.color} blur-2xl opacity-0 group-hover:opacity-50 transition-opacity duration-700`}></div>
                </div>
                
                {/* Label */}
                <div className="text-gray-300 text-lg mt-3 group-hover:text-white transition-all duration-500 font-medium">{stat.label}</div>
                
                {/* Logo Watermark */}
                <img 
                  src="/arthasashtri.png" 
                  alt="Arthasashtri" 
                  className="w-4 h-4 object-contain mx-auto mt-2 opacity-30 group-hover:opacity-60 transition-all duration-700"
                />
              </div>
            ))}
          </div>
        </div>
      </div>


    </div>
  );
};

export default LandingPage;
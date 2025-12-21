/**
 * Home Component - Landing Page
 * Professional homepage with icons and smooth transitions
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FaMicrophone, 
  FaArrowRight,
  FaUserGraduate
} from 'react-icons/fa';
import { 
  MdSpellcheck, 
  MdAttachMoney,
  MdLanguage,
  MdSupportAgent
} from 'react-icons/md';

import './Home.css';

export function Home() {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const features = [
    {
      icon: FaMicrophone,
      title: 'Voice Conversations',
      description: 'Practice speaking with AI companions Pandu & Chandu in multiple languages',
      color: '#667eea'
    },
    {
      icon: MdSpellcheck,
      title: 'Grammar Guardian',
      description: 'Get instant corrections and improve your writing skills',
      color: '#f093fb'
    },
    {
      icon: MdLanguage,
      title: 'Multi-Language',
      description: 'Support for English, Kannada, Telugu, and more',
      color: '#4facfe'
    },
    {
      icon: MdAttachMoney,
      title: '100% Free',
      description: 'No subscriptions, no hidden costs, completely free forever',
      color: '#43e97b'
    }
  ];

  return (
    <div className="home-container">
      {/* Hero Section */}
      <header className={`hero-section ${isVisible ? 'visible' : ''}`}>
        <div className="hero-background">
          <div className="floating-shapes">
            <div className="shape shape-1"></div>
            <div className="shape shape-2"></div>
            <div className="shape shape-3"></div>
          </div>
        </div>

        <nav className="navbar">
          <div className="nav-content">
            <div className="home-logo-section">
              <img src="/assets/logos/logo-full.png" alt="KeLiva Logo" className="home-logo" />
              <div className="brand">
                <h1 className="brand-name">KeLiva</h1>
              </div>
            </div>
            <div className="nav-links">
              <a href="#features" className="nav-link">Features</a>
              <a href="#about" className="nav-link">About</a>
              <button onClick={() => navigate('/welcome')} className="cta-button">
                Get Started
                <FaArrowRight className="arrow" />
              </button>
            </div>
          </div>
        </nav>

        <div className="hero-content">
          <h1 className="hero-title">
            Learn English with
            <span className="gradient-text"> AI Tutors</span>
          </h1>
          <p className="hero-subtitle">
            Practice speaking, improve grammar, and chat naturally with Pandu & Chandu.
            Supports English, Kannada, and Telugu.
          </p>
          <div className="hero-buttons">
            <button onClick={() => navigate('/welcome')} className="primary-button">
              Start Learning
              <FaArrowRight className="sparkle" />
            </button>
          </div>
        </div>
      </header>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="section-header">
          <h2 className="section-title">What You Can Do</h2>
        </div>
        <div className="features-grid">
          {features.map((feature, index) => {
            const IconComponent = feature.icon;
            return (
              <div
                key={index}
                className="feature-card"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="feature-icon" style={{ background: feature.color }}>
                  <IconComponent />
                </div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="about-section">
        <div className="about-content">
          <div className="about-text">
            <h2 className="about-title">Your AI Tutors</h2>
            <p className="about-description">
              Choose between Pandu (male voice) or Chandu (female voice) for your learning sessions.
              Both understand English, Kannada, and Telugu.
            </p>
          </div>
          <div className="about-visual">
            <div className="tutor-card tutor-pandu">
              <div className="tutor-avatar">
                <FaUserGraduate />
              </div>
              <h3>Pandu</h3>
              <p>Male Voice</p>
            </div>
            <div className="tutor-card tutor-chandu">
              <div className="tutor-avatar">
                <MdSupportAgent />
              </div>
              <h3>Chandu</h3>
              <p>Female Voice</p>
            </div>
          </div>
        </div>
      </section>



      {/* Footer */}
      <footer className="home-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3>KeLiva</h3>
            <p>AI-powered language learning</p>
          </div>
          <div className="footer-links">
            <div className="footer-column">
              <h4>Quick Links</h4>
              <a href="#features">Features</a>
              <a href="#about">Tutors</a>
              <a href="/welcome">Launch App</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2024 KeLiva • Built with Groq API & Web Speech API</p>
        </div>
      </footer>
    </div>
  );
}

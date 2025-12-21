/**
 * Welcome Component
 * Secret name authentication before accessing dashboard
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowRight, FaUserCircle, FaTimesCircle } from 'react-icons/fa';
import { HiSparkles } from 'react-icons/hi';
import { isNameAllowed } from '../config/allowedUsers';
import './Welcome.css';

export function Welcome() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [isAnimating, setIsAnimating] = useState(false);
  const [isRejected, setIsRejected] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      // Check if name is in allowed list
      if (isNameAllowed(name)) {
        // Access granted
        localStorage.setItem('keliva_user_name', name.trim());
        localStorage.setItem('keliva_authenticated', 'true');
        
        // Animate and navigate
        setIsAnimating(true);
        setTimeout(() => {
          navigate('/app');
        }, 600);
      } else {
        // Access denied
        setIsRejected(true);
        setError('Sorry, you are not my friend. Access denied! 👋');
        
        // Close after 3 seconds
        setTimeout(() => {
          window.close();
          // If window.close() doesn't work (browser security), redirect to home
          setTimeout(() => {
            navigate('/');
          }, 500);
        }, 3000);
      }
    }
  };

  return (
    <div className={`welcome-container ${isAnimating ? 'exit' : ''} ${isRejected ? 'rejected' : ''}`}>
      <div className="welcome-background">
        <div className="floating-shape shape-1"></div>
        <div className="floating-shape shape-2"></div>
        <div className="floating-shape shape-3"></div>
      </div>

      {!isRejected ? (
        <div className="welcome-content">
          <div className="welcome-logo">
            <img src="/assets/logos/logo-full.png" alt="KeLiva" className="logo-image" />
          </div>

          <h1 className="welcome-title">
            Welcome to <span className="gradient-text">KeLiva</span>
          </h1>
          
          <p className="welcome-subtitle">
            Your AI-powered language learning companion
          </p>

          <form onSubmit={handleSubmit} className="name-form">
            <div className="input-group">
              <FaUserCircle className="input-icon" />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
                className="name-input"
                autoFocus
                maxLength={50}
              />
            </div>

            <button 
              type="submit" 
              className="start-button"
              disabled={!name.trim()}
            >
              <span>Start Learning</span>
              <HiSparkles className="button-icon" />
              <FaArrowRight className="arrow-icon" />
            </button>
          </form>

          <div className="welcome-features">
            <div className="feature-badge">
              <span className="badge-icon">🎤</span>
              <span>Voice Practice</span>
            </div>
            <div className="feature-badge">
              <span className="badge-icon">✍️</span>
              <span>Grammar Check</span>
            </div>
            <div className="feature-badge">
              <span className="badge-icon">🌍</span>
              <span>Multi-Language</span>
            </div>
          </div>

          <p className="welcome-note">
            No signup required • Completely free
          </p>
        </div>
      ) : (
        <div className="rejection-content">
          <div className="rejection-icon">
            <FaTimesCircle />
          </div>
          <h1 className="rejection-title">Access Denied</h1>
          <p className="rejection-message">{error}</p>
          <p className="rejection-note">Redirecting...</p>
        </div>
      )}
    </div>
  );
}

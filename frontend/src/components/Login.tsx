/**
 * Login Component
 * JWT-based authentication for advanced features
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowRight, FaUserCircle, FaLock, FaEye, FaEyeSlash, FaSpinner, FaEnvelope } from 'react-icons/fa';
import { HiSparkles } from 'react-icons/hi';
import './Login.css';

interface LoginResponse {
  message: string;
  user: {
    id: string;
    username: string;
    email: string;
    full_name: string;
  };
  token: string;
}

interface RegisterResponse {
  message: string;
  user: {
    id: string;
    username: string;
    email: string;
    full_name: string;
  };
  token: string;
}

export function Login() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form data
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: ''
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });

      const data: LoginResponse = await response.json();

      if (response.ok) {
        // Store authentication data
        localStorage.setItem('keliva_token', data.token);
        localStorage.setItem('keliva_user', JSON.stringify(data.user));
        localStorage.setItem('keliva_authenticated', 'true');

        setSuccess('Login successful! Redirecting...');
        setTimeout(() => {
          navigate('/app');
        }, 1000);
      } else {
        setError(data.message || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Basic validation
    if (!formData.email.includes('@')) {
      setError('Please enter a valid email address');
      setIsLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      setIsLoading(false);
      return;
    }

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const data: RegisterResponse = await response.json();

      if (response.ok) {
        // Store authentication data
        localStorage.setItem('keliva_token', data.token);
        localStorage.setItem('keliva_user', JSON.stringify(data.user));
        localStorage.setItem('keliva_authenticated', 'true');

        setSuccess('Registration successful! Redirecting...');
        setTimeout(() => {
          navigate('/app');
        }, 1000);
      } else {
        setError(data.message || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuestAccess = () => {
    // Allow guest access with limited features
    localStorage.setItem('keliva_guest', 'true');
    localStorage.setItem('keliva_authenticated', 'true');
    navigate('/app');
  };

  return (
    <div className="login-container">
      <div className="login-background">
        <div className="floating-shape shape-1"></div>
        <div className="floating-shape shape-2"></div>
        <div className="floating-shape shape-3"></div>
      </div>

      <div className="login-content">
        <div className="login-logo">
          <img src="/assets/logos/logo-full.png" alt="KeLiva" className="logo-image" />
        </div>

        <h1 className="login-title">
          Welcome to <span className="gradient-text">KeLiva</span>
        </h1>
        
        <p className="login-subtitle">
          {isLogin ? 'Sign in to access advanced features' : 'Create your account to get started'}
        </p>

        <div className="auth-tabs">
          <button 
            className={`tab-button ${isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(true)}
          >
            Login
          </button>
          <button 
            className={`tab-button ${!isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(false)}
          >
            Register
          </button>
        </div>

        <form onSubmit={isLogin ? handleLogin : handleRegister} className="auth-form">
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <div className="input-group">
            <FaEnvelope className="input-icon" />
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Email address"
              className="auth-input"
              required
              autoFocus
            />
          </div>

          {!isLogin && (
            <>
              <div className="input-group">
                <FaUserCircle className="input-icon" />
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  placeholder="Username"
                  className="auth-input"
                  required
                />
              </div>

              <div className="input-group">
                <FaUserCircle className="input-icon" />
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  placeholder="Full name"
                  className="auth-input"
                  required
                />
              </div>
            </>
          )}

          <div className="input-group">
            <FaLock className="input-icon" />
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="Password"
              className="auth-input"
              required
              minLength={6}
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <FaEyeSlash /> : <FaEye />}
            </button>
          </div>

          <button 
            type="submit" 
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <FaSpinner className="spinner" />
                <span>{isLogin ? 'Signing in...' : 'Creating account...'}</span>
              </>
            ) : (
              <>
                <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                <HiSparkles className="button-icon" />
                <FaArrowRight className="arrow-icon" />
              </>
            )}
          </button>
        </form>

        <div className="auth-divider">
          <span>or</span>
        </div>

        <button onClick={handleGuestAccess} className="guest-button">
          Continue as Guest
          <span className="guest-note">(Limited features)</span>
        </button>

        <div className="feature-preview">
          <h3>Advanced Features Include:</h3>
          <div className="feature-grid">
            <div className="feature-item">
              <span className="feature-icon">👨‍👩‍👧‍👦</span>
              <span>Family Learning Groups</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🎭</span>
              <span>Emotion Recognition AI</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🎤</span>
              <span>Voice Biometric Tracking</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">💭</span>
              <span>Dream Journal Integration</span>
            </div>
          </div>
        </div>

        <p className="auth-note">
          Your data is secure and private • No spam, ever
        </p>
      </div>
    </div>
  );
}
/**
 * Dashboard Component
 * Main layout for the Study Room interface
 * Provides navigation and container for all features
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { GrammarEditor } from './GrammarEditor';
import { VoiceCall } from './VoiceCall';
import { LoadingSpinner } from './LoadingSpinner';
import { useUser } from '../contexts/UserContext';
import { useConversation } from '../contexts/ConversationContext';
import { useToast } from '../contexts/ToastContext';
import { MdSpellcheck, MdAttachMoney, MdClose } from 'react-icons/md';
import { FaMicrophone, FaSignOutAlt, FaUser, FaCog, FaChevronDown, FaGlobe, FaBell, FaMoon, FaSun, FaEdit, FaSave } from 'react-icons/fa';
import './Dashboard.css';

type ActiveView = 'grammar' | 'voice';
type ModalType = 'profile' | 'settings' | null;

interface StoredUser {
  id: string;
  username: string;
  email: string;
  full_name: string;
}

export function Dashboard() {
  const [activeView, setActiveView] = useState<ActiveView>('grammar');
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({ full_name: '', email: '' });
  const [settings, setSettings] = useState({
    language: 'en',
    notifications: true,
    darkMode: true,
    voiceSpeed: 1.0
  });
  const { user, isLoading: userLoading } = useUser();
  const { startConversation } = useConversation();
  const { showError } = useToast();
  const navigate = useNavigate();
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Get stored user info from login
  const storedUser: StoredUser | null = (() => {
    try {
      const data = localStorage.getItem('keliva_user');
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  })();

  const isGuest = localStorage.getItem('keliva_guest') === 'true';
  const displayName = storedUser?.username || storedUser?.full_name || (isGuest ? 'Guest' : user?.sessionId?.slice(0, 8) || 'User');

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowProfileDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('keliva_token');
    localStorage.removeItem('keliva_user');
    localStorage.removeItem('keliva_authenticated');
    localStorage.removeItem('keliva_guest');
    localStorage.removeItem('keliva_user_name');
    navigate('/login');
  };

  const openProfile = () => {
    setProfileForm({
      full_name: storedUser?.full_name || '',
      email: storedUser?.email || ''
    });
    setActiveModal('profile');
    setShowProfileDropdown(false);
  };

  const openSettings = () => {
    setActiveModal('settings');
    setShowProfileDropdown(false);
  };

  const saveProfile = () => {
    if (storedUser) {
      const updatedUser = { ...storedUser, ...profileForm };
      localStorage.setItem('keliva_user', JSON.stringify(updatedUser));
    }
    setEditingProfile(false);
  };

  const saveSettings = () => {
    localStorage.setItem('keliva_settings', JSON.stringify(settings));
    setActiveModal(null);
  };

  // Start a conversation when user is loaded
  useEffect(() => {
    if (user && !userLoading) {
      try {
        startConversation(user.id, 'web');
      } catch (error) {
        showError('Failed to start conversation. Please refresh the page.');
      }
    }
  }, [user, userLoading, startConversation, showError]);

  // Show loading state while user is being initialized
  if (userLoading) {
    return (
      <div className="dashboard">
        <LoadingSpinner size="large" message="Initializing KeLiva..." fullScreen />
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Professional Header */}
      <header className="dashboard-header">
        <div className="header-container">
          <div className="header-left">
            <div className="logo-section">
              <img src="/assets/logos/logo-full.png" alt="KeLiva" className="header-logo" />
              <div className="brand-info">
                <h1 className="app-title">KeLiva</h1>
                <p className="app-tagline">AI Language Learning</p>
              </div>
            </div>
          </div>
          
          <div className="header-right">
            <div className="profile-section" ref={dropdownRef}>
              <button 
                className="profile-trigger"
                onClick={() => setShowProfileDropdown(!showProfileDropdown)}
              >
                <div className="user-avatar">
                  <span>{displayName.charAt(0).toUpperCase()}</span>
                </div>
                <div className="user-details">
                  <span className="user-label">{isGuest ? 'Guest Mode' : 'Welcome'}</span>
                  <span className="user-id">{displayName}</span>
                </div>
                <FaChevronDown className={`dropdown-arrow ${showProfileDropdown ? 'open' : ''}`} />
              </button>

              {showProfileDropdown && (
                <div className="profile-dropdown">
                  <div className="dropdown-header">
                    <div className="dropdown-avatar">
                      <span>{displayName.charAt(0).toUpperCase()}</span>
                    </div>
                    <div className="dropdown-info">
                      <span className="dropdown-name">{displayName}</span>
                      {storedUser?.email && <span className="dropdown-email">{storedUser.email}</span>}
                      {isGuest && <span className="dropdown-guest-badge">Guest Account</span>}
                    </div>
                  </div>
                  <div className="dropdown-divider"></div>
                  <button className="dropdown-item" onClick={openProfile}>
                    <FaUser />
                    <span>Profile</span>
                  </button>
                  <button className="dropdown-item" onClick={openSettings}>
                    <FaCog />
                    <span>Settings</span>
                  </button>
                  <div className="dropdown-divider"></div>
                  <button className="dropdown-item logout" onClick={handleLogout}>
                    <FaSignOutAlt />
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Modern Navigation Tabs */}
      <nav className="dashboard-nav">
        <div className="nav-container">
          <div className="nav-tabs">
            <button
              className={`nav-tab ${activeView === 'grammar' ? 'active' : ''}`}
              onClick={() => setActiveView('grammar')}
            >
              <MdSpellcheck className="nav-icon" />
              <span className="nav-label">Grammar Check</span>
              {activeView === 'grammar' && <div className="active-indicator"></div>}
            </button>
            <button
              className={`nav-tab ${activeView === 'voice' ? 'active' : ''}`}
              onClick={() => setActiveView('voice')}
            >
              <FaMicrophone className="nav-icon" />
              <span className="nav-label">Voice Practice</span>
              {activeView === 'voice' && <div className="active-indicator"></div>}
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content with Animation */}
      <main className="dashboard-main">
        <div className="content-wrapper">
          <div className={`view-container ${activeView}`}>
            {activeView === 'grammar' && <GrammarEditor />}
            {activeView === 'voice' && <VoiceCall />}
          </div>
        </div>
      </main>

      {/* Modern Footer */}
      <footer className="dashboard-footer">
        <div className="footer-container">
          <div className="footer-left">
            <MdAttachMoney className="footer-icon" />
            <span>100% Free</span>
          </div>
          <div className="footer-center">
            <span>Powered by Groq API • Web Speech API</span>
          </div>
          <div className="footer-right">
            <span>© 2024 KeLiva</span>
          </div>
        </div>
      </footer>

      {/* Profile Modal */}
      {activeModal === 'profile' && (
        <div className="modal-overlay" onClick={() => setActiveModal(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Profile</h2>
              <button className="modal-close" onClick={() => setActiveModal(null)}>
                <MdClose />
              </button>
            </div>
            <div className="modal-body">
              <div className="profile-avatar-large">
                <span>{displayName.charAt(0).toUpperCase()}</span>
              </div>
              
              {isGuest ? (
                <div className="guest-notice">
                  <p>You're using a guest account. Create an account to save your progress!</p>
                  <button className="btn-primary" onClick={() => navigate('/login')}>
                    Create Account
                  </button>
                </div>
              ) : (
                <div className="profile-form">
                  <div className="form-group">
                    <label>Full Name</label>
                    {editingProfile ? (
                      <input
                        type="text"
                        value={profileForm.full_name}
                        onChange={e => setProfileForm({...profileForm, full_name: e.target.value})}
                      />
                    ) : (
                      <p>{storedUser?.full_name || 'Not set'}</p>
                    )}
                  </div>
                  <div className="form-group">
                    <label>Email</label>
                    {editingProfile ? (
                      <input
                        type="email"
                        value={profileForm.email}
                        onChange={e => setProfileForm({...profileForm, email: e.target.value})}
                      />
                    ) : (
                      <p>{storedUser?.email || 'Not set'}</p>
                    )}
                  </div>
                  <div className="form-group">
                    <label>Username</label>
                    <p>{storedUser?.username || 'Not set'}</p>
                  </div>
                  <div className="profile-actions">
                    {editingProfile ? (
                      <>
                        <button className="btn-secondary" onClick={() => setEditingProfile(false)}>Cancel</button>
                        <button className="btn-primary" onClick={saveProfile}><FaSave /> Save</button>
                      </>
                    ) : (
                      <button className="btn-primary" onClick={() => setEditingProfile(true)}><FaEdit /> Edit Profile</button>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {activeModal === 'settings' && (
        <div className="modal-overlay" onClick={() => setActiveModal(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Settings</h2>
              <button className="modal-close" onClick={() => setActiveModal(null)}>
                <MdClose />
              </button>
            </div>
            <div className="modal-body">
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <FaGlobe />
                    <div>
                      <span className="setting-label">Language</span>
                      <span className="setting-desc">Choose your preferred language</span>
                    </div>
                  </div>
                  <select 
                    value={settings.language} 
                    onChange={e => setSettings({...settings, language: e.target.value})}
                  >
                    <option value="en">English</option>
                    <option value="te">Telugu</option>
                    <option value="hi">Hindi</option>
                  </select>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <FaBell />
                    <div>
                      <span className="setting-label">Notifications</span>
                      <span className="setting-desc">Enable push notifications</span>
                    </div>
                  </div>
                  <label className="toggle">
                    <input 
                      type="checkbox" 
                      checked={settings.notifications}
                      onChange={e => setSettings({...settings, notifications: e.target.checked})}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    {settings.darkMode ? <FaMoon /> : <FaSun />}
                    <div>
                      <span className="setting-label">Dark Mode</span>
                      <span className="setting-desc">Toggle dark/light theme</span>
                    </div>
                  </div>
                  <label className="toggle">
                    <input 
                      type="checkbox" 
                      checked={settings.darkMode}
                      onChange={e => setSettings({...settings, darkMode: e.target.checked})}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <FaMicrophone />
                    <div>
                      <span className="setting-label">Voice Speed</span>
                      <span className="setting-desc">Adjust AI voice speed</span>
                    </div>
                  </div>
                  <input 
                    type="range" 
                    min="0.5" 
                    max="2" 
                    step="0.1"
                    value={settings.voiceSpeed}
                    onChange={e => setSettings({...settings, voiceSpeed: parseFloat(e.target.value)})}
                  />
                  <span className="range-value">{settings.voiceSpeed}x</span>
                </div>
              </div>

              <div className="settings-actions">
                <button className="btn-primary" onClick={saveSettings}>Save Settings</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

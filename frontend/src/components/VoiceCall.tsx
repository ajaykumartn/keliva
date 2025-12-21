/**
 * VoiceCall Component
 * Real-time voice conversation with call controls and transcription display
 */

import { useState } from 'react';
import { useVoiceChat } from '../hooks/useVoiceChat';
import { AudioVisualizer } from './AudioVisualizer';
import { PhotoAvatar } from './PhotoAvatar';
import { useToast } from '../contexts/ToastContext';
import { useOnlineStatus } from '../hooks/useOnlineStatus';
import { 
  FaMicrophone, 
  FaPhone, 
  FaPhoneSlash, 
  FaStop,
  FaComments 
} from 'react-icons/fa';
import { MdSpellcheck } from 'react-icons/md';

import './VoiceCall.css';

type ConversationMode = 'grammar' | 'general';
type Assistant = 'pandu' | 'chandu';

export function VoiceCall() {
  const { showError, showSuccess } = useToast();
  const isOnline = useOnlineStatus();
  const [mode, setMode] = useState<ConversationMode>('general');
  const [assistant, setAssistant] = useState<Assistant>('pandu');
  
  const {
    isConnected,
    isListening,
    messages,
    audioStream,
    startListening,
    stopListening,
    connect,
    disconnect,
    error,
    setConversationMode,
    setVoiceGender
  } = useVoiceChat({
    wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/voice/stream',
    language: 'en-US'
  });

  // Update voice gender when assistant changes
  const handleAssistantChange = (newAssistant: Assistant) => {
    setAssistant(newAssistant);
    const gender = newAssistant === 'pandu' ? 'male' : 'female';
    console.log(`🎭 Assistant changed to ${newAssistant} (${gender})`);
    
    if (setVoiceGender) {
      setVoiceGender(gender);
      console.log(`🎤 Voice gender set to: ${gender}`);
    } else {
      console.error('❌ setVoiceGender function not available');
    }
  };

  // Update conversation mode when mode changes
  const handleModeChange = (newMode: ConversationMode) => {
    setMode(newMode);
    if (setConversationMode) {
      setConversationMode(newMode === 'grammar');
    }
  };

  const handleConnect = async () => {
    if (!isOnline) {
      showError('You are offline. Please check your internet connection.');
      return;
    }
    
    try {
      await connect();
      showSuccess('Connected to voice call');
    } catch (err) {
      showError('Failed to connect. Please try again.');
    }
  };

  const handleDisconnect = () => {
    disconnect();
    showSuccess('Call ended');
  };

  const handleStartListening = async () => {
    try {
      await startListening();
    } catch (err) {
      showError('Failed to access microphone. Please check permissions.');
    }
  };

  return (
    <div className="voice-call">
      <div className="call-header">
        <h2>Voice Call with {assistant === 'pandu' ? 'Pandu' : 'Chandu'}</h2>
        <p className="call-description">
          Have a natural conversation in English, Kannada, or Telugu
        </p>
      </div>

      {/* Photo Avatar with Voice Waves - Click to flip */}
      <PhotoAvatar 
        gender={assistant === 'pandu' ? 'male' : 'female'}
        isSpeaking={isListening}
        name={assistant === 'pandu' ? 'Pandu' : 'Chandu'}
        onFlip={() => handleAssistantChange(assistant === 'pandu' ? 'chandu' : 'pandu')}
      />

      {/* Mode Selection */}
      <div className="mode-selector">
        <button
          className={`mode-btn ${mode === 'grammar' ? 'active' : ''}`}
          onClick={() => handleModeChange('grammar')}
        >
          <MdSpellcheck className="mode-icon" />
          <span className="mode-text">Grammar Check</span>
        </button>
        <button
          className={`mode-btn ${mode === 'general' ? 'active' : ''}`}
          onClick={() => handleModeChange('general')}
        >
          <FaComments className="mode-icon" />
          <span className="mode-text">General Talk</span>
        </button>
      </div>

      {/* Connection Status Bar */}
      <div className="status-bar">
        <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot"></span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
        {isListening && (
          <div className="status-badge listening">
            <span className="status-dot pulse"></span>
            Listening...
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
        </div>
      )}

      {/* Audio Visualizer */}
      {isConnected && (
        <AudioVisualizer 
          isActive={isListening} 
          audioStream={audioStream}
        />
      )}

      {/* Call Controls */}
      <div className="call-controls">
        {!isConnected ? (
          <button onClick={handleConnect} className="control-btn connect-btn" disabled={!isOnline}>
            <FaPhone className="btn-icon" />
            <span className="btn-text">{isOnline ? 'Start Call' : 'Offline'}</span>
          </button>
        ) : (
          <>
            <button onClick={handleDisconnect} className="control-btn disconnect-btn">
              <FaPhoneSlash className="btn-icon" />
              <span className="btn-text">End Call</span>
            </button>

            {!isListening ? (
              <button onClick={handleStartListening} className="control-btn speak-btn">
                <FaMicrophone className="btn-icon" />
                <span className="btn-text">Start Speaking</span>
              </button>
            ) : (
              <button onClick={stopListening} className="control-btn mute-btn">
                <FaStop className="btn-icon" />
                <span className="btn-text">Stop Speaking</span>
              </button>
            )}
          </>
        )}
      </div>

      {/* Transcription Display */}
      <div className="transcription-container">
        <div className="transcription-header">
          <h3>Conversation Transcript</h3>
          <span className="message-count">{messages.length} messages</span>
        </div>

        <div className="transcription-content">
          {messages.length === 0 ? (
            <div className="empty-state">
              <FaComments className="empty-icon" />
              <p>No messages yet</p>
              <p className="empty-hint">
                {isConnected 
                  ? 'Click "Start Speaking" to begin the conversation'
                  : 'Click "Start Call" to connect'}
              </p>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message, index) => (
                <div key={index} className={`message message-${message.type}`}>
                  <div className="message-avatar">
                    {message.type === 'user' ? '👤' : 
                     message.type === 'assistant' ? '🤖' : '⚙️'}
                  </div>
                  <div className="message-content">
                    <div className="message-meta">
                      <span className="message-sender">
                        {message.type === 'user' ? 'You' : 
                         message.type === 'assistant' ? 'Captain' : 
                         'System'}
                      </span>
                      <span className="message-time">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="message-text">{message.text}</div>
                    {message.confidence !== undefined && message.confidence < 0.8 && (
                      <div className="message-confidence">
                        Confidence: {(message.confidence * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="call-instructions">
        <h4>📋 How to use:</h4>
        <ol>
          <li>Click "Start Call" to establish connection</li>
          <li>Click "Start Speaking" and speak clearly into your microphone</li>
          <li>Your speech will be transcribed in real-time</li>
          <li>Captain will respond with voice and text</li>
          <li>Switch languages naturally - Captain will adapt!</li>
        </ol>
      </div>
    </div>
  );
}

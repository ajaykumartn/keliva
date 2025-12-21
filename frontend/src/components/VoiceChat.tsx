/**
 * VoiceChat Component
 * Demonstrates Web Speech API integration with WebSocket
 */

import { useVoiceChat } from '../hooks/useVoiceChat';
import './VoiceChat.css';

export function VoiceChat() {
  const {
    isConnected,
    isListening,
    messages,
    startListening,
    stopListening,
    connect,
    disconnect,
    error
  } = useVoiceChat({
    wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/voice/stream',
    language: 'en-US'
  });

  return (
    <div className="voice-chat">
      <h2>Voice Chat</h2>
      
      {/* Connection Status */}
      <div className="status-bar">
        <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </div>
        <div className={`status-indicator ${isListening ? 'listening' : ''}`}>
          {isListening ? '🎤 Listening...' : '🎤 Not Listening'}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {/* Controls */}
      <div className="controls">
        {!isConnected ? (
          <button onClick={connect} className="btn btn-primary">
            Connect
          </button>
        ) : (
          <button onClick={disconnect} className="btn btn-secondary">
            Disconnect
          </button>
        )}

        {isConnected && !isListening && (
          <button onClick={startListening} className="btn btn-success">
            Start Speaking
          </button>
        )}

        {isConnected && isListening && (
          <button onClick={stopListening} className="btn btn-danger">
            Stop Speaking
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="messages">
        <h3>Conversation</h3>
        {messages.length === 0 ? (
          <p className="no-messages">No messages yet. Start speaking to begin!</p>
        ) : (
          <div className="message-list">
            {messages.map((message, index) => (
              <div key={index} className={`message message-${message.type}`}>
                <div className="message-header">
                  <span className="message-type">
                    {message.type === 'user' ? '👤 You' : 
                     message.type === 'assistant' ? '🤖 Captain' : 
                     '⚙️ System'}
                  </span>
                  <span className="message-time">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="message-text">{message.text}</div>
                {message.confidence !== undefined && (
                  <div className="message-confidence">
                    Confidence: {(message.confidence * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="instructions">
        <h4>How to use:</h4>
        <ol>
          <li>Click "Connect" to establish WebSocket connection</li>
          <li>Click "Start Speaking" to begin voice recognition</li>
          <li>Speak clearly into your microphone</li>
          <li>Your speech will be transcribed and sent to the backend</li>
          <li>If confidence is low (&lt; 60%), you'll be asked to repeat</li>
        </ol>
      </div>
    </div>
  );
}

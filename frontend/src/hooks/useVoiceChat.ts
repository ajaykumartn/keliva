/**
 * useVoiceChat Hook
 * Integrates Web Speech API with WebSocket for real-time voice conversations
 * 
 * Features:
 * - Browser-based speech recognition (FREE)
 * - WebSocket communication with backend
 * - Confidence score checking
 * - Low-confidence handling
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { webSpeechService, TranscriptionResult } from '../services/webSpeechService';

export interface VoiceChatMessage {
  type: 'user' | 'assistant' | 'system';
  text: string;
  confidence?: number;
  timestamp: Date;
}

export interface UseVoiceChatOptions {
  wsUrl?: string;
  language?: string;
  onMessage?: (message: VoiceChatMessage) => void;
  onError?: (error: string) => void;
}

export interface UseVoiceChatReturn {
  isConnected: boolean;
  isListening: boolean;
  messages: VoiceChatMessage[];
  audioStream: MediaStream | null;
  startListening: () => void;
  stopListening: () => void;
  connect: () => void;
  disconnect: () => void;
  error: string | null;
  setConversationMode?: (isGrammarMode: boolean) => void;
  setVoiceGender?: (gender: 'male' | 'female') => void;
}

export function useVoiceChat(options: UseVoiceChatOptions = {}): UseVoiceChatReturn {
  const {
    language = 'en-US',
    onMessage,
    onError
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState<VoiceChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
  const [, setVoicesLoaded] = useState(false);
  const [, setIsGrammarMode] = useState(false);
  const [voiceGender, setVoiceGender] = useState<'male' | 'female'>('male');
  const voiceGenderRef = useRef<'male' | 'female'>('male');
  const reconnectTimeoutRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef<boolean>(false);
  const shouldReconnectRef = useRef<boolean>(true);
  const isMountedRef = useRef<boolean>(true);
  const audioStreamRef = useRef<MediaStream | null>(null);

  /**
   * Add a message to the chat
   */
  const addMessage = useCallback((message: VoiceChatMessage) => {
    setMessages(prev => [...prev, message]);
    if (onMessage) {
      onMessage(message);
    }
  }, [onMessage]);

  /**
   * Handle error
   */
  const handleError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    if (onError) {
      onError(errorMessage);
    }
  }, [onError]);

  /**
   * Play next audio chunk from queue
   */
  const playNextAudioChunk = useCallback(() => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      return;
    }

    const audioContext = audioContextRef.current;
    if (!audioContext) return;

    isPlayingRef.current = true;
    const audioBuffer = audioQueueRef.current.shift()!;
    
    // Create source and play
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    
    // Play next chunk when this one ends
    source.onended = () => {
      playNextAudioChunk();
    };
    
    source.start(0);
  }, []);

  /**
   * Connect (simplified for HTTP-based communication)
   */
  const connect = useCallback(() => {
    // For HTTP-based voice chat, we don't need a persistent connection
    // Just mark as connected to enable voice functionality
    console.log('Voice chat ready (HTTP mode)');
    setIsConnected(true);
    setError(null);
  }, []);

  /**
   * Disconnect (simplified for HTTP-based communication)
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsConnected(false);
  }, []);

  /**
   * Send transcription to backend via HTTP
   */
  const sendTranscription = useCallback(async (result: TranscriptionResult) => {
    // Only send final results to reduce noise
    if (!result.isFinal) {
      return;
    }

    // Add user message to chat immediately
    addMessage({
      type: 'user',
      text: result.text,
      confidence: result.confidence,
      timestamp: new Date()
    });

    try {
      // Send to chat conversation API (correct endpoint)
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/chat/conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: result.text,
          user_name: 'Voice User',
          session_id: `voice_${Date.now()}`,
          mode: 'chat'
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Add AI response to chat
        addMessage({
          type: 'assistant',
          text: data.response,
          timestamp: new Date()
        });
        
        // Use the updated webSpeechService to speak the response with gender preference
        const language = data.language || 'en';
        const currentGender = voiceGenderRef.current; // Use ref to get current gender
        console.log(`🎤 Speaking AI response with gender: ${currentGender}, language: ${language}`);
        console.log(`📝 AI Response text: "${data.response}"`);
        console.log(`🔍 Current voiceGender state: ${voiceGender}, ref: ${voiceGenderRef.current}`);
        await webSpeechService.speakAIResponse(data.response, language, currentGender);
        
      } else {
        console.error('Failed to get AI response:', response.status);
        addMessage({
          type: 'system',
          text: 'Sorry, I had trouble processing that. Please try again.',
          timestamp: new Date()
        });
      }
    } catch (error) {
      console.error('Error sending transcription:', error);
      addMessage({
        type: 'system',
        text: 'Connection error. Please check your internet connection.',
        timestamp: new Date()
      });
    }
  }, [addMessage, voiceGender]);

  /**
   * Start listening for speech
   */
  const startListening = useCallback(async () => {
    if (!webSpeechService.isSupported()) {
      handleError('Web Speech API is not supported in this browser');
      return;
    }

    try {
      // Request microphone access and get audio stream for visualization
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
      setAudioStream(stream);

      // Always re-initialize to ensure recognition object exists
      // This handles cases where cleanup() was called
      webSpeechService.initialize({
        language: language,
        continuous: true,
        interimResults: true
      });

      // Set up callbacks
      webSpeechService.onTranscription(sendTranscription);
      webSpeechService.onError(handleError);

      webSpeechService.start();
      setIsListening(true);
      setError(null);
    } catch (err) {
      console.error('Error starting speech recognition:', err);
      handleError('Failed to start speech recognition. Please allow microphone access.');
    }
  }, [language, sendTranscription, handleError]);

  /**
   * Stop listening for speech
   */
  const stopListening = useCallback(() => {
    try {
      webSpeechService.stop();
      
      // Stop audio stream
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
        setAudioStream(null);
      }
      
      setIsListening(false);
    } catch (err) {
      console.error('Error stopping speech recognition:', err);
    }
  }, []);

  /**
   * Load speech synthesis voices
   */
  useEffect(() => {
    if ('speechSynthesis' in window) {
      // Load voices
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
          setVoicesLoaded(true);
          console.log('Available voices:', voices.map(v => `${v.name} (${v.lang})`));
        }
      };
      
      // Voices might load asynchronously
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    isMountedRef.current = true;
    
    return () => {
      isMountedRef.current = false;
      shouldReconnectRef.current = false;
      
      // Clear reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      
      // Stop speech recognition
      try {
        webSpeechService.stop();
      } catch (e) {
        // Ignore errors during cleanup
      }
      
      // Stop audio stream
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
      }
      
      // Clean up audio context
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      
      // Clear audio queue
      audioQueueRef.current = [];
      isPlayingRef.current = false;
      
      // Cleanup speech service
      webSpeechService.cleanup();
    };
  }, []);

  /**
   * Update conversation mode
   */
  const updateConversationMode = useCallback((isGrammar: boolean) => {
    setIsGrammarMode(isGrammar);
    console.log('Conversation mode updated:', isGrammar ? 'Grammar' : 'General');
  }, []);

  /**
   * Update voice gender
   */
  const updateVoiceGender = useCallback((gender: 'male' | 'female') => {
    console.log(`🎭 useVoiceChat: Updating voice gender to ${gender}`);
    setVoiceGender(gender);
    voiceGenderRef.current = gender; // Update ref to avoid stale closure
    console.log(`✅ useVoiceChat: Voice gender state updated to ${gender}`);
  }, []);

  return {
    isConnected,
    isListening,
    messages,
    audioStream,
    startListening,
    stopListening,
    connect,
    disconnect,
    error,
    setConversationMode: updateConversationMode,
    setVoiceGender: updateVoiceGender
  };
}

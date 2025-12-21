/**
 * Web Speech API Service
 * Provides browser-based speech-to-text AND text-to-speech functionality (100% FREE)
 * 
 * Requirements:
 * - 11.1: Use Web Speech API for robust multi-language support
 * - 11.3: Handle code-mixed speech
 * - 11.4: Provide proper word boundaries and punctuation
 * - 11.5: Check confidence scores and handle low-confidence
 * - TTS: Provide text-to-speech for AI responses
 */

export interface TranscriptionResult {
  text: string;
  confidence: number;
  language: string;
  isFinal: boolean;
}

export interface WebSpeechConfig {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
}

export interface TTSConfig {
  voice?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
  language?: string;
  gender?: 'male' | 'female';
}

export interface TTSResult {
  success: boolean;
  error?: string;
}

export class WebSpeechService {
  private recognition: SpeechRecognition | null = null;
  private synthesis: SpeechSynthesis;
  private voices: SpeechSynthesisVoice[] = [];
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private isListening: boolean = false;
  private isSpeaking: boolean = false;
  private onTranscriptionCallback: ((result: TranscriptionResult) => void) | null = null;
  private onErrorCallback: ((error: string) => void) | null = null;

  constructor() {
    // Initialize synthesis
    this.synthesis = window.speechSynthesis;
    
    // Load voices
    this.loadVoices();
    
    // Load voices when they become available
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = () => this.loadVoices();
    }
    
    // Check if Web Speech API is supported
    if (!this.isSupported()) {
      console.error('Web Speech API is not supported in this browser');
    }
  }

  /**
   * Check if Web Speech API is supported in the current browser
   */
  isSupported(): boolean {
    const sttSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    const ttsSupported = 'speechSynthesis' in window;
    return sttSupported && ttsSupported;
  }

  /**
   * Check if Text-to-Speech is supported
   */
  isTTSSupported(): boolean {
    return 'speechSynthesis' in window;
  }

  /**
   * Load available voices for TTS
   */
  private loadVoices(): void {
    this.voices = this.synthesis.getVoices();
    console.log('Available voices:', this.voices.map(v => `${v.name} (${v.lang})`));
  }

  /**
   * Initialize speech recognition with configuration
   */
  initialize(config: WebSpeechConfig = {}): void {
    if (!this.isSupported()) {
      throw new Error('Web Speech API is not supported in this browser');
    }

    // Create recognition instance
    const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    this.recognition = new SpeechRecognitionAPI();

    // Configure recognition
    if (this.recognition) {
      this.recognition.continuous = config.continuous ?? true;
      this.recognition.interimResults = config.interimResults ?? true;
      this.recognition.maxAlternatives = config.maxAlternatives ?? 1;
      this.recognition.lang = config.language ?? 'en-US';
    }

    // Set up event handlers
    this.setupEventHandlers();
  }

  /**
   * Set up event handlers for speech recognition
   */
  private setupEventHandlers(): void {
    if (!this.recognition) return;

    // Handle results
    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      const results = event.results;
      const lastResult = results[results.length - 1];
      
      if (lastResult) {
        const transcript = lastResult[0].transcript;
        const confidence = lastResult[0].confidence;
        const isFinal = lastResult.isFinal;

        // Create transcription result
        const result: TranscriptionResult = {
          text: transcript,
          confidence: confidence,
          language: this.recognition?.lang || 'en-US',
          isFinal: isFinal
        };

        // Call callback if set
        if (this.onTranscriptionCallback) {
          this.onTranscriptionCallback(result);
        }
      }
    };

    // Handle errors
    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      
      let errorMessage = 'Speech recognition error';
      
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected. Please try again.';
          break;
        case 'audio-capture':
          errorMessage = 'Microphone not available. Please check your settings.';
          break;
        case 'not-allowed':
          errorMessage = 'Microphone access denied. Please allow microphone access.';
          break;
        case 'network':
          errorMessage = 'Network error. Please check your connection.';
          break;
        default:
          errorMessage = `Speech recognition error: ${event.error}`;
      }

      if (this.onErrorCallback) {
        this.onErrorCallback(errorMessage);
      }
    };

    // Handle end of recognition
    this.recognition.onend = () => {
      this.isListening = false;
      
      // Restart if continuous mode is enabled
      if (this.recognition?.continuous && this.isListening) {
        this.start();
      }
    };

    // Handle start
    this.recognition.onstart = () => {
      this.isListening = true;
      console.log('Speech recognition started');
    };
  }

  /**
   * Start listening for speech
   */
  start(): void {
    if (!this.recognition) {
      throw new Error('Speech recognition not initialized. Call initialize() first.');
    }

    if (this.isListening) {
      console.warn('Speech recognition is already listening');
      return;
    }

    try {
      this.recognition.start();
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      if (this.onErrorCallback) {
        this.onErrorCallback('Failed to start speech recognition');
      }
    }
  }

  /**
   * Stop listening for speech
   */
  stop(): void {
    if (!this.recognition) {
      return;
    }

    if (!this.isListening) {
      console.warn('Speech recognition is not listening');
      return;
    }

    try {
      this.recognition.stop();
      this.isListening = false;
    } catch (error) {
      console.error('Error stopping speech recognition:', error);
    }
  }

  /**
   * Set callback for transcription results
   */
  onTranscription(callback: (result: TranscriptionResult) => void): void {
    this.onTranscriptionCallback = callback;
  }

  /**
   * Set callback for errors
   */
  onError(callback: (error: string) => void): void {
    this.onErrorCallback = callback;
  }

  /**
   * Change recognition language
   */
  setLanguage(language: string): void {
    if (this.recognition) {
      this.recognition.lang = language;
    }
  }

  /**
   * Get current listening status
   */
  getIsListening(): boolean {
    return this.isListening;
  }

  /**
   * Clean up resources
   */
  cleanup(): void {
    this.stop();
    this.stopSpeaking();
    this.recognition = null;
    this.onTranscriptionCallback = null;
    this.onErrorCallback = null;
  }

  // ==========================================
  // TEXT-TO-SPEECH (TTS) METHODS
  // ==========================================

  /**
   * Speak text using Web Speech API
   */
  speak(text: string, config: TTSConfig = {}): Promise<TTSResult> {
    return new Promise((resolve) => {
      if (!this.isTTSSupported()) {
        resolve({ success: false, error: 'Text-to-Speech not supported in this browser' });
        return;
      }

      if (!text || !text.trim()) {
        resolve({ success: false, error: 'No text provided to speak' });
        return;
      }

      // Stop any current speech
      this.stopSpeaking();

      // Create utterance
      this.currentUtterance = new SpeechSynthesisUtterance(text);

      // Configure voice with gender preference
      const selectedVoice = this.selectVoice(config.voice, config.language, config.gender);
      if (selectedVoice) {
        this.currentUtterance.voice = selectedVoice;
        console.log(`Selected voice: ${selectedVoice.name} (${selectedVoice.lang}) for ${config.gender || 'default'} preference`);
      }

      // Set speech parameters
      this.currentUtterance.rate = config.rate ?? 1.0;
      this.currentUtterance.pitch = config.pitch ?? 1.0;
      this.currentUtterance.volume = config.volume ?? 1.0;

      // Set up event handlers
      this.currentUtterance.onstart = () => {
        this.isSpeaking = true;
        console.log('🔊 Speaking:', text.substring(0, 50) + (text.length > 50 ? '...' : ''));
      };

      this.currentUtterance.onend = () => {
        this.isSpeaking = false;
        this.currentUtterance = null;
        console.log('✅ Speech completed');
        resolve({ success: true });
      };

      this.currentUtterance.onerror = (event) => {
        this.isSpeaking = false;
        this.currentUtterance = null;
        console.error('❌ Speech error:', event.error);
        resolve({ success: false, error: `Speech error: ${event.error}` });
      };

      // Speak the text
      try {
        this.synthesis.speak(this.currentUtterance);
      } catch (error) {
        this.isSpeaking = false;
        this.currentUtterance = null;
        resolve({ success: false, error: `Failed to start speech: ${error}` });
      }
    });
  }

  /**
   * Stop current speech
   */
  stopSpeaking(): void {
    if (this.synthesis.speaking) {
      this.synthesis.cancel();
    }
    this.isSpeaking = false;
    this.currentUtterance = null;
  }

  /**
   * Select appropriate voice based on preferences including gender
   */
  private selectVoice(voiceName?: string, language?: string, gender?: 'male' | 'female'): SpeechSynthesisVoice | null {
    if (this.voices.length === 0) {
      this.loadVoices();
    }

    console.log(`🎤 Selecting voice for: language=${language}, gender=${gender}, voiceName=${voiceName}`);
    console.log(`Available voices:`, this.voices.map(v => `${v.name} (${v.lang})`));

    // If specific voice name is provided, try to find it
    if (voiceName) {
      const voice = this.voices.find(v => 
        v.name.toLowerCase().includes(voiceName.toLowerCase()) ||
        v.name === voiceName
      );
      if (voice) {
        console.log(`✅ Found specific voice: ${voice.name}`);
        return voice;
      }
    }

    // Focus on English voices first, then apply gender preference
    const englishVoices = this.voices.filter(v => v.lang.startsWith('en'));
    console.log(`English voices available:`, englishVoices.map(v => `${v.name} (${v.lang})`));

    if (gender === 'male') {
      // Look for male voices - be more specific about male indicators
      const maleVoices = englishVoices.filter(v => {
        const name = v.name.toLowerCase();
        return (
          name.includes('david') ||
          name.includes('mark') ||
          name.includes('guy') ||
          name.includes('ravi') ||
          name.includes('male') ||
          (name.includes('google') && name.includes('us') && !name.includes('female')) ||
          (name.includes('microsoft') && (name.includes('david') || name.includes('mark')))
        );
      });
      
      console.log(`Male voices found:`, maleVoices.map(v => v.name));
      
      if (maleVoices.length > 0) {
        const selectedVoice = maleVoices[0];
        console.log(`✅ Selected male voice: ${selectedVoice.name}`);
        return selectedVoice;
      }
      
      // Fallback: try to find any non-female English voice
      const nonFemaleVoice = englishVoices.find(v => !v.name.toLowerCase().includes('female'));
      if (nonFemaleVoice) {
        console.log(`✅ Selected non-female fallback: ${nonFemaleVoice.name}`);
        return nonFemaleVoice;
      }
      
    } else if (gender === 'female') {
      // Look for female voices
      const femaleVoices = englishVoices.filter(v => {
        const name = v.name.toLowerCase();
        return (
          name.includes('female') ||
          name.includes('zira') ||
          name.includes('aria') ||
          name.includes('samantha') ||
          name.includes('heera') ||
          name.includes('shruti') ||
          (name.includes('google') && name.includes('female'))
        );
      });
      
      console.log(`Female voices found:`, femaleVoices.map(v => v.name));
      
      if (femaleVoices.length > 0) {
        const selectedVoice = femaleVoices[0];
        console.log(`✅ Selected female voice: ${selectedVoice.name}`);
        return selectedVoice;
      }
    }

    // If no gender-specific voice found, return first English voice
    if (englishVoices.length > 0) {
      console.log(`⚠️ No gender-specific voice found, using first English voice: ${englishVoices[0].name}`);
      return englishVoices[0];
    }

    // Final fallback
    if (this.voices.length > 0) {
      console.log(`⚠️ No English voice found, using first available: ${this.voices[0].name}`);
      return this.voices[0];
    }

    console.log(`❌ No voices available`);
    return null;
  }

  /**
   * Get available voices
   */
  getVoices(): SpeechSynthesisVoice[] {
    return this.voices;
  }

  /**
   * Test voice selection for debugging
   */
  testVoiceSelection(gender: 'male' | 'female' = 'male'): void {
    console.log(`🧪 Testing voice selection for ${gender}:`);
    const selectedVoice = this.selectVoice(undefined, 'en', gender);
    if (selectedVoice) {
      console.log(`Selected: ${selectedVoice.name} (${selectedVoice.lang})`);
      // Test speak
      this.speak(`Testing ${gender} voice selection`, { gender: gender, language: 'en' });
    } else {
      console.log('No voice selected');
    }
  }

  /**
   * Get current speaking status
   */
  getIsSpeaking(): boolean {
    return this.isSpeaking;
  }

  /**
   * Speak AI response with automatic language detection and gender preference
   */
  async speakAIResponse(response: string, language: string = 'en', gender: 'male' | 'female' = 'male'): Promise<TTSResult> {
    console.log(`🎤 webSpeechService.speakAIResponse called with:`);
    console.log(`   - Text: "${response.substring(0, 50)}${response.length > 50 ? '...' : ''}"`);
    console.log(`   - Language: ${language}`);
    console.log(`   - Gender: ${gender}`);
    
    const config: TTSConfig = {
      language: language,
      gender: gender,
      rate: 1.0,
      pitch: 1.0,
      volume: 1.0
    };

    // Don't pre-select voice name, let selectVoice handle it based on gender
    return this.speak(response, config);
  }
}

// Export singleton instance
export const webSpeechService = new WebSpeechService();

/**
 * GrammarEditor Component
 * Text input area for grammar checking with real-time feedback
 */

import { useState } from 'react';
import './GrammarEditor.css';
import { ErrorHighlight } from './ErrorHighlight';
import { ExplanationTooltip } from './ExplanationTooltip';
import { LoadingSpinner } from './LoadingSpinner';
import { useToast } from '../contexts/ToastContext';
import { useOnlineStatus } from '../hooks/useOnlineStatus';
import { MdSpellcheck } from 'react-icons/md';

interface GrammarError {
  start_pos: number;
  end_pos: number;
  error_type: string;
  original_text: string;
  corrected_text: string;
  explanation: string;
  severity: string;
}

interface GrammarCheckResponse {
  original_text: string;
  corrected_text: string;
  errors: GrammarError[];
  overall_score: number;
  has_errors: boolean;
}

export function GrammarEditor() {
  const [text, setText] = useState('');
  const [isChecking, setIsChecking] = useState(false);
  const [grammarResult, setGrammarResult] = useState<GrammarCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hoveredError, setHoveredError] = useState<GrammarError | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number } | null>(null);
  const { showError, showSuccess } = useToast();
  const isOnline = useOnlineStatus();

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    // Clear previous results when text changes
    setGrammarResult(null);
    setError(null);
  };

  const handleCheckGrammar = async () => {
    if (!text.trim()) {
      showError('Please enter some text to check');
      return;
    }

    if (!isOnline) {
      showError('You are offline. Please check your internet connection.');
      return;
    }

    setIsChecking(true);
    setError(null);
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/grammar/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Grammar check failed' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result: GrammarCheckResponse = await response.json();
      setGrammarResult(result);
      
      if (result.has_errors) {
        showSuccess(`Found ${result.errors.length} grammar issue${result.errors.length !== 1 ? 's' : ''}`);
      } else {
        showSuccess('Perfect! No grammar errors found.');
      }
    } catch (err) {
      console.error('Grammar check error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to check grammar. Please try again.';
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setIsChecking(false);
    }
  };

  const handleClear = () => {
    setText('');
    setGrammarResult(null);
    setError(null);
    setHoveredError(null);
    setTooltipPosition(null);
  };

  const handleErrorHover = (grammarError: GrammarError, event: React.MouseEvent) => {
    setHoveredError(grammarError);
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    setTooltipPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
    });
  };

  const handleErrorLeave = () => {
    setHoveredError(null);
    setTooltipPosition(null);
  };

  return (
    <div className="grammar-editor">
      <div className="editor-header">
        <h2>Grammar Check</h2>
        <p className="editor-description">
          Type or paste your English text below for instant grammar correction and explanations
        </p>
      </div>

      <div className="editor-container">
        <div className="editor-panel">
          <div className="panel-header">
            <h3>Your Text</h3>
            <div className="editor-actions">
              <button
                className="btn btn-secondary"
                onClick={handleClear}
                disabled={!text}
              >
                Clear
              </button>
              <button
                className="btn btn-primary"
                onClick={handleCheckGrammar}
                disabled={!text.trim() || isChecking}
              >
                {isChecking ? 'Checking...' : 'Check Grammar'}
              </button>
            </div>
          </div>
          
          <div className="text-input-container">
            {grammarResult && grammarResult.has_errors ? (
              <ErrorHighlight
                text={grammarResult.original_text}
                errors={grammarResult.errors}
                onErrorHover={handleErrorHover}
                onErrorLeave={handleErrorLeave}
              />
            ) : (
              <textarea
                className="text-input"
                value={text}
                onChange={handleTextChange}
                placeholder="Start typing your English text here... Captain will help you improve your grammar!"
                rows={15}
              />
            )}
          </div>
          
          <div className="editor-stats">
            <span>Characters: {text.length}</span>
            <span>Words: {text.trim() ? text.trim().split(/\s+/).length : 0}</span>
            {grammarResult && (
              <span className="score">
                Score: {Math.round(grammarResult.overall_score)}/100
              </span>
            )}
          </div>
        </div>

        <div className="feedback-panel">
          <div className="panel-header">
            <h3>Grammar Feedback</h3>
          </div>
          
          <div className="feedback-content">
            {isChecking ? (
              <LoadingSpinner size="medium" message="Analyzing your grammar..." />
            ) : error ? (
              <div className="feedback-error">
                <span className="error-icon">⚠️</span>
                <p>{error}</p>
              </div>
            ) : !text.trim() ? (
              <div className="feedback-placeholder">
                <MdSpellcheck className="placeholder-icon" />
                <p>Start typing to get grammar feedback</p>
              </div>
            ) : !grammarResult ? (
              <div className="feedback-placeholder">
                <span className="placeholder-icon">🔍</span>
                <p>Click "Check Grammar" to analyze your text</p>
              </div>
            ) : grammarResult.has_errors ? (
              <div className="feedback-results">
                <div className="results-summary">
                  <h4>Found {grammarResult.errors.length} issue{grammarResult.errors.length !== 1 ? 's' : ''}</h4>
                  <div className="corrected-text">
                    <strong>Corrected version:</strong>
                    <p>{grammarResult.corrected_text}</p>
                  </div>
                </div>
                <div className="error-list">
                  {grammarResult.errors.map((err, index) => (
                    <div key={index} className={`error-item severity-${err.severity}`}>
                      <div className="error-header">
                        <span className="error-type">{err.error_type}</span>
                        <span className={`severity-badge ${err.severity}`}>
                          {err.severity}
                        </span>
                      </div>
                      <div className="error-details">
                        <div className="error-text">
                          <span className="original">"{err.original_text}"</span>
                          <span className="arrow">→</span>
                          <span className="corrected">"{err.corrected_text}"</span>
                        </div>
                        <p className="error-explanation">{err.explanation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="feedback-success">
                <span className="success-icon">✅</span>
                <h4>Perfect!</h4>
                <p>No grammar errors found. Great job!</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="editor-tips">
        <h4>💡 Tips for better results:</h4>
        <ul>
          <li>Write complete sentences for accurate analysis</li>
          <li>Check your text regularly to learn from mistakes</li>
          <li>Read the explanations to understand grammar rules</li>
        </ul>
      </div>

      {hoveredError && tooltipPosition && (
        <ExplanationTooltip
          error={hoveredError}
          position={tooltipPosition}
        />
      )}
    </div>
  );
}

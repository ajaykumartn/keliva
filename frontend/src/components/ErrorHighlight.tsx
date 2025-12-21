/**
 * ErrorHighlight Component
 * Displays text with visual indicators for grammar errors
 */

import './ErrorHighlight.css';

interface GrammarError {
  start_pos: number;
  end_pos: number;
  error_type: string;
  original_text: string;
  corrected_text: string;
  explanation: string;
  severity: string;
}

interface ErrorHighlightProps {
  text: string;
  errors: GrammarError[];
  onErrorHover: (error: GrammarError, event: React.MouseEvent) => void;
  onErrorLeave: () => void;
}

export function ErrorHighlight({ text, errors, onErrorHover, onErrorLeave }: ErrorHighlightProps) {
  // Sort errors by start position to process them in order
  const sortedErrors = [...errors].sort((a, b) => a.start_pos - b.start_pos);

  // Build segments of text with error markers
  const segments: Array<{ text: string; error?: GrammarError }> = [];
  let currentPos = 0;

  sortedErrors.forEach((error) => {
    // Add text before the error
    if (currentPos < error.start_pos) {
      segments.push({ text: text.substring(currentPos, error.start_pos) });
    }

    // Add the error segment
    segments.push({
      text: text.substring(error.start_pos, error.end_pos),
      error: error,
    });

    currentPos = error.end_pos;
  });

  // Add remaining text after the last error
  if (currentPos < text.length) {
    segments.push({ text: text.substring(currentPos) });
  }

  return (
    <div className="error-highlight-container">
      {segments.map((segment, index) => {
        if (segment.error) {
          return (
            <span
              key={index}
              className={`error-highlight severity-${segment.error.severity}`}
              onMouseEnter={(e) => onErrorHover(segment.error!, e)}
              onMouseLeave={onErrorLeave}
              data-error-type={segment.error.error_type}
            >
              {segment.text}
            </span>
          );
        }
        return <span key={index}>{segment.text}</span>;
      })}
    </div>
  );
}

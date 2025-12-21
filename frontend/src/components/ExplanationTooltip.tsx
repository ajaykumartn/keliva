/**
 * ExplanationTooltip Component
 * Displays detailed error information in a tooltip
 */

import './ExplanationTooltip.css';

interface GrammarError {
  start_pos: number;
  end_pos: number;
  error_type: string;
  original_text: string;
  corrected_text: string;
  explanation: string;
  severity: string;
}

interface ExplanationTooltipProps {
  error: GrammarError;
  position: { x: number; y: number };
}

export function ExplanationTooltip({ error, position }: ExplanationTooltipProps) {
  return (
    <div
      className="explanation-tooltip"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
      }}
    >
      <div className={`tooltip-content severity-${error.severity}`}>
        <div className="tooltip-header">
          <span className="tooltip-type">{error.error_type}</span>
          <span className={`tooltip-severity ${error.severity}`}>
            {error.severity}
          </span>
        </div>
        
        <div className="tooltip-correction">
          <div className="correction-row">
            <span className="label">Original:</span>
            <span className="original-text">"{error.original_text}"</span>
          </div>
          <div className="correction-row">
            <span className="label">Corrected:</span>
            <span className="corrected-text">"{error.corrected_text}"</span>
          </div>
        </div>
        
        <div className="tooltip-explanation">
          <p>{error.explanation}</p>
        </div>
        
        <div className="tooltip-arrow"></div>
      </div>
    </div>
  );
}

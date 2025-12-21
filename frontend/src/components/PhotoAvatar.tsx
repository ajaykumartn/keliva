/**
 * PhotoAvatar Component
 * Clickable avatar that flips between Pandu and Chandu
 */
import { useEffect, useState } from 'react';
import { FaUserGraduate } from 'react-icons/fa';
import { MdSupportAgent } from 'react-icons/md';
import { HiCursorClick } from 'react-icons/hi';
import './PhotoAvatar.css';

interface PhotoAvatarProps {
  gender: 'male' | 'female';
  isSpeaking: boolean;
  name: string;
  onFlip: () => void;
}

export function PhotoAvatar({ gender, isSpeaking, name, onFlip }: PhotoAvatarProps) {
  const [waveScale, setWaveScale] = useState(1);
  const [isFlipping, setIsFlipping] = useState(false);

  useEffect(() => {
    if (isSpeaking) {
      const interval = setInterval(() => {
        setWaveScale(1 + Math.random() * 0.3);
      }, 100);
      return () => clearInterval(interval);
    } else {
      setWaveScale(1);
    }
  }, [isSpeaking]);

  const handleClick = () => {
    setIsFlipping(true);
    setTimeout(() => {
      onFlip();
      setIsFlipping(false);
    }, 300);
  };

  // Avatar icon based on gender
  const AvatarIcon = gender === 'male' ? FaUserGraduate : MdSupportAgent;

  return (
    <div className="photo-avatar-container">
      <div className="avatar-wrapper">
        {/* Voice waves */}
        {isSpeaking && (
          <>
            <div className="voice-wave wave-1" style={{ transform: `scale(${waveScale})` }}></div>
            <div className="voice-wave wave-2" style={{ transform: `scale(${waveScale * 1.2})` }}></div>
            <div className="voice-wave wave-3" style={{ transform: `scale(${waveScale * 1.4})` }}></div>
          </>
        )}
        
        {/* Avatar circle - clickable */}
        <div 
          className={`avatar-circle ${isSpeaking ? 'speaking' : ''} ${isFlipping ? 'flipping' : ''}`}
          onClick={handleClick}
          title="Click to switch between Pandu and Chandu"
        >
          <div className="avatar-emoji">
            <AvatarIcon />
          </div>
          <div className="flip-hint">
            <HiCursorClick /> Tap to switch
          </div>
        </div>
      </div>
      
      {/* Name */}
      <div className="avatar-name">{name}</div>
      
      {/* Status */}
      {isSpeaking && (
        <div className="speaking-status">
          <span className="pulse-dot"></span>
          <span>Speaking...</span>
        </div>
      )}
    </div>
  );
}

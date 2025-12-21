/**
 * AudioVisualizer Component
 * Displays real-time waveform visualization for voice calls
 * 
 * Requirements:
 * - Visual feedback during voice conversations
 * - Waveform display for audio input
 * - Animated bars showing audio levels
 */

import { useEffect, useRef, useState } from 'react';
import './AudioVisualizer.css';

export interface AudioVisualizerProps {
  isActive: boolean;
  audioStream?: MediaStream | null;
}

export function AudioVisualizer({ isActive, audioStream }: AudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const [bars, setBars] = useState<number[]>(new Array(32).fill(0));

  useEffect(() => {
    if (!isActive || !audioStream) {
      // Stop visualization
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      analyserRef.current = null;
      setBars(new Array(32).fill(0));
      return;
    }

    // Set up audio analysis
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(audioStream);
      
      analyser.fftSize = 64; // 32 frequency bins
      analyser.smoothingTimeConstant = 0.8;
      
      source.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      // Start visualization loop
      visualize();
    } catch (error) {
      console.error('Error setting up audio visualization:', error);
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [isActive, audioStream]);

  const visualize = () => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    // Normalize values to 0-1 range
    const normalizedBars = Array.from(dataArray).map(value => value / 255);
    setBars(normalizedBars);

    // Continue animation loop
    animationFrameRef.current = requestAnimationFrame(visualize);
  };

  // Canvas-based visualization (alternative to CSS bars)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!isActive) return;

    // Draw waveform bars
    const barWidth = canvas.width / bars.length;
    const barGap = 2;

    bars.forEach((value, index) => {
      const barHeight = value * canvas.height * 0.8;
      const x = index * barWidth;
      const y = (canvas.height - barHeight) / 2;

      // Create gradient
      const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
      gradient.addColorStop(0, '#3b82f6');
      gradient.addColorStop(0.5, '#8b5cf6');
      gradient.addColorStop(1, '#ec4899');

      ctx.fillStyle = gradient;
      ctx.fillRect(x + barGap / 2, y, barWidth - barGap, barHeight);
    });
  }, [bars, isActive]);

  return (
    <div className="audio-visualizer">
      <canvas
        ref={canvasRef}
        width={800}
        height={100}
        className="visualizer-canvas"
      />
      {!isActive && (
        <div className="visualizer-placeholder">
          <span className="placeholder-icon">🎵</span>
          <span className="placeholder-text">Start speaking to see waveform</span>
        </div>
      )}
    </div>
  );
}

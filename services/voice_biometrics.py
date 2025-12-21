"""
Voice Biometric Tracking Service
Tracks voice characteristics and pronunciation improvement over time
"""
import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import secrets

@dataclass
class VoiceFeatures:
    pitch_mean: float
    pitch_std: float
    energy_mean: float
    energy_std: float
    speaking_rate: float
    pause_frequency: float
    voice_quality_score: float
    pronunciation_clarity: float
    accent_markers: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pitch_mean': self.pitch_mean,
            'pitch_std': self.pitch_std,
            'energy_mean': self.energy_mean,
            'energy_std': self.energy_std,
            'speaking_rate': self.speaking_rate,
            'pause_frequency': self.pause_frequency,
            'voice_quality_score': self.voice_quality_score,
            'pronunciation_clarity': self.pronunciation_clarity,
            'accent_markers': self.accent_markers
        }

@dataclass
class PronunciationProgress:
    user_id: str
    language: str
    phoneme_scores: Dict[str, float]
    word_accuracy_scores: Dict[str, float]
    overall_improvement: float
    problem_areas: List[str]
    strengths: List[str]
    recommendations: List[str]
    last_assessment: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'language': self.language,
            'phoneme_scores': self.phoneme_scores,
            'word_accuracy_scores': self.word_accuracy_scores,
            'overall_improvement': self.overall_improvement,
            'problem_areas': self.problem_areas,
            'strengths': self.strengths,
            'recommendations': self.recommendations,
            'last_assessment': self.last_assessment.isoformat()
        }

@dataclass
class VoiceBiometricProfile:
    user_id: str
    baseline_features: VoiceFeatures
    current_features: VoiceFeatures
    improvement_metrics: Dict[str, float]
    voice_consistency_score: float
    unique_voice_signature: str
    created_at: datetime
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'baseline_features': self.baseline_features.to_dict(),
            'current_features': self.current_features.to_dict(),
            'improvement_metrics': self.improvement_metrics,
            'voice_consistency_score': self.voice_consistency_score,
            'unique_voice_signature': self.unique_voice_signature,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }

class VoiceBiometricService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
        
        # Phoneme difficulty mapping for different languages
        self.phoneme_difficulty = {
            'en': {
                'easy': ['a', 'e', 'i', 'o', 'u', 'm', 'n', 'p', 'b'],
                'medium': ['t', 'd', 'k', 'g', 'f', 'v', 's', 'z'],
                'hard': ['θ', 'ð', 'ʃ', 'ʒ', 'tʃ', 'dʒ', 'r', 'l']
            },
            'kn': {
                'easy': ['ಅ', 'ಆ', 'ಇ', 'ಈ', 'ಉ', 'ಊ'],
                'medium': ['ಕ', 'ಖ', 'ಗ', 'ಘ', 'ಙ'],
                'hard': ['ಞ', 'ಟ', 'ಠ', 'ಡ', 'ಢ', 'ಣ']
            },
            'te': {
                'easy': ['అ', 'ఆ', 'ఇ', 'ఈ', 'ఉ', 'ఊ'],
                'medium': ['క', 'ఖ', 'గ', 'ఘ', 'ఙ'],
                'hard': ['ఞ', 'ట', 'ఠ', 'డ', 'ఢ', 'ణ']
            }
        }
    
    def init_database(self):
        """Initialize voice biometric tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Voice samples table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_samples (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                language TEXT NOT NULL,
                text_spoken TEXT,
                voice_features TEXT NOT NULL,
                pronunciation_scores TEXT,
                recording_quality REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Pronunciation progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pronunciation_progress (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                language TEXT NOT NULL,
                assessment_data TEXT NOT NULL,
                overall_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Voice biometric profiles table (updated structure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_biometric_profiles (
                user_id TEXT PRIMARY KEY,
                baseline_features TEXT NOT NULL,
                current_features TEXT NOT NULL,
                improvement_metrics TEXT,
                voice_consistency_score REAL DEFAULT 0.0,
                unique_voice_signature TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def extract_voice_features(self, audio_data: bytes, sample_rate: int = 16000) -> VoiceFeatures:
        """Extract voice features from audio data"""
        # This is a simplified version - in production, use librosa, praat-parselmouth, or similar
        # For now, we'll simulate feature extraction
        
        # Simulate pitch analysis
        pitch_values = np.random.normal(150, 30, 100)  # Simulated pitch values
        pitch_mean = float(np.mean(pitch_values))
        pitch_std = float(np.std(pitch_values))
        
        # Simulate energy analysis
        energy_values = np.random.normal(0.5, 0.2, 100)
        energy_mean = float(np.mean(energy_values))
        energy_std = float(np.std(energy_values))
        
        # Simulate other features
        speaking_rate = np.random.uniform(2.0, 6.0)  # syllables per second
        pause_frequency = np.random.uniform(0.1, 0.5)  # pauses per second
        voice_quality_score = np.random.uniform(0.6, 0.95)
        pronunciation_clarity = np.random.uniform(0.5, 0.9)
        
        # Simulate accent markers
        accent_markers = {
            'r_pronunciation': np.random.uniform(0.3, 0.9),
            'th_sounds': np.random.uniform(0.2, 0.8),
            'vowel_clarity': np.random.uniform(0.5, 0.95),
            'consonant_precision': np.random.uniform(0.4, 0.9)
        }
        
        return VoiceFeatures(
            pitch_mean=pitch_mean,
            pitch_std=pitch_std,
            energy_mean=energy_mean,
            energy_std=energy_std,
            speaking_rate=speaking_rate,
            pause_frequency=pause_frequency,
            voice_quality_score=voice_quality_score,
            pronunciation_clarity=pronunciation_clarity,
            accent_markers=accent_markers
        )
    
    def analyze_pronunciation(self, text_spoken: str, voice_features: VoiceFeatures, 
                            expected_text: str, language: str) -> Dict[str, float]:
        """Analyze pronunciation accuracy"""
        # Simplified pronunciation analysis
        pronunciation_scores = {}
        
        # Word-level accuracy (simplified)
        spoken_words = text_spoken.lower().split()
        expected_words = expected_text.lower().split()
        
        for i, (spoken, expected) in enumerate(zip(spoken_words, expected_words)):
            # Simple similarity score (in production, use phonetic analysis)
            similarity = self._calculate_word_similarity(spoken, expected)
            pronunciation_scores[f"word_{i}_{expected}"] = similarity
        
        # Phoneme-level analysis (simplified)
        phonemes = self.phoneme_difficulty.get(language, self.phoneme_difficulty['en'])
        
        for difficulty, phoneme_list in phonemes.items():
            # Simulate phoneme accuracy based on voice features
            base_score = voice_features.pronunciation_clarity
            
            if difficulty == 'easy':
                score = min(0.95, base_score + 0.2)
            elif difficulty == 'medium':
                score = base_score
            else:  # hard
                score = max(0.3, base_score - 0.2)
            
            for phoneme in phoneme_list[:3]:  # Limit for demo
                pronunciation_scores[f"phoneme_{phoneme}"] = score + np.random.uniform(-0.1, 0.1)
        
        return pronunciation_scores
    
    def _calculate_word_similarity(self, word1: str, word2: str) -> float:
        """Calculate similarity between two words (simplified)"""
        if word1 == word2:
            return 1.0
        
        # Simple character-based similarity
        max_len = max(len(word1), len(word2))
        if max_len == 0:
            return 1.0
        
        matches = sum(c1 == c2 for c1, c2 in zip(word1, word2))
        return matches / max_len
    
    def create_voice_profile(self, user_id: str, initial_voice_features: VoiceFeatures) -> str:
        """Create initial voice biometric profile for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate unique voice signature
        voice_signature = hashlib.sha256(
            f"{user_id}_{initial_voice_features.pitch_mean}_{initial_voice_features.energy_mean}_{datetime.now()}".encode()
        ).hexdigest()[:16]
        
        improvement_metrics = {
            'pronunciation_improvement': 0.0,
            'fluency_improvement': 0.0,
            'confidence_improvement': 0.0,
            'consistency_improvement': 0.0
        }
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO voice_biometric_profiles 
                (user_id, baseline_features, current_features, improvement_metrics,
                 voice_consistency_score, unique_voice_signature)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                json.dumps(initial_voice_features.to_dict()),
                json.dumps(initial_voice_features.to_dict()),
                json.dumps(improvement_metrics),
                0.0,
                voice_signature
            ))
            
            conn.commit()
            return voice_signature
            
        except Exception as e:
            print(f"Error creating voice profile: {e}")
            return None
        finally:
            conn.close()
    
    def update_voice_profile(self, user_id: str, new_voice_features: VoiceFeatures) -> bool:
        """Update user's voice profile with new sample"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get existing profile
            cursor.execute('''
                SELECT baseline_features, current_features, improvement_metrics, voice_consistency_score
                FROM voice_biometric_profiles WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if not row:
                # Create new profile if doesn't exist
                return self.create_voice_profile(user_id, new_voice_features) is not None
            
            baseline_features = VoiceFeatures(**json.loads(row[0]))
            current_features = VoiceFeatures(**json.loads(row[1]))
            improvement_metrics = json.loads(row[2])
            
            # Calculate improvements
            pronunciation_improvement = (
                new_voice_features.pronunciation_clarity - baseline_features.pronunciation_clarity
            )
            
            fluency_improvement = (
                new_voice_features.speaking_rate - baseline_features.speaking_rate
            ) / baseline_features.speaking_rate if baseline_features.speaking_rate > 0 else 0
            
            # Voice consistency (how similar new sample is to previous samples)
            consistency_score = self._calculate_voice_consistency(current_features, new_voice_features)
            
            # Update improvement metrics
            improvement_metrics.update({
                'pronunciation_improvement': pronunciation_improvement,
                'fluency_improvement': fluency_improvement,
                'consistency_improvement': consistency_score,
                'voice_quality_improvement': (
                    new_voice_features.voice_quality_score - baseline_features.voice_quality_score
                )
            })
            
            # Update profile
            cursor.execute('''
                UPDATE voice_biometric_profiles 
                SET current_features = ?, improvement_metrics = ?, 
                    voice_consistency_score = ?, last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                json.dumps(new_voice_features.to_dict()),
                json.dumps(improvement_metrics),
                consistency_score,
                user_id
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating voice profile: {e}")
            return False
        finally:
            conn.close()
    
    def _calculate_voice_consistency(self, features1: VoiceFeatures, features2: VoiceFeatures) -> float:
        """Calculate consistency score between two voice feature sets"""
        # Compare key features
        pitch_diff = abs(features1.pitch_mean - features2.pitch_mean) / max(features1.pitch_mean, features2.pitch_mean)
        energy_diff = abs(features1.energy_mean - features2.energy_mean) / max(features1.energy_mean, features2.energy_mean)
        rate_diff = abs(features1.speaking_rate - features2.speaking_rate) / max(features1.speaking_rate, features2.speaking_rate)
        
        # Calculate overall consistency (lower differences = higher consistency)
        consistency = 1.0 - (pitch_diff + energy_diff + rate_diff) / 3.0
        return max(0.0, min(1.0, consistency))
    
    def store_voice_sample(self, user_id: str, language: str, text_spoken: str, 
                          voice_features: VoiceFeatures, pronunciation_scores: Dict[str, float],
                          recording_quality: float = 0.8) -> str:
        """Store a voice sample for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sample_id = f"voice_{secrets.token_urlsafe(12)}"
        
        try:
            cursor.execute('''
                INSERT INTO voice_samples 
                (id, user_id, language, text_spoken, voice_features, 
                 pronunciation_scores, recording_quality)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                sample_id,
                user_id,
                language,
                text_spoken,
                json.dumps(voice_features.to_dict()),
                json.dumps(pronunciation_scores),
                recording_quality
            ))
            
            conn.commit()
            
            # Update voice profile
            self.update_voice_profile(user_id, voice_features)
            
            return sample_id
            
        except Exception as e:
            print(f"Error storing voice sample: {e}")
            return None
        finally:
            conn.close()
    
    def get_pronunciation_progress(self, user_id: str, language: str, 
                                 days_back: int = 30) -> Optional[PronunciationProgress]:
        """Get pronunciation progress for user in specific language"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent voice samples
        cursor.execute('''
            SELECT voice_features, pronunciation_scores, created_at
            FROM voice_samples 
            WHERE user_id = ? AND language = ? 
            AND created_at >= datetime('now', '-{} days')
            ORDER BY created_at DESC
        '''.format(days_back), (user_id, language))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        # Analyze progress
        all_pronunciation_scores = {}
        phoneme_scores = {}
        word_scores = {}
        
        for row in rows:
            scores = json.loads(row[1])
            for key, score in scores.items():
                if key.startswith('phoneme_'):
                    phoneme = key.split('_')[1]
                    if phoneme not in phoneme_scores:
                        phoneme_scores[phoneme] = []
                    phoneme_scores[phoneme].append(score)
                elif key.startswith('word_'):
                    word = key.split('_', 2)[2]
                    if word not in word_scores:
                        word_scores[word] = []
                    word_scores[word].append(score)
        
        # Calculate averages and improvements
        phoneme_averages = {k: np.mean(v) for k, v in phoneme_scores.items()}
        word_averages = {k: np.mean(v) for k, v in word_scores.items()}
        
        # Identify problem areas and strengths
        problem_areas = [k for k, v in phoneme_averages.items() if v < 0.6]
        strengths = [k for k, v in phoneme_averages.items() if v > 0.8]
        
        # Calculate overall improvement
        if len(rows) > 1:
            recent_scores = json.loads(rows[0][1])
            older_scores = json.loads(rows[-1][1])
            
            recent_avg = np.mean(list(recent_scores.values()))
            older_avg = np.mean(list(older_scores.values()))
            overall_improvement = recent_avg - older_avg
        else:
            overall_improvement = 0.0
        
        # Generate recommendations
        recommendations = self._generate_pronunciation_recommendations(
            problem_areas, strengths, language
        )
        
        return PronunciationProgress(
            user_id=user_id,
            language=language,
            phoneme_scores=phoneme_averages,
            word_accuracy_scores=word_averages,
            overall_improvement=overall_improvement,
            problem_areas=problem_areas,
            strengths=strengths,
            recommendations=recommendations,
            last_assessment=datetime.now()
        )
    
    def _generate_pronunciation_recommendations(self, problem_areas: List[str], 
                                             strengths: List[str], language: str) -> List[str]:
        """Generate personalized pronunciation recommendations"""
        recommendations = []
        
        if problem_areas:
            recommendations.append(f"Focus on practicing these sounds: {', '.join(problem_areas[:3])}")
            
            # Language-specific recommendations
            if language == 'en':
                if any(sound in problem_areas for sound in ['θ', 'ð']):
                    recommendations.append("Practice 'th' sounds by placing tongue between teeth")
                if 'r' in problem_areas:
                    recommendations.append("Practice 'r' sound by curling tongue tip slightly back")
            
        if strengths:
            recommendations.append(f"Great job with: {', '.join(strengths[:3])}! Keep it up!")
        
        recommendations.append("Try recording yourself daily to track improvement")
        recommendations.append("Practice with tongue twisters for better articulation")
        
        return recommendations
    
    def get_voice_biometric_profile(self, user_id: str) -> Optional[VoiceBiometricProfile]:
        """Get complete voice biometric profile for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM voice_biometric_profiles WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return VoiceBiometricProfile(
                user_id=row[0],
                baseline_features=VoiceFeatures(**json.loads(row[1])),
                current_features=VoiceFeatures(**json.loads(row[2])),
                improvement_metrics=json.loads(row[3]) if row[3] else {},
                voice_consistency_score=row[4],
                unique_voice_signature=row[5],
                created_at=datetime.fromisoformat(row[6]),
                last_updated=datetime.fromisoformat(row[7])
            )
        return None
    
    def get_voice_improvement_timeline(self, user_id: str, days_back: int = 90) -> List[Dict[str, Any]]:
        """Get voice improvement timeline for visualization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT voice_features, pronunciation_scores, created_at
            FROM voice_samples 
            WHERE user_id = ? AND created_at >= datetime('now', '-{} days')
            ORDER BY created_at ASC
        '''.format(days_back), (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        timeline = []
        for row in rows:
            features = VoiceFeatures(**json.loads(row[0]))
            scores = json.loads(row[1])
            
            timeline.append({
                'date': row[2],
                'pronunciation_clarity': features.pronunciation_clarity,
                'voice_quality': features.voice_quality_score,
                'speaking_rate': features.speaking_rate,
                'average_pronunciation_score': np.mean(list(scores.values())) if scores else 0,
                'sample_count': 1
            })
        
        return timeline
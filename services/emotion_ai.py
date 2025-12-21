"""
Emotion Recognition AI Service
Analyzes text and voice for emotional content and adapts responses accordingly
"""
import re
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class EmotionAnalysis:
    primary_emotion: str
    confidence: float
    emotions_detected: Dict[str, float]
    sentiment_score: float  # -1 to 1
    energy_level: str  # low, medium, high
    stress_indicators: List[str]
    suggested_response_tone: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'primary_emotion': self.primary_emotion,
            'confidence': self.confidence,
            'emotions_detected': self.emotions_detected,
            'sentiment_score': self.sentiment_score,
            'energy_level': self.energy_level,
            'stress_indicators': self.stress_indicators,
            'suggested_response_tone': self.suggested_response_tone
        }

@dataclass
class UserEmotionalProfile:
    user_id: str
    emotional_patterns: Dict[str, Any]
    stress_triggers: List[str]
    motivation_factors: List[str]
    preferred_interaction_style: str
    learning_mood_preferences: Dict[str, str]
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'emotional_patterns': self.emotional_patterns,
            'stress_triggers': self.stress_triggers,
            'motivation_factors': self.motivation_factors,
            'preferred_interaction_style': self.preferred_interaction_style,
            'learning_mood_preferences': self.learning_mood_preferences,
            'last_updated': self.last_updated.isoformat()
        }

class EmotionRecognitionAI:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
        
        # Emotion keywords and patterns
        self.emotion_patterns = {
            'happy': {
                'keywords': ['happy', 'joy', 'excited', 'great', 'awesome', 'wonderful', 'amazing', 'fantastic', 'love', 'perfect'],
                'patterns': [r'\b(yay|woohoo|yes!|excellent)\b', r'[!]{2,}', r'[😊😄😃🎉✨]'],
                'intensity_multipliers': {'!': 1.2, 'very': 1.3, 'so': 1.2, 'really': 1.3}
            },
            'sad': {
                'keywords': ['sad', 'depressed', 'down', 'upset', 'disappointed', 'hurt', 'crying', 'tears', 'lonely', 'empty'],
                'patterns': [r'\b(sigh|ugh|oh no)\b', r'[😢😭😞💔]'],
                'intensity_multipliers': {'very': 1.4, 'so': 1.3, 'really': 1.4, 'extremely': 1.5}
            },
            'angry': {
                'keywords': ['angry', 'mad', 'furious', 'annoyed', 'irritated', 'frustrated', 'hate', 'stupid', 'ridiculous'],
                'patterns': [r'\b(grr|argh|damn|wtf)\b', r'[😠😡🤬]', r'[A-Z]{3,}'],
                'intensity_multipliers': {'fucking': 1.8, 'damn': 1.3, 'really': 1.4}
            },
            'anxious': {
                'keywords': ['worried', 'nervous', 'anxious', 'scared', 'afraid', 'panic', 'stress', 'overwhelmed', 'tense'],
                'patterns': [r'\b(um|uh|er)\b', r'\.{3,}', r'[😰😨😱]'],
                'intensity_multipliers': {'very': 1.4, 'so': 1.3, 'really': 1.4}
            },
            'excited': {
                'keywords': ['excited', 'thrilled', 'pumped', 'energetic', 'motivated', 'ready', 'eager', 'can\'t wait'],
                'patterns': [r'[!]{2,}', r'\b(wow|omg|amazing)\b', r'[🚀⚡🔥💪]'],
                'intensity_multipliers': {'super': 1.5, 'really': 1.3, 'so': 1.2}
            },
            'tired': {
                'keywords': ['tired', 'exhausted', 'sleepy', 'drained', 'weary', 'fatigue', 'worn out'],
                'patterns': [r'\b(yawn|zzz)\b', r'[😴💤]'],
                'intensity_multipliers': {'very': 1.4, 'so': 1.3, 'extremely': 1.5}
            },
            'confused': {
                'keywords': ['confused', 'lost', 'don\'t understand', 'unclear', 'puzzled', 'bewildered'],
                'patterns': [r'\?{2,}', r'\b(huh|what|hmm)\b', r'[🤔😕]'],
                'intensity_multipliers': {'very': 1.3, 'so': 1.2, 'really': 1.3}
            }
        }
        
        # Response tone suggestions based on emotions
        self.response_tones = {
            'happy': 'enthusiastic',
            'sad': 'gentle_supportive',
            'angry': 'calm_understanding',
            'anxious': 'reassuring_patient',
            'excited': 'matching_energy',
            'tired': 'gentle_encouraging',
            'confused': 'clear_explanatory'
        }
    
    def init_database(self):
        """Initialize emotion tracking database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Emotion analysis history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_analysis (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                text_analyzed TEXT,
                voice_features TEXT,
                emotion_results TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User emotional profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_emotional_profiles (
                user_id TEXT PRIMARY KEY,
                emotional_patterns TEXT NOT NULL,
                stress_triggers TEXT,
                motivation_factors TEXT,
                preferred_interaction_style TEXT,
                learning_mood_preferences TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def analyze_text_emotion(self, text: str, user_id: str = None) -> EmotionAnalysis:
        """Analyze emotion from text input"""
        text_lower = text.lower()
        emotions_detected = {}
        
        # Analyze each emotion
        for emotion, data in self.emotion_patterns.items():
            score = 0.0
            
            # Check keywords
            for keyword in data['keywords']:
                if keyword in text_lower:
                    base_score = 0.3
                    
                    # Apply intensity multipliers
                    for multiplier, factor in data['intensity_multipliers'].items():
                        if multiplier in text_lower:
                            base_score *= factor
                    
                    score += base_score
            
            # Check patterns
            for pattern in data['patterns']:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches * 0.2
            
            # Normalize score
            emotions_detected[emotion] = min(score, 1.0)
        
        # Determine primary emotion
        primary_emotion = max(emotions_detected, key=emotions_detected.get) if emotions_detected else 'neutral'
        confidence = emotions_detected.get(primary_emotion, 0.0)
        
        # Calculate sentiment score
        positive_emotions = ['happy', 'excited']
        negative_emotions = ['sad', 'angry', 'anxious']
        
        positive_score = sum(emotions_detected.get(e, 0) for e in positive_emotions)
        negative_score = sum(emotions_detected.get(e, 0) for e in negative_emotions)
        
        sentiment_score = positive_score - negative_score
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Determine energy level
        high_energy_emotions = ['excited', 'angry', 'happy']
        low_energy_emotions = ['tired', 'sad']
        
        high_energy_score = sum(emotions_detected.get(e, 0) for e in high_energy_emotions)
        low_energy_score = sum(emotions_detected.get(e, 0) for e in low_energy_emotions)
        
        if high_energy_score > 0.5:
            energy_level = 'high'
        elif low_energy_score > 0.3:
            energy_level = 'low'
        else:
            energy_level = 'medium'
        
        # Identify stress indicators
        stress_indicators = []
        if emotions_detected.get('anxious', 0) > 0.3:
            stress_indicators.append('anxiety_detected')
        if emotions_detected.get('angry', 0) > 0.4:
            stress_indicators.append('anger_detected')
        if emotions_detected.get('tired', 0) > 0.5:
            stress_indicators.append('fatigue_detected')
        if len(re.findall(r'[A-Z]{3,}', text)) > 0:
            stress_indicators.append('caps_usage')
        
        # Suggest response tone
        suggested_tone = self.response_tones.get(primary_emotion, 'neutral_supportive')
        
        analysis = EmotionAnalysis(
            primary_emotion=primary_emotion,
            confidence=confidence,
            emotions_detected=emotions_detected,
            sentiment_score=sentiment_score,
            energy_level=energy_level,
            stress_indicators=stress_indicators,
            suggested_response_tone=suggested_tone
        )
        
        # Store analysis if user_id provided
        if user_id:
            self.store_emotion_analysis(user_id, text, analysis)
            self.update_user_emotional_profile(user_id, analysis)
        
        return analysis
    
    def analyze_voice_emotion(self, voice_features: Dict[str, Any], user_id: str = None) -> EmotionAnalysis:
        """Analyze emotion from voice features (pitch, tone, speed, etc.)"""
        # This is a simplified version - in production, you'd use advanced ML models
        emotions_detected = {}
        
        # Extract features
        pitch = voice_features.get('pitch', 0.5)  # 0-1 normalized
        energy = voice_features.get('energy', 0.5)
        speaking_rate = voice_features.get('speaking_rate', 0.5)
        voice_quality = voice_features.get('voice_quality', 'normal')
        
        # Analyze based on voice characteristics
        if pitch > 0.7 and energy > 0.6:
            emotions_detected['excited'] = 0.7
            emotions_detected['happy'] = 0.5
        elif pitch < 0.3 and energy < 0.4:
            emotions_detected['sad'] = 0.6
            emotions_detected['tired'] = 0.4
        elif energy > 0.8 and speaking_rate > 0.7:
            emotions_detected['angry'] = 0.6
            emotions_detected['excited'] = 0.3
        elif speaking_rate < 0.3:
            emotions_detected['tired'] = 0.5
            emotions_detected['sad'] = 0.3
        
        # Voice quality indicators
        if voice_quality == 'shaky':
            emotions_detected['anxious'] = 0.6
        elif voice_quality == 'monotone':
            emotions_detected['tired'] = 0.4
        
        # Determine primary emotion
        primary_emotion = max(emotions_detected, key=emotions_detected.get) if emotions_detected else 'neutral'
        confidence = emotions_detected.get(primary_emotion, 0.0)
        
        # Calculate other metrics similar to text analysis
        positive_score = emotions_detected.get('happy', 0) + emotions_detected.get('excited', 0)
        negative_score = emotions_detected.get('sad', 0) + emotions_detected.get('angry', 0)
        sentiment_score = positive_score - negative_score
        
        energy_level = 'high' if energy > 0.6 else 'low' if energy < 0.3 else 'medium'
        
        stress_indicators = []
        if emotions_detected.get('anxious', 0) > 0.4:
            stress_indicators.append('voice_anxiety')
        if speaking_rate > 0.8:
            stress_indicators.append('rapid_speech')
        if voice_quality == 'strained':
            stress_indicators.append('voice_strain')
        
        analysis = EmotionAnalysis(
            primary_emotion=primary_emotion,
            confidence=confidence,
            emotions_detected=emotions_detected,
            sentiment_score=sentiment_score,
            energy_level=energy_level,
            stress_indicators=stress_indicators,
            suggested_response_tone=self.response_tones.get(primary_emotion, 'neutral_supportive')
        )
        
        if user_id:
            self.store_emotion_analysis(user_id, None, analysis, voice_features)
            self.update_user_emotional_profile(user_id, analysis)
        
        return analysis
    
    def store_emotion_analysis(self, user_id: str, text: str = None, 
                             analysis: EmotionAnalysis = None, voice_features: Dict = None):
        """Store emotion analysis in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        analysis_id = f"emotion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"
        
        cursor.execute('''
            INSERT INTO emotion_analysis 
            (id, user_id, text_analyzed, voice_features, emotion_results)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            analysis_id,
            user_id,
            text,
            json.dumps(voice_features) if voice_features else None,
            json.dumps(analysis.to_dict())
        ))
        
        conn.commit()
        conn.close()
    
    def update_user_emotional_profile(self, user_id: str, analysis: EmotionAnalysis):
        """Update user's emotional profile based on new analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get existing profile
        cursor.execute('''
            SELECT * FROM user_emotional_profiles WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing profile
            existing_patterns = json.loads(row[1])
            existing_triggers = json.loads(row[2]) if row[2] else []
            existing_motivators = json.loads(row[3]) if row[3] else []
            
            # Update emotional patterns (running average)
            for emotion, score in analysis.emotions_detected.items():
                if emotion in existing_patterns:
                    existing_patterns[emotion] = (existing_patterns[emotion] + score) / 2
                else:
                    existing_patterns[emotion] = score
            
            # Update stress triggers
            for trigger in analysis.stress_indicators:
                if trigger not in existing_triggers:
                    existing_triggers.append(trigger)
            
            # Update motivators (positive emotions)
            if analysis.sentiment_score > 0.3:
                motivator = f"{analysis.primary_emotion}_context"
                if motivator not in existing_motivators:
                    existing_motivators.append(motivator)
            
            cursor.execute('''
                UPDATE user_emotional_profiles 
                SET emotional_patterns = ?, stress_triggers = ?, motivation_factors = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                json.dumps(existing_patterns),
                json.dumps(existing_triggers),
                json.dumps(existing_motivators),
                user_id
            ))
        else:
            # Create new profile
            initial_patterns = analysis.emotions_detected
            initial_triggers = analysis.stress_indicators
            initial_motivators = [f"{analysis.primary_emotion}_context"] if analysis.sentiment_score > 0 else []
            
            cursor.execute('''
                INSERT INTO user_emotional_profiles 
                (user_id, emotional_patterns, stress_triggers, motivation_factors,
                 preferred_interaction_style, learning_mood_preferences)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                json.dumps(initial_patterns),
                json.dumps(initial_triggers),
                json.dumps(initial_motivators),
                'adaptive',
                json.dumps({'default': 'supportive'})
            ))
        
        conn.commit()
        conn.close()
    
    def get_user_emotional_profile(self, user_id: str) -> Optional[UserEmotionalProfile]:
        """Get user's emotional profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_emotional_profiles WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return UserEmotionalProfile(
                user_id=row[0],
                emotional_patterns=json.loads(row[1]),
                stress_triggers=json.loads(row[2]) if row[2] else [],
                motivation_factors=json.loads(row[3]) if row[3] else [],
                preferred_interaction_style=row[4],
                learning_mood_preferences=json.loads(row[5]) if row[5] else {},
                last_updated=datetime.fromisoformat(row[6])
            )
        return None
    
    def adapt_response_for_emotion(self, base_response: str, emotion_analysis: EmotionAnalysis, 
                                 user_profile: UserEmotionalProfile = None) -> str:
        """Adapt AI response based on detected emotion"""
        tone = emotion_analysis.suggested_response_tone
        
        # Response adaptations based on tone
        adaptations = {
            'enthusiastic': {
                'prefix': "That's fantastic! ",
                'style': 'exclamation_marks',
                'encouragement': "You're doing amazing! "
            },
            'gentle_supportive': {
                'prefix': "I understand how you're feeling. ",
                'style': 'soft_language',
                'encouragement': "Take your time, you're doing great. "
            },
            'calm_understanding': {
                'prefix': "I hear you. ",
                'style': 'measured_tone',
                'encouragement': "Let's work through this together. "
            },
            'reassuring_patient': {
                'prefix': "Don't worry, ",
                'style': 'patient_explanation',
                'encouragement': "We'll take this step by step. "
            },
            'matching_energy': {
                'prefix': "Yes! ",
                'style': 'high_energy',
                'encouragement': "Let's keep this momentum going! "
            },
            'gentle_encouraging': {
                'prefix': "I know you might be tired, but ",
                'style': 'gentle_push',
                'encouragement': "You're stronger than you think. "
            },
            'clear_explanatory': {
                'prefix': "Let me explain this clearly: ",
                'style': 'step_by_step',
                'encouragement': "Don't worry, this will make sense soon. "
            }
        }
        
        adaptation = adaptations.get(tone, adaptations['gentle_supportive'])
        
        # Apply adaptations
        adapted_response = adaptation['prefix'] + base_response
        
        # Add encouragement if user seems stressed
        if emotion_analysis.stress_indicators:
            adapted_response += " " + adaptation['encouragement']
        
        # Adjust based on energy level
        if emotion_analysis.energy_level == 'low':
            adapted_response = adapted_response.replace('!', '.')
            adapted_response += " Remember, learning is a journey, not a race."
        elif emotion_analysis.energy_level == 'high':
            adapted_response += "!"
        
        return adapted_response
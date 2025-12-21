"""
Dream Journal Integration Service
Unique psychological approach to language learning through dream recording and analysis
"""
import json
import sqlite3
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class DreamEntry:
    id: str
    user_id: str
    dream_text: str
    language: str
    emotion_detected: Optional[str]
    keywords_extracted: List[str]
    learning_opportunities: List[str]
    vocabulary_suggestions: List[str]
    cultural_insights: List[str]
    voice_recording_url: Optional[str]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'dream_text': self.dream_text,
            'language': self.language,
            'emotion_detected': self.emotion_detected,
            'keywords_extracted': self.keywords_extracted,
            'learning_opportunities': self.learning_opportunities,
            'vocabulary_suggestions': self.vocabulary_suggestions,
            'cultural_insights': self.cultural_insights,
            'voice_recording_url': self.voice_recording_url,
            'created_at': self.created_at.isoformat()
        }

@dataclass
class DreamAnalysis:
    themes: List[str]
    emotions: List[str]
    characters: List[str]
    locations: List[str]
    actions: List[str]
    objects: List[str]
    language_complexity: str  # beginner, intermediate, advanced
    subconscious_concerns: List[str]
    learning_readiness_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'themes': self.themes,
            'emotions': self.emotions,
            'characters': self.characters,
            'locations': self.locations,
            'actions': self.actions,
            'objects': self.objects,
            'language_complexity': self.language_complexity,
            'subconscious_concerns': self.subconscious_concerns,
            'learning_readiness_score': self.learning_readiness_score
        }

@dataclass
class DreamLearningInsight:
    user_id: str
    insight_type: str  # vocabulary, grammar, cultural, emotional
    insight_text: str
    confidence_score: float
    suggested_exercises: List[str]
    related_dreams: List[str]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'insight_type': self.insight_type,
            'insight_text': self.insight_text,
            'confidence_score': self.confidence_score,
            'suggested_exercises': self.suggested_exercises,
            'related_dreams': self.related_dreams,
            'created_at': self.created_at.isoformat()
        }

class DreamJournalService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
        
        # Dream analysis patterns and keywords
        self.dream_patterns = {
            'themes': {
                'adventure': ['journey', 'travel', 'explore', 'adventure', 'quest', 'mountain', 'forest', 'ocean'],
                'relationships': ['family', 'friend', 'love', 'partner', 'mother', 'father', 'child', 'wedding'],
                'work_school': ['office', 'school', 'teacher', 'boss', 'exam', 'presentation', 'meeting', 'study'],
                'fear_anxiety': ['chase', 'fall', 'lost', 'dark', 'monster', 'danger', 'scared', 'panic'],
                'achievement': ['success', 'win', 'award', 'celebrate', 'accomplish', 'graduate', 'promotion'],
                'transformation': ['change', 'grow', 'become', 'transform', 'new', 'different', 'evolve']
            },
            'emotions': {
                'positive': ['happy', 'joy', 'excited', 'peaceful', 'love', 'content', 'proud', 'grateful'],
                'negative': ['sad', 'angry', 'scared', 'worried', 'frustrated', 'lonely', 'disappointed'],
                'neutral': ['curious', 'confused', 'surprised', 'calm', 'focused', 'determined']
            },
            'characters': {
                'family': ['mother', 'father', 'sister', 'brother', 'grandmother', 'grandfather', 'aunt', 'uncle'],
                'social': ['friend', 'teacher', 'boss', 'colleague', 'neighbor', 'stranger', 'celebrity'],
                'symbolic': ['child', 'old man', 'wise woman', 'guide', 'shadow', 'angel', 'animal']
            }
        }
        
        # Language-specific vocabulary for dreams
        self.dream_vocabulary = {
            'en': {
                'basic': ['sleep', 'dream', 'night', 'bed', 'wake up', 'remember', 'forget'],
                'emotions': ['feel', 'emotion', 'happy', 'sad', 'scared', 'excited', 'peaceful'],
                'actions': ['run', 'fly', 'fall', 'chase', 'hide', 'search', 'find', 'lose'],
                'places': ['home', 'school', 'work', 'forest', 'ocean', 'mountain', 'city', 'room']
            },
            'kn': {
                'basic': ['ನಿದ್ರೆ', 'ಕನಸು', 'ರಾತ್ರಿ', 'ಹಾಸಿಗೆ', 'ಎಚ್ಚರ', 'ನೆನಪು', 'ಮರೆ'],
                'emotions': ['ಭಾವನೆ', 'ಸಂತೋಷ', 'ದುಃಖ', 'ಭಯ', 'ಉತ್ಸಾಹ', 'ಶಾಂತಿ'],
                'actions': ['ಓಡು', 'ಹಾರು', 'ಬೀಳು', 'ಹಿಂಬಾಲಿಸು', 'ಅಡಗು', 'ಹುಡುಕು'],
                'places': ['ಮನೆ', 'ಶಾಲೆ', 'ಕೆಲಸ', 'ಕಾಡು', 'ಸಮುದ್ರ', 'ಪರ್ವತ', 'ನಗರ']
            },
            'te': {
                'basic': ['నిద్ర', 'కల', 'రాత్రి', 'మంచం', 'మేల్కొను', 'గుర్తు', 'మర్చిపో'],
                'emotions': ['భావన', 'సంతోషం', 'దుఃఖం', 'భయం', 'ఉత్సాహం', 'శాంతి'],
                'actions': ['పరుగు', 'ఎగురు', 'పడు', 'వెంబడించు', 'దాచు', 'వెతుకు'],
                'places': ['ఇల్లు', 'పాఠశాల', 'పని', 'అడవి', 'సముద్రం', 'పర్వతం', 'నగరం']
            }
        }
    
    def init_database(self):
        """Initialize dream journal database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Dream entries table (enhanced)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dream_entries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                dream_text TEXT NOT NULL,
                language TEXT NOT NULL,
                emotion_detected TEXT,
                keywords_extracted TEXT,
                learning_opportunities TEXT,
                vocabulary_suggestions TEXT,
                cultural_insights TEXT,
                voice_recording_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Dream analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dream_analysis (
                id TEXT PRIMARY KEY,
                dream_entry_id TEXT NOT NULL,
                analysis_data TEXT NOT NULL,
                learning_insights TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dream_entry_id) REFERENCES dream_entries (id)
            )
        ''')
        
        # Dream learning insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dream_learning_insights (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                insight_text TEXT NOT NULL,
                confidence_score REAL,
                suggested_exercises TEXT,
                related_dreams TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User dream patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_dream_patterns (
                user_id TEXT PRIMARY KEY,
                recurring_themes TEXT,
                emotional_patterns TEXT,
                vocabulary_preferences TEXT,
                learning_style_indicators TEXT,
                subconscious_language_exposure TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_dream_entry(self, user_id: str, dream_text: str, language: str, 
                       voice_recording_url: str = None) -> Optional[str]:
        """Add a new dream entry and analyze it"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            entry_id = f"dream_{secrets.token_urlsafe(12)}"
            
            # Analyze the dream
            analysis = self.analyze_dream_content(dream_text, language)
            emotion = self.detect_dream_emotion(dream_text)
            keywords = self.extract_dream_keywords(dream_text, language)
            learning_opportunities = self.identify_learning_opportunities(dream_text, language)
            vocabulary_suggestions = self.suggest_vocabulary_from_dream(dream_text, language)
            cultural_insights = self.extract_cultural_insights(dream_text, language)
            
            cursor.execute('''
                INSERT INTO dream_entries 
                (id, user_id, dream_text, language, emotion_detected, keywords_extracted,
                 learning_opportunities, vocabulary_suggestions, cultural_insights, voice_recording_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_id, user_id, dream_text, language, emotion,
                json.dumps(keywords), json.dumps(learning_opportunities),
                json.dumps(vocabulary_suggestions), json.dumps(cultural_insights),
                voice_recording_url
            ))
            
            # Store detailed analysis
            analysis_id = f"analysis_{secrets.token_urlsafe(12)}"
            cursor.execute('''
                INSERT INTO dream_analysis (id, dream_entry_id, analysis_data)
                VALUES (?, ?, ?)
            ''', (analysis_id, entry_id, json.dumps(analysis.to_dict())))
            
            conn.commit()
            
            # Update user dream patterns
            self.update_user_dream_patterns(user_id, analysis, keywords)
            
            # Generate learning insights
            self.generate_learning_insights(user_id, entry_id, analysis, dream_text)
            
            return entry_id
            
        except Exception as e:
            print(f"Error adding dream entry: {e}")
            return None
        finally:
            conn.close()
    
    def analyze_dream_content(self, dream_text: str, language: str) -> DreamAnalysis:
        """Analyze dream content for themes, emotions, and learning opportunities"""
        text_lower = dream_text.lower()
        
        # Extract themes
        themes = []
        for theme, keywords in self.dream_patterns['themes'].items():
            if any(keyword in text_lower for keyword in keywords):
                themes.append(theme)
        
        # Extract emotions
        emotions = []
        for emotion_type, keywords in self.dream_patterns['emotions'].items():
            if any(keyword in text_lower for keyword in keywords):
                emotions.extend([kw for kw in keywords if kw in text_lower])
        
        # Extract characters
        characters = []
        for char_type, keywords in self.dream_patterns['characters'].items():
            characters.extend([kw for kw in keywords if kw in text_lower])
        
        # Extract locations (simple pattern matching)
        location_patterns = [
            r'\b(in|at|to)\s+(\w+)\b',
            r'\b(home|school|work|office|park|beach|forest|mountain)\b'
        ]
        locations = []
        for pattern in location_patterns:
            matches = re.findall(pattern, text_lower)
            locations.extend([match[1] if isinstance(match, tuple) else match for match in matches])
        
        # Extract actions (verbs)
        action_patterns = [
            r'\b(run|walk|fly|fall|jump|climb|swim|drive|dance|sing|speak|talk)\b',
            r'\b(was|were)\s+(\w+ing)\b'
        ]
        actions = []
        for pattern in action_patterns:
            matches = re.findall(pattern, text_lower)
            actions.extend([match[1] if isinstance(match, tuple) else match for match in matches])
        
        # Extract objects
        object_patterns = [
            r'\b(car|house|book|phone|computer|tree|flower|animal|dog|cat)\b'
        ]
        objects = []
        for pattern in object_patterns:
            objects.extend(re.findall(pattern, text_lower))
        
        # Determine language complexity
        word_count = len(dream_text.split())
        unique_words = len(set(dream_text.lower().split()))
        complexity_ratio = unique_words / word_count if word_count > 0 else 0
        
        if word_count < 50 or complexity_ratio < 0.6:
            language_complexity = 'beginner'
        elif word_count < 150 or complexity_ratio < 0.8:
            language_complexity = 'intermediate'
        else:
            language_complexity = 'advanced'
        
        # Identify subconscious concerns
        concern_keywords = {
            'performance_anxiety': ['exam', 'test', 'fail', 'late', 'unprepared', 'forgot'],
            'social_anxiety': ['embarrassed', 'naked', 'laugh', 'judge', 'alone', 'rejected'],
            'control_issues': ['lost', 'can\'t find', 'broken', 'stuck', 'trapped'],
            'change_fear': ['moving', 'leaving', 'ending', 'goodbye', 'different']
        }
        
        subconscious_concerns = []
        for concern, keywords in concern_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                subconscious_concerns.append(concern)
        
        # Calculate learning readiness score
        positive_emotions = ['happy', 'excited', 'peaceful', 'confident']
        negative_emotions = ['scared', 'worried', 'frustrated', 'sad']
        
        positive_count = sum(1 for emotion in positive_emotions if emotion in text_lower)
        negative_count = sum(1 for emotion in negative_emotions if emotion in text_lower)
        
        learning_readiness_score = max(0.0, min(1.0, (positive_count - negative_count + 2) / 4))
        
        return DreamAnalysis(
            themes=themes,
            emotions=emotions,
            characters=characters,
            locations=locations,
            actions=actions,
            objects=objects,
            language_complexity=language_complexity,
            subconscious_concerns=subconscious_concerns,
            learning_readiness_score=learning_readiness_score
        )
    
    def detect_dream_emotion(self, dream_text: str) -> str:
        """Detect primary emotion in dream"""
        text_lower = dream_text.lower()
        emotion_scores = {}
        
        for emotion_type, keywords in self.dream_patterns['emotions'].items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion_type] = score
        
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        return 'neutral'
    
    def extract_dream_keywords(self, dream_text: str, language: str) -> List[str]:
        """Extract relevant keywords from dream text"""
        text_lower = dream_text.lower()
        keywords = []
        
        # Get language-specific vocabulary
        vocab = self.dream_vocabulary.get(language, self.dream_vocabulary['en'])
        
        for category, words in vocab.items():
            for word in words:
                if word.lower() in text_lower:
                    keywords.append(word)
        
        # Extract proper nouns (names, places)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', dream_text)
        keywords.extend(proper_nouns)
        
        return list(set(keywords))  # Remove duplicates
    
    def identify_learning_opportunities(self, dream_text: str, language: str) -> List[str]:
        """Identify learning opportunities from dream content"""
        opportunities = []
        analysis = self.analyze_dream_content(dream_text, language)
        
        # Theme-based opportunities
        if 'adventure' in analysis.themes:
            opportunities.append("Practice travel and adventure vocabulary")
            opportunities.append("Learn directional and movement verbs")
        
        if 'relationships' in analysis.themes:
            opportunities.append("Study family and relationship terms")
            opportunities.append("Practice expressing emotions and feelings")
        
        if 'work_school' in analysis.themes:
            opportunities.append("Learn professional and academic vocabulary")
            opportunities.append("Practice formal communication skills")
        
        # Emotion-based opportunities
        if analysis.emotions:
            opportunities.append("Practice expressing emotions and feelings")
            opportunities.append("Learn emotional vocabulary and expressions")
        
        # Complexity-based opportunities
        if analysis.language_complexity == 'beginner':
            opportunities.append("Focus on basic vocabulary expansion")
            opportunities.append("Practice simple sentence structures")
        elif analysis.language_complexity == 'intermediate':
            opportunities.append("Work on complex sentence structures")
            opportunities.append("Practice storytelling and narrative skills")
        else:
            opportunities.append("Explore advanced vocabulary and idioms")
            opportunities.append("Practice creative writing and expression")
        
        return opportunities
    
    def suggest_vocabulary_from_dream(self, dream_text: str, language: str) -> List[str]:
        """Suggest vocabulary words based on dream content"""
        suggestions = []
        analysis = self.analyze_dream_content(dream_text, language)
        
        # Get base vocabulary for the language
        vocab = self.dream_vocabulary.get(language, self.dream_vocabulary['en'])
        
        # Suggest words based on themes
        for theme in analysis.themes:
            if theme == 'adventure':
                suggestions.extend(['journey', 'explore', 'discover', 'path', 'destination'])
            elif theme == 'relationships':
                suggestions.extend(['connect', 'bond', 'trust', 'support', 'communicate'])
            elif theme == 'fear_anxiety':
                suggestions.extend(['courage', 'brave', 'overcome', 'face', 'conquer'])
        
        # Suggest words based on actions mentioned
        for action in analysis.actions:
            if action in ['run', 'running']:
                suggestions.extend(['sprint', 'jog', 'race', 'marathon', 'speed'])
            elif action in ['fly', 'flying']:
                suggestions.extend(['soar', 'glide', 'hover', 'wings', 'altitude'])
        
        # Language-specific suggestions
        if language == 'en':
            suggestions.extend(['subconscious', 'imagination', 'symbolism', 'metaphor'])
        elif language == 'kn':
            suggestions.extend(['ಅರಿವಿಲ್ಲದ', 'ಕಲ್ಪನೆ', 'ಸಂಕೇತ', 'ರೂಪಕ'])
        elif language == 'te':
            suggestions.extend(['అపస్మారక', 'కల్పన', 'సంకేతం', 'రూపకం'])
        
        return list(set(suggestions))[:10]  # Return unique suggestions, max 10
    
    def extract_cultural_insights(self, dream_text: str, language: str) -> List[str]:
        """Extract cultural insights from dream content"""
        insights = []
        text_lower = dream_text.lower()
        
        # Cultural elements detection
        cultural_elements = {
            'family_values': ['family', 'parents', 'children', 'respect', 'tradition'],
            'spiritual_beliefs': ['temple', 'prayer', 'god', 'blessing', 'ritual'],
            'social_customs': ['wedding', 'festival', 'celebration', 'community', 'gathering'],
            'food_culture': ['food', 'cooking', 'meal', 'feast', 'recipe'],
            'nature_connection': ['tree', 'river', 'mountain', 'earth', 'sky']
        }
        
        for culture_type, keywords in cultural_elements.items():
            if any(keyword in text_lower for keyword in keywords):
                if culture_type == 'family_values':
                    insights.append("Dreams reflect strong family connections - common in collectivist cultures")
                elif culture_type == 'spiritual_beliefs':
                    insights.append("Spiritual elements suggest importance of faith and tradition")
                elif culture_type == 'social_customs':
                    insights.append("Social gatherings indicate community-oriented mindset")
                elif culture_type == 'food_culture':
                    insights.append("Food in dreams often represents nurturing and cultural identity")
                elif culture_type == 'nature_connection':
                    insights.append("Nature elements suggest harmony and environmental awareness")
        
        # Language-specific cultural insights
        if language == 'kn':
            insights.append("Kannada dreams often reflect Karnataka's rich cultural heritage")
        elif language == 'te':
            insights.append("Telugu dreams may include elements of Andhra/Telangana traditions")
        
        return insights
    
    def update_user_dream_patterns(self, user_id: str, analysis: DreamAnalysis, keywords: List[str]):
        """Update user's dream patterns for personalized insights"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get existing patterns
            cursor.execute('''
                SELECT * FROM user_dream_patterns WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            
            if row:
                # Update existing patterns
                recurring_themes = json.loads(row[1]) if row[1] else {}
                emotional_patterns = json.loads(row[2]) if row[2] else {}
                vocabulary_preferences = json.loads(row[3]) if row[3] else {}
                
                # Update themes
                for theme in analysis.themes:
                    recurring_themes[theme] = recurring_themes.get(theme, 0) + 1
                
                # Update emotions
                for emotion in analysis.emotions:
                    emotional_patterns[emotion] = emotional_patterns.get(emotion, 0) + 1
                
                # Update vocabulary
                for keyword in keywords:
                    vocabulary_preferences[keyword] = vocabulary_preferences.get(keyword, 0) + 1
                
                cursor.execute('''
                    UPDATE user_dream_patterns 
                    SET recurring_themes = ?, emotional_patterns = ?, vocabulary_preferences = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (
                    json.dumps(recurring_themes),
                    json.dumps(emotional_patterns),
                    json.dumps(vocabulary_preferences),
                    user_id
                ))
            else:
                # Create new patterns
                recurring_themes = {theme: 1 for theme in analysis.themes}
                emotional_patterns = {emotion: 1 for emotion in analysis.emotions}
                vocabulary_preferences = {keyword: 1 for keyword in keywords}
                
                cursor.execute('''
                    INSERT INTO user_dream_patterns 
                    (user_id, recurring_themes, emotional_patterns, vocabulary_preferences,
                     learning_style_indicators, subconscious_language_exposure)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    json.dumps(recurring_themes),
                    json.dumps(emotional_patterns),
                    json.dumps(vocabulary_preferences),
                    json.dumps({'complexity_preference': analysis.language_complexity}),
                    json.dumps({'readiness_score': analysis.learning_readiness_score})
                ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error updating dream patterns: {e}")
        finally:
            conn.close()
    
    def generate_learning_insights(self, user_id: str, dream_entry_id: str, 
                                 analysis: DreamAnalysis, dream_text: str):
        """Generate personalized learning insights from dream analysis"""
        insights = []
        
        # Vocabulary insights
        if analysis.language_complexity == 'beginner':
            insights.append(DreamLearningInsight(
                user_id=user_id,
                insight_type='vocabulary',
                insight_text="Your dreams use simple vocabulary - perfect for building foundational language skills",
                confidence_score=0.8,
                suggested_exercises=['Basic vocabulary flashcards', 'Simple sentence construction'],
                related_dreams=[dream_entry_id],
                created_at=datetime.now()
            ))
        
        # Emotional insights
        if analysis.emotions:
            dominant_emotion = max(set(analysis.emotions), key=analysis.emotions.count)
            insights.append(DreamLearningInsight(
                user_id=user_id,
                insight_type='emotional',
                insight_text=f"Your dreams often feature {dominant_emotion} emotions - practice expressing these feelings",
                confidence_score=0.7,
                suggested_exercises=[f'Emotional vocabulary for {dominant_emotion}', 'Feeling expression practice'],
                related_dreams=[dream_entry_id],
                created_at=datetime.now()
            ))
        
        # Cultural insights
        if 'family' in dream_text.lower() or 'home' in dream_text.lower():
            insights.append(DreamLearningInsight(
                user_id=user_id,
                insight_type='cultural',
                insight_text="Family themes in dreams suggest learning family-related vocabulary would be meaningful",
                confidence_score=0.6,
                suggested_exercises=['Family relationship terms', 'Home and household vocabulary'],
                related_dreams=[dream_entry_id],
                created_at=datetime.now()
            ))
        
        # Store insights
        self._store_learning_insights(insights)
    
    def _store_learning_insights(self, insights: List[DreamLearningInsight]):
        """Store learning insights in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for insight in insights:
                insight_id = f"insight_{secrets.token_urlsafe(12)}"
                cursor.execute('''
                    INSERT INTO dream_learning_insights 
                    (id, user_id, insight_type, insight_text, confidence_score,
                     suggested_exercises, related_dreams)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    insight_id,
                    insight.user_id,
                    insight.insight_type,
                    insight.insight_text,
                    insight.confidence_score,
                    json.dumps(insight.suggested_exercises),
                    json.dumps(insight.related_dreams)
                ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error storing learning insights: {e}")
        finally:
            conn.close()
    
    def get_user_dream_entries(self, user_id: str, limit: int = 20, offset: int = 0) -> List[DreamEntry]:
        """Get user's dream entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM dream_entries 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for row in rows:
            entries.append(DreamEntry(
                id=row[0],
                user_id=row[1],
                dream_text=row[2],
                language=row[3],
                emotion_detected=row[4],
                keywords_extracted=json.loads(row[5]) if row[5] else [],
                learning_opportunities=json.loads(row[6]) if row[6] else [],
                vocabulary_suggestions=json.loads(row[7]) if row[7] else [],
                cultural_insights=json.loads(row[8]) if row[8] else [],
                voice_recording_url=row[9],
                created_at=datetime.fromisoformat(row[10])
            ))
        
        return entries
    
    def get_user_learning_insights(self, user_id: str, insight_type: str = None) -> List[DreamLearningInsight]:
        """Get user's learning insights from dreams"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if insight_type:
            cursor.execute('''
                SELECT * FROM dream_learning_insights 
                WHERE user_id = ? AND insight_type = ?
                ORDER BY created_at DESC
            ''', (user_id, insight_type))
        else:
            cursor.execute('''
                SELECT * FROM dream_learning_insights 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        insights = []
        for row in rows:
            insights.append(DreamLearningInsight(
                user_id=row[1],
                insight_type=row[2],
                insight_text=row[3],
                confidence_score=row[4],
                suggested_exercises=json.loads(row[5]) if row[5] else [],
                related_dreams=json.loads(row[6]) if row[6] else [],
                created_at=datetime.fromisoformat(row[7])
            ))
        
        return insights
    
    def get_dream_statistics(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get dream journal statistics for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get dream count
        cursor.execute('''
            SELECT COUNT(*) FROM dream_entries 
            WHERE user_id = ? AND created_at >= datetime('now', '-{} days')
        '''.format(days_back), (user_id,))
        
        dream_count = cursor.fetchone()[0]
        
        # Get most common themes
        cursor.execute('''
            SELECT keywords_extracted FROM dream_entries 
            WHERE user_id = ? AND created_at >= datetime('now', '-{} days')
        '''.format(days_back), (user_id,))
        
        all_keywords = []
        for row in cursor.fetchall():
            if row[0]:
                all_keywords.extend(json.loads(row[0]))
        
        # Count keyword frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        most_common_themes = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Get emotional patterns
        cursor.execute('''
            SELECT emotion_detected FROM dream_entries 
            WHERE user_id = ? AND emotion_detected IS NOT NULL 
            AND created_at >= datetime('now', '-{} days')
        '''.format(days_back), (user_id,))
        
        emotions = [row[0] for row in cursor.fetchall()]
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        conn.close()
        
        return {
            'total_dreams': dream_count,
            'most_common_themes': most_common_themes,
            'emotional_patterns': emotion_counts,
            'average_dreams_per_week': dream_count * 7 / days_back,
            'learning_insights_generated': len(self.get_user_learning_insights(user_id))
        }
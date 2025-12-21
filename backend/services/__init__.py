"""
KeLiva Services
Core business logic and AI services
"""
from .grammar_guardian import GrammarGuardian, GrammarError, GrammarAnalysis
from .polyglot_engine import PolyglotEngine, Language, LanguageDetectionResult
from .tts_service import TTSService, TTSConfig, AudioChunk

__all__ = [
    "GrammarGuardian",
    "GrammarError", 
    "GrammarAnalysis",
    "PolyglotEngine",
    "Language",
    "LanguageDetectionResult",
    "TTSService",
    "TTSConfig",
    "AudioChunk"
]

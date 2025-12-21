/**
 * Hooks exports
 * Centralized export for all custom hooks
 */

export { useApi } from './useApi';
export { useGrammarCheck } from './useGrammarCheck';
export type { GrammarError, GrammarCheckResponse } from './useGrammarCheck';
export { useChatMessage } from './useChatMessage';
export type { ChatMessageRequest, ChatMessageResponse } from './useChatMessage';
export { useVoiceChat } from './useVoiceChat';
export type { VoiceChatMessage, UseVoiceChatOptions, UseVoiceChatReturn } from './useVoiceChat';
export { useOnlineStatus } from './useOnlineStatus';

# Keliva Mobile App Development Plan

## Project Overview
Convert the existing Keliva web application into a fully functional mobile APK with local AI capabilities, featuring chat and voice conversation functionality that works completely offline.

## Core Requirements
- **Same features as web version**: Chat interface + Voice conversation
- **Fully local operation**: No backend dependency for mobile
- **Direct APK distribution**: Host on server for direct download
- **Local AI Model**: Llama 3.1 8B Instruct for high-quality responses
- **Offline functionality**: Complete app works without internet

## Technical Architecture

### Frontend Stack
- **Base**: Existing React + TypeScript codebase
- **Mobile Wrapper**: Capacitor (converts web app to native)
- **UI Framework**: Current React components (mobile-optimized)
- **Build Tool**: Vite (existing setup)

### AI & Processing
- **Local LLM**: Llama 3.1 8B Instruct (~4.5GB)
- **Model Format**: GGUF (optimized for mobile)
- **Quantization**: Q4_K_M (balance of size/quality)
- **Runtime Engine**: llama.cpp (C++ inference engine)
- **Integration**: WebAssembly or React Native bindings

### Voice Features
- **Speech Recognition**: Android native Web Speech API
- **Text-to-Speech**: Android native TTS engine
- **Audio Processing**: Real-time voice conversation flow
- **Voice UI**: Same interface as web version

### Data Storage
- **Database**: SQLite (built into mobile)
- **Conversation History**: Local storage only
- **User Preferences**: Device storage
- **Model Storage**: App bundle (~4.5GB for LLM)

## Development Phases

### Phase 1: Mobile App Foundation (Week 1)
**Objective**: Convert web app to mobile APK

**Tasks**:
1. **Setup Capacitor**
   ```bash
   npm install @capacitor/core @capacitor/cli
   npm install @capacitor/android
   npx cap init keliva-mobile com.keliva.app
   ```

2. **Configure for Mobile**
   - Update `capacitor.config.ts`
   - Configure Android permissions
   - Setup mobile-specific styling

3. **Build & Test Basic APK**
   ```bash
   npm run build
   npx cap add android
   npx cap sync
   npx cap open android
   ```

4. **Mobile UI Optimization**
   - Touch-friendly interface
   - Mobile responsive design
   - Native navigation feel

**Deliverable**: Basic mobile APK with web functionality

### Phase 2: Local AI Integration (Week 2)
**Objective**: Replace API calls with local Llama 3.1 8B model

**Tasks**:
1. **Setup LLM Runtime**
   - Install llama.cpp for mobile
   - Configure WASM bindings
   - Setup model loading system

2. **Download & Integrate Model**
   - Download Llama 3.1 8B GGUF (Q4_K_M)
   - Bundle with APK or download on first run
   - Implement model initialization

3. **Replace API Calls**
   - Create local inference service
   - Replace backend API calls with local model
   - Implement conversation context management

4. **Performance Optimization**
   - Memory management for 4.5GB model
   - Inference speed optimization
   - Battery usage optimization

**Deliverable**: Mobile app with local AI responses

### Phase 3: Voice Features Implementation (Week 3)
**Objective**: Add voice conversation capabilities

**Tasks**:
1. **Speech Recognition Setup**
   ```javascript
   // Android Web Speech API integration
   const recognition = new webkitSpeechRecognition();
   recognition.continuous = true;
   recognition.interimResults = true;
   ```

2. **Text-to-Speech Integration**
   ```javascript
   // Android TTS integration
   const utterance = new SpeechSynthesisUtterance(text);
   speechSynthesis.speak(utterance);
   ```

3. **Voice Conversation Flow**
   - Real-time voice input processing
   - Seamless voice-to-text-to-AI-to-speech pipeline
   - Voice conversation UI (same as web)

4. **Voice Optimizations**
   - Background voice processing
   - Noise cancellation (if available)
   - Voice activity detection

**Deliverable**: Full voice conversation functionality

### Phase 4: Local Storage & Offline Features (Week 4)
**Objective**: Complete offline functionality

**Tasks**:
1. **SQLite Database Setup**
   ```sql
   CREATE TABLE conversations (
     id INTEGER PRIMARY KEY,
     message TEXT,
     response TEXT,
     timestamp DATETIME,
     is_voice BOOLEAN
   );
   ```

2. **Conversation Management**
   - Save all conversations locally
   - Conversation history UI
   - Search through conversations
   - Export/backup conversations

3. **App State Management**
   - Offline-first design
   - Local preferences storage
   - App settings management

4. **Performance & Polish**
   - App startup optimization
   - Memory leak prevention
   - UI/UX polish for mobile

**Deliverable**: Complete offline mobile app

### Phase 5: APK Distribution Setup (Week 5)
**Objective**: Setup direct APK download system

**Tasks**:
1. **APK Generation & Signing**
   ```bash
   # Generate signed APK
   ./gradlew assembleRelease
   # Sign APK with keystore
   jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore keliva.keystore app-release-unsigned.apk keliva
   ```

2. **Server Setup for APK Hosting**
   - Add APK hosting to existing backend
   - Create download endpoint
   - Version management system

3. **Download Page Creation**
   ```html
   <div class="mobile-download">
     <h2>Download Keliva Mobile App</h2>
     <a href="/downloads/keliva-app-v1.0.apk" 
        download="keliva-app.apk"
        class="download-btn">
       📱 Download Android App (APK)
     </a>
     <p>Size: ~5GB | Version: 1.0.0 | Offline AI Included</p>
   </div>
   ```

4. **User Installation Guide**
   - Step-by-step installation instructions
   - Android security settings guide
   - Troubleshooting documentation

**Deliverable**: Live APK download system

## Technical Specifications

### Mobile App Features
- ✅ **Chat Interface**: Same UI as web version
- ✅ **Voice Conversation**: Real-time voice chat
- ✅ **Local AI**: Llama 3.1 8B for responses
- ✅ **Offline Operation**: No internet required
- ✅ **Conversation History**: Local SQLite storage
- ✅ **Fast Responses**: 1-3 second AI inference
- ✅ **Native Feel**: Capacitor native wrapper

### System Requirements
- **Android Version**: 7.0+ (API level 24+)
- **RAM**: 6GB+ recommended (4GB minimum)
- **Storage**: 8GB free space (5GB for app + model)
- **Processor**: ARM64 or x86_64

### Performance Targets
- **App Startup**: < 3 seconds
- **AI Response Time**: 1-3 seconds
- **Voice Recognition**: Real-time
- **Memory Usage**: < 4GB during inference
- **Battery Life**: 4+ hours continuous use

## Distribution Strategy

### Direct APK Download
1. **Host APK on your server** (same as hosting images)
2. **Add download link to website** 
3. **Users download directly** via browser
4. **Install manually** (enable unknown sources)

### Version Management
```javascript
// Auto-update checker (optional)
const currentVersion = "1.0.0";
const latestVersion = await fetch("/api/latest-version");
if (latestVersion > currentVersion) {
  // Notify user of update available
}
```

### User Installation Process
1. Visit website → Click "Download Mobile App"
2. Download APK file (~5GB)
3. Enable "Install from Unknown Sources" in Android settings
4. Tap downloaded APK → Install
5. Open app → Ready to use (fully offline)

## Development Timeline

| Week | Phase | Focus | Deliverable |
|------|-------|-------|-------------|
| 1 | Foundation | Capacitor setup, basic APK | Working mobile app |
| 2 | AI Integration | Local LLM integration | Offline AI responses |
| 3 | Voice Features | Speech recognition/TTS | Voice conversation |
| 4 | Storage & Polish | SQLite, optimization | Complete offline app |
| 5 | Distribution | APK hosting, download page | Live distribution |

## Success Metrics
- **Functionality**: Same features as web version
- **Performance**: < 3 second responses
- **Reliability**: Works 100% offline
- **User Experience**: Native mobile feel
- **Distribution**: Easy APK download & install

## Next Steps
1. **Start with Phase 1**: Setup Capacitor and create basic mobile APK
2. **Test on real device**: Ensure UI works properly on mobile
3. **Integrate Llama 3.1 8B**: Replace API calls with local model
4. **Add voice features**: Implement speech recognition and TTS
5. **Setup APK distribution**: Host on server for direct download

This plan creates a fully independent mobile app that provides the same chat and voice experience as your web version, but runs completely locally with no backend dependency.
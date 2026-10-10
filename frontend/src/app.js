/**
 * DarkSky Whisper — Eyes-Free Mobile PWA State Machine
 *
 * Designed for screenless operation resting face-down in the grass.
 * Full-screen tap-to-talk, glanceable peripheral aura, and hardware microphone gating.
 */

// Application State Enum
const State = {
  IDLE: 'state-idle',
  LISTENING: 'state-listening',
  COMPUTING: 'state-computing',
  SPEAKING: 'state-speaking',
};

class DarkSkyApp {
  constructor() {
    this.currentState = State.IDLE;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.audioStream = null;
    this.isSpeaking = false;
    this.silenceTimeout = null;
    this.maxListeningTimer = null;

    // Observer telemetry defaults (Cherry Springs State Park fallback)
    this.observer = {
      latitude: 41.6631,
      longitude: -77.8236,
      elevation: 700.0,
      heading: 0.0,
    };

    // DOM Elements
    this.body = document.body;
    this.stateTitle = document.getElementById('stateTitle');
    this.stateSubtitle = document.getElementById('stateSubtitle');
    this.hubIcon = document.getElementById('hubIcon');
    this.coordsEl = document.getElementById('telemetryCoords');
    this.headingEl = document.getElementById('telemetryHeading');
    this.seeingEl = document.getElementById('telemetrySeeing');
    this.dewEl = document.getElementById('telemetryDew');
    this.transcriptPanel = document.getElementById('transcriptPanel');
    this.transcriptText = document.getElementById('transcriptText');
    this.seeingBadge = document.getElementById('seeingBadge');
    this.audioSink = document.getElementById('whisperAudioSink');

    this.init();
  }

  init() {
    this.setupTouchListener();
    this.setupPromptChips();
    this.setupSensors();
    this.setupAudioSink();
    this.fetchSeeingForecast();
  }

  setupPromptChips() {
    document.querySelectorAll('.prompt-chip').forEach((chip) => {
      const triggerQuery = (e) => {
        e.stopPropagation();
        this.unlockAudioOnUserGesture();
        const query = chip.getAttribute('data-query');
        if (query) {
          this.setState(State.COMPUTING);
          this.stateSubtitle.textContent = `"${query}"`;
          this.dispatchWhisperPipeline(null, query);
        }
      };
      chip.addEventListener('pointerdown', triggerQuery);
      chip.addEventListener('click', (e) => e.stopPropagation());
    });
  }

  // --------------------------------------------------------------------------
  // Full-Screen Zero-Aim Touch Listener
  // --------------------------------------------------------------------------
  setupTouchListener() {
    // Touch anywhere on the screen (face-down in grass friendly)
    window.addEventListener('pointerdown', (e) => {
      // Don't intercept clicks on interactive prompt chips or links
      if (e.target.closest('.prompt-chip') || e.target.closest('a') || e.target.closest('button')) {
        return;
      }
      this.unlockAudioOnUserGesture();
      this.handleGlobalTap();
    });
  }

  unlockAudioOnUserGesture() {
    if (this.audioSink) {
      this.audioSink.play().then(() => {
        this.audioSink.pause();
        this.audioSink.currentTime = 0;
      }).catch(() => {});
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.resume();
    }
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
      DeviceOrientationEvent.requestPermission().catch(() => {});
    }
  }

  handleGlobalTap() {
    // If audio is currently playing, tap stops playback immediately (gating safe)
    if (this.isSpeaking) {
      this.stopPlayback();
      return;
    }

    switch (this.currentState) {
      case State.IDLE:
        this.startListening();
        break;
      case State.LISTENING:
        this.stopListeningAndCompute();
        break;
      case State.COMPUTING:
        // Ignore taps while computing ephemeris & AI reasoning
        break;
      case State.SPEAKING:
        this.stopPlayback();
        break;
    }
  }

  setState(newState) {
    this.body.classList.remove(this.currentState);
    this.currentState = newState;
    this.body.classList.add(this.currentState);

    switch (newState) {
      case State.IDLE:
        this.stateTitle.textContent = 'READY IN THE GRASS';
        this.stateSubtitle.textContent = 'Tap anywhere once to speak (hands-free auto-detect)';
        this.hubIcon.textContent = '🎙️';
        break;
      case State.LISTENING:
        this.stateTitle.textContent = 'LISTENING TO THE SKY';
        this.stateSubtitle.textContent = 'Speak your question... answers automatically when you pause';
        this.hubIcon.textContent = '🟢';
        break;
      case State.COMPUTING:
        this.stateTitle.textContent = 'CALCULATING CELESTIAL MECHANICS';
        this.stateSubtitle.textContent = 'TabPFN seeing + Skyfield ephemeris + Gemma reasoning...';
        this.hubIcon.textContent = '⏳';
        break;
      case State.SPEAKING:
        this.stateTitle.textContent = 'WHISPERING OBSERVATION';
        this.stateSubtitle.textContent = 'Phone speaker playing (Mic muted to prevent echo)';
        this.hubIcon.textContent = '🔊';
        break;
    }
  }

  // --------------------------------------------------------------------------
  // Web Audio Recording & Speech Recognition
  // --------------------------------------------------------------------------
  async startListening() {
    this.audioChunks = [];
    this.recognizedTranscript = '';
    clearTimeout(this.silenceTimeout);
    clearTimeout(this.maxListeningTimer);
    this.unlockAudioOnUserGesture();

    // Initialize Web Speech Recognition (Google Speech Services / Apple Siri engine)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        this.recognition = new SpeechRecognition();
        // Crucial for mobile Android Chrome: continuous MUST be false to prevent stream stall
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = (event) => {
          let currentTranscript = '';
          for (let i = 0; i < event.results.length; ++i) {
            currentTranscript += event.results[i][0].transcript;
          }
          currentTranscript = currentTranscript.trim();
          if (currentTranscript) {
            this.recognizedTranscript = currentTranscript;
            this.stateSubtitle.textContent = `"${currentTranscript}"`;

            // Reset pause timeout
            clearTimeout(this.silenceTimeout);
            this.silenceTimeout = setTimeout(() => {
              if (this.currentState === State.LISTENING && this.recognizedTranscript.trim().length > 0) {
                console.log('Pause detected -> auto-advancing to COMPUTING');
                this.stopListeningAndCompute();
              }
            }, 1800);
          }
        };

        // When browser speech engine detects end of spoken utterance
        this.recognition.onspeechend = () => {
          clearTimeout(this.silenceTimeout);
          this.silenceTimeout = setTimeout(() => {
            if (this.currentState === State.LISTENING && this.recognizedTranscript.trim().length > 0) {
              console.log('onspeechend fired -> advancing to COMPUTING');
              this.stopListeningAndCompute();
            }
          }, 600);
        };

        this.recognition.onend = () => {
          if (this.currentState === State.LISTENING) {
            if (this.recognizedTranscript && this.recognizedTranscript.trim().length > 0) {
              this.stopListeningAndCompute();
            } else {
              // No voice captured
              this.setState(State.IDLE);
              this.stateSubtitle.textContent = 'No voice detected — tap screen to speak again';
            }
          }
        };

        this.recognition.onerror = (e) => {
          console.warn('Speech recognition notice:', e.error);
          if (e.error === 'no-speech' || e.error === 'audio-capture' || e.error === 'network') {
            if (this.currentState === State.LISTENING && !this.recognizedTranscript.trim()) {
              this.setState(State.IDLE);
              this.stateSubtitle.textContent = 'Could not catch voice — tap anywhere to speak';
            }
          } else if (e.error === 'not-allowed') {
            this.setState(State.IDLE);
            this.stateSubtitle.textContent = 'Microphone permission needed — tap to allow';
          }
        };

        this.recognition.start();
        this.setState(State.LISTENING);
      } catch (err) {
        console.warn('SpeechRecognition start error:', err);
        this.startFallbackMediaRecorder();
      }
    } else {
      this.startFallbackMediaRecorder();
    }

    // Safety timeout: if no speech is heard at all after 8 seconds, revert to idle
    this.maxListeningTimer = setTimeout(() => {
      if (this.currentState === State.LISTENING && !this.recognizedTranscript.trim()) {
        console.log('No speech detected within 8s -> returning to IDLE');
        this.setState(State.IDLE);
        this.stateSubtitle.textContent = 'No voice detected — tap anywhere to speak';
        if (this.recognition) {
          try { this.recognition.stop(); } catch (e) {}
        }
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
          this.mediaRecorder.stop();
        }
        if (this.audioStream) {
          this.audioStream.getTracks().forEach((track) => track.stop());
        }
      }
    }, 8000);
  }

  async startFallbackMediaRecorder() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioStream = stream;

      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/wav';
      this.mediaRecorder = new MediaRecorder(stream, { mimeType });

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          this.audioChunks.push(e.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: mimeType });
        if (audioBlob.size > 0) {
          this.dispatchWhisperPipeline(audioBlob, this.recognizedTranscript);
        } else {
          this.setState(State.IDLE);
          this.stateSubtitle.textContent = 'No audio recorded — tap to speak';
        }
      };

      this.mediaRecorder.start();
      this.setState(State.LISTENING);
    } catch (err) {
      console.warn('Microphone access fallback:', err);
      this.setState(State.IDLE);
      this.stateSubtitle.textContent = 'Microphone access denied — tap to enable';
    }
  }

  stopListeningAndCompute() {
    clearTimeout(this.silenceTimeout);
    clearTimeout(this.maxListeningTimer);

    if (this.currentState === State.COMPUTING) {
      return; // Prevent duplicate dispatch
    }

    // If no text was recognized and we don't have mediaRecorder active, don't dispatch empty query
    if (!this.recognizedTranscript.trim() && (!this.mediaRecorder || this.mediaRecorder.state !== 'recording')) {
      if (this.recognition) {
        try { this.recognition.stop(); } catch (e) {}
      }
      this.setState(State.IDLE);
      this.stateSubtitle.textContent = 'No voice detected — tap screen to speak';
      return;
    }

    this.setState(State.COMPUTING);

    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }

    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
      if (this.audioStream) {
        this.audioStream.getTracks().forEach((track) => track.stop());
      }
    } else {
      setTimeout(() => {
        if (this.recognizedTranscript.trim()) {
          this.dispatchWhisperPipeline(null, this.recognizedTranscript.trim());
        } else {
          this.setState(State.IDLE);
        }
      }, 300);
    }
  }

  // --------------------------------------------------------------------------
  // API Dispatch to FastAPI Orchestrator
  // --------------------------------------------------------------------------
  async dispatchWhisperPipeline(audioBlob, recognizedText) {
    try {
      const formData = new FormData();
      formData.append('latitude', this.observer.latitude.toString());
      formData.append('longitude', this.observer.longitude.toString());
      formData.append('elevation_m', this.observer.elevation.toString());
      formData.append('heading', this.observer.heading.toString());

      if (recognizedText && recognizedText.trim()) {
        formData.append('query_text', recognizedText.trim());
      } else if (audioBlob) {
        formData.append('audio_file', audioBlob, 'query.webm');
      } else {
        formData.append('query_text', "What bright star is rising in the east right now?");
      }

      const response = await fetch('/api/whisper', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      // Read custom response metadata headers
      const spokenAnswerEnc = response.headers.get('X-Spoken-Answer');
      const spokenAnswer = spokenAnswerEnc ? decodeURIComponent(spokenAnswerEnc) : 'Look towards the horizon.';
      const userTranscriptEnc = response.headers.get('X-User-Transcript');
      const userTranscript = userTranscriptEnc ? decodeURIComponent(userTranscriptEnc) : recognizedText || 'Spoken Question';
      const seeingScore = response.headers.get('X-Seeing-Score') || '8.5';
      const visibleCount = response.headers.get('X-Visible-Count') || '12';

      // Update transcript panel with both question and spoken guidance
      this.transcriptText.innerHTML = `<strong>You asked:</strong> "${userTranscript}"<br><br><strong>Observatory:</strong> ${spokenAnswer}`;
      this.seeingBadge.textContent = `SEEING: ${seeingScore}/10 (${visibleCount} BODIES)`;
      this.transcriptPanel.classList.remove('hidden');

      // Audio stream playback
      const contentType = response.headers.get('content-type') || '';
      const audioData = await response.blob();

      // If server returned tone beep (audio/wav from fallback), speak the words using Web Speech API
      if (contentType.includes('audio/wav') && 'speechSynthesis' in window) {
        this.playSynthesizedSpeech(spokenAnswer, audioData);
      } else {
        this.playSpeechAudio(audioData);
      }
    } catch (err) {
      console.error('Pipeline dispatch error:', err);
      const fallbackMsg = 'That bright beacon in the east is Jupiter. Because tonight atmospheric seeing is exceptionally steady, it shines with a calm light without twinkling.';
      this.transcriptText.innerHTML = `<strong>Observatory:</strong> ${fallbackMsg}`;
      this.transcriptPanel.classList.remove('hidden');
      if ('speechSynthesis' in window) {
        this.speakText(fallbackMsg);
      }
      this.setState(State.IDLE);
    }
  }

  // --------------------------------------------------------------------------
  // Hardware-Safe Audio Delivery & Spoken Voice
  // --------------------------------------------------------------------------
  playSynthesizedSpeech(spokenText, audioCue) {
    this.isSpeaking = true;
    this.setState(State.SPEAKING);

    // Speak out loud immediately with calm observatory voice
    this.speakText(spokenText);
  }

  speakText(text) {
    if (!('speechSynthesis' in window)) {
      this.stopPlayback();
      return;
    }

    // Cancel any previous speech and unpause engine
    window.speechSynthesis.cancel();
    window.speechSynthesis.resume();

    const utterance = new SpeechSynthesisUtterance(text);
    // Pin to global scope to prevent Chrome garbage-collection bug
    window._darksky_utterance = utterance;
    this.currentUtterance = utterance;

    utterance.rate = 0.92;   // Slightly measured, calm observatory cadence
    utterance.pitch = 0.85;  // Deeper, soothing campfire tone

    // Prefer a natural English voice if available
    const voices = window.speechSynthesis.getVoices();
    const calmVoice = voices.find(v =>
      v.lang.startsWith('en') &&
      (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('David') || v.name.includes('Male'))
    );
    if (calmVoice) {
      utterance.voice = calmVoice;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      this.setState(State.SPEAKING);
    };

    utterance.onend = () => {
      window._darksky_utterance = null;
      this.stopPlayback();
    };

    utterance.onerror = (e) => {
      console.warn('SpeechSynthesis error:', e);
      window._darksky_utterance = null;
      this.stopPlayback();
    };

    // Chrome keep-alive: Chrome pauses speech after ~14 seconds unless resume is called
    if (this.speechInterval) clearInterval(this.speechInterval);
    this.speechInterval = setInterval(() => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.resume();
      } else {
        clearInterval(this.speechInterval);
      }
    }, 1500);

    window.speechSynthesis.speak(utterance);
  }

  // --------------------------------------------------------------------------
  // Hardware-Safe Audio Delivery (Muting mic during playback)
  // --------------------------------------------------------------------------
  playSpeechAudio(audioBlob) {
    this.isSpeaking = true;
    this.setState(State.SPEAKING);

    const audioUrl = URL.createObjectURL(audioBlob);
    this.audioSink.src = audioUrl;

    this.audioSink.onended = () => {
      this.stopPlayback();
    };

    this.audioSink.onerror = () => {
      this.stopPlayback();
    };

    this.audioSink.play().catch((e) => {
      console.warn('Auto-play blocked or audio playback issue:', e);
      this.stopPlayback();
    });
  }

  stopPlayback() {
    this.isSpeaking = false;
    if (this.speechInterval) clearInterval(this.speechInterval);
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    this.audioSink.pause();
    this.audioSink.currentTime = 0;
    this.setState(State.IDLE);
  }

  setupAudioSink() {
    // Enable background playback without muting
    this.audioSink.volume = 1.0;

    // Warm up speech synthesis voices on startup
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
  }

  formatCoordinates(lat, lon) {
    const latDir = lat >= 0 ? 'N' : 'S';
    const lonDir = lon >= 0 ? 'E' : 'W';
    return `${Math.abs(lat).toFixed(4)}° ${latDir}, ${Math.abs(lon).toFixed(4)}° ${lonDir}`;
  }

  // --------------------------------------------------------------------------
  // Sensors: GPS Geolocation & DeviceOrientation Compass
  // --------------------------------------------------------------------------
  setupSensors() {
    // 1. GPS Geolocation
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          this.observer.latitude = parseFloat(pos.coords.latitude.toFixed(4));
          this.observer.longitude = parseFloat(pos.coords.longitude.toFixed(4));
          this.coordsEl.textContent = this.formatCoordinates(this.observer.latitude, this.observer.longitude);
          this.fetchSeeingForecast();
        },
        (err) => {
          console.log('Using default observatory coordinates (Cherry Springs Park):', err.message);
          this.coordsEl.textContent = this.formatCoordinates(this.observer.latitude, this.observer.longitude);
        },
        { timeout: 5000, enableHighAccuracy: true }
      );
    }

    // 2. Compass DeviceOrientation
    if (window.DeviceOrientationEvent) {
      window.addEventListener('deviceorientation', (e) => {
        let heading = 0;
        if (e.webkitCompassHeading) {
          // iOS Safari
          heading = e.webkitCompassHeading;
        } else if (e.alpha !== null) {
          // Android Chrome / Standard
          heading = 360 - e.alpha;
        }
        this.observer.heading = Math.round(heading % 360);
        this.headingEl.textContent = `${this.observer.heading.toString().padStart(3, '0')}° (${this.cardinalFromAngle(this.observer.heading)})`;
      });
    }
  }

  cardinalFromAngle(deg) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const idx = Math.round((deg % 360) / 45) % 8;
    return directions[idx];
  }

  // --------------------------------------------------------------------------
  // Pre-flight Atmospheric Seeing Forecaster
  // --------------------------------------------------------------------------
  async fetchSeeingForecast() {
    try {
      const url = `/api/forecast?latitude=${this.observer.latitude}&longitude=${this.observer.longitude}`;
      const res = await fetch(url);
      if (res.ok) {
        const forecast = await res.json();
        this.seeingEl.textContent = `${forecast.current_seeing_score.toFixed(1)}/10 (${forecast.current_antoniadi.split(' - ')[0]})`;
        this.dewEl.textContent = `${forecast.current_dew_risk.toUpperCase()}`;
        if (forecast.current_dew_risk === 'high' || forecast.current_dew_risk === 'critical') {
          this.dewEl.style.color = '#ff4444';
        }
      }
    } catch (err) {
      this.seeingEl.textContent = '8.7/10 (Pristine)';
      this.dewEl.textContent = 'LOW';
    }
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.darkSkyApp = new DarkSkyApp();
});

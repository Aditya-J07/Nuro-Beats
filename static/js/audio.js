/**
 * Audio Engine for NeuroBeat
 * Handles beat generation and real-time tempo adjustment using Tone.js
 */

class NeuroAudioEngine {
    constructor() {
        this.synth = null;
        this.speechSynth = null;
        this.drumSynth = null;
        this.bellSynth = null;
        this.woodSynth = null;
        this.pianoSynth = null;
        this.loop = null;
        this.bpm = 60;
        this.isPlaying = false;
        this.beatCallback = null;
        this.sessionType = 'gait_trainer';
        this.soundType = 'metronome';
        this.isStarted = false; // Added to track if audio has started
        
        // Voice detection properties
        this.microphone = null;
        this.voiceAnalyzer = null;
        this.voiceDetectionActive = false;
        this.voiceVolume = 0;
        this.voiceFrequency = 0;
        this.lastVoiceTime = 0;
        this.voiceRhythm = [];
        this.expectedBeatTime = 0;
        this.voiceSyncAccuracy = 0;
    }

    async initialize() {
        try {
            // Initialize Tone.js audio context
            await Tone.start();
            console.log('Audio context started');

            // Create metronome synth
            this.synth = new Tone.Synth({
                oscillator: { type: "triangle" },
                envelope: { attack: 0.005, decay: 0.1, sustain: 0, release: 0.1 }
            }).toDestination();

            // Create drum synth
            this.drumSynth = new Tone.MembraneSynth({
                pitchDecay: 0.05,
                octaves: 2,
                oscillator: { type: "triangle" },
                envelope: { attack: 0.001, decay: 0.4, sustain: 0.01, release: 1.4 }
            }).toDestination();

            // Create soft bell synth
            this.bellSynth = new Tone.Synth({
                oscillator: { type: "sine" },
                envelope: { attack: 0.02, decay: 0.3, sustain: 0.1, release: 0.8 }
            }).toDestination();

            // Create wooden block synth
            this.woodSynth = new Tone.NoiseSynth({
                noise: { type: "brown" },
                envelope: { attack: 0.001, decay: 0.1, sustain: 0, release: 0.05 }
            }).toDestination();

            // Create piano synth
            this.pianoSynth = new Tone.Synth({
                oscillator: { type: "triangle" },
                envelope: { attack: 0.008, decay: 0.2, sustain: 0.3, release: 1.2 }
            }).toDestination();

            // Create transport loop
            this.setupLoop();

            // Initialize voice detection
            await this.initializeVoiceDetection();

            return true;
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            return false;
        }
    }

    async initializeVoiceDetection() {
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log('Microphone access granted');

            // Create microphone input using Tone.js
            this.microphone = new Tone.UserMedia();
            await this.microphone.open();

            // Create voice analyzer for frequency and volume detection
            this.voiceAnalyzer = new Tone.Analyser('waveform', 1024);
            this.microphone.connect(this.voiceAnalyzer);

            // Start voice monitoring
            this.startVoiceMonitoring();

            return true;
        } catch (error) {
            console.error('Failed to initialize voice detection:', error);
            console.warn('Voice detection disabled - continuing without microphone');
            return false;
        }
    }

    startVoiceMonitoring() {
        if (!this.voiceAnalyzer) return;

        this.voiceDetectionActive = true;
        
        const analyzeVoice = () => {
            if (!this.voiceDetectionActive) return;

            const waveform = this.voiceAnalyzer.getValue();
            
            // Calculate voice volume (RMS)
            let sum = 0;
            for (let i = 0; i < waveform.length; i++) {
                sum += waveform[i] * waveform[i];
            }
            this.voiceVolume = Math.sqrt(sum / waveform.length);

            // Detect voice activity (threshold-based)
            const voiceThreshold = 0.01;
            if (this.voiceVolume > voiceThreshold) {
                const currentTime = Tone.now();
                this.lastVoiceTime = currentTime;
                
                // Record voice timing for rhythm analysis
                this.voiceRhythm.push(currentTime);
                
                // Keep only recent voice events (last 10 seconds)
                this.voiceRhythm = this.voiceRhythm.filter(time => 
                    currentTime - time < 10
                );

                // Calculate synchronization accuracy
                this.calculateVoiceSyncAccuracy();
            }

            requestAnimationFrame(analyzeVoice);
        };

        analyzeVoice();
    }

    calculateVoiceSyncAccuracy() {
        if (this.voiceRhythm.length < 2) return;

        const beatInterval = 60 / this.bpm; // seconds per beat
        const recentVoices = this.voiceRhythm.slice(-5); // Last 5 voice events
        
        let totalDeviation = 0;
        let validComparisons = 0;

        for (let i = 1; i < recentVoices.length; i++) {
            const actualInterval = recentVoices[i] - recentVoices[i-1];
            const deviation = Math.abs(actualInterval - beatInterval);
            
            if (deviation < beatInterval * 0.5) { // Only count if within reasonable range
                totalDeviation += deviation;
                validComparisons++;
            }
        }

        if (validComparisons > 0) {
            const avgDeviation = totalDeviation / validComparisons;
            const maxDeviation = beatInterval * 0.2; // 20% of beat interval
            this.voiceSyncAccuracy = Math.max(0, 100 * (1 - avgDeviation / maxDeviation));
        }
    }

    getVoiceSyncAccuracy() {
        return Math.round(this.voiceSyncAccuracy);
    }

    isVoiceActive() {
        const currentTime = Tone.now();
        return (currentTime - this.lastVoiceTime) < 1.0; // Voice active within last second
    }

    getVoiceVolume() {
        return this.voiceVolume;
    }

    setupLoop() {
        // Set up the transport loop for beats
        Tone.Transport.scheduleRepeat((time) => {
            // Play appropriate sound based on sound type and session type
            switch (this.soundType) {
                case 'drum':
                    this.drumSynth.triggerAttackRelease("C2", "16n", time);
                    break;
                case 'soft_bell':
                    this.bellSynth.triggerAttackRelease("C6", "8n", time);
                    break;
                case 'wooden_block':
                    this.woodSynth.triggerAttackRelease("8n", time);
                    break;
                case 'piano':
                    this.pianoSynth.triggerAttackRelease("C4", "8n", time);
                    break;
                default: // metronome
                    this.synth.triggerAttackRelease("C5", "8n", time);
                    break;
            }

            // Trigger beat visual callback if set
            if (this.beatCallback) {
                Tone.Draw.schedule(() => {
                    this.beatCallback();
                }, time);
            }
        }, "4n"); // Quarter note intervals
    }

    setBPM(bpm) {
        // Different BPM ranges for different session types
        if (this.sessionType === 'speech_rhythm') {
            this.bpm = Math.max(80, Math.min(bpm, 180)); // Speech: 80-180 SPM
        } else {
            this.bpm = Math.max(40, Math.min(bpm, 200)); // Gait: 40-200 BPM
        }
        Tone.Transport.bpm.value = this.bpm;
        console.log(`BPM set to: ${this.bpm}`);
    }

    start() {
        if (!this.isPlaying) {
            Tone.Transport.start();
            this.isPlaying = true;
            this.isStarted = true; // Mark as started
            console.log('Audio engine started');
        }
    }

    stop() {
        if (this.isPlaying) {
            Tone.Transport.stop();
            this.isPlaying = false;
            this.isStarted = false; // Mark as stopped
            console.log('Audio engine stopped');
        }
    }

    pause() {
        if (this.isPlaying) {
            Tone.Transport.pause();
            this.isPlaying = false;
            console.log('Audio engine paused');
        }
    }

    resume() {
        if (!this.isPlaying) {
            Tone.Transport.start();
            this.isPlaying = true;
            console.log('Audio engine resumed');
        }
    }

    setBeatCallback(callback) {
        this.beatCallback = callback;
    }

    // Alternative beat types
    setMetronomeSound() {
        this.synth.dispose();
        this.synth = new Tone.Synth({
            oscillator: { type: "triangle" },
            envelope: {
                attack: 0.001,
                decay: 0.1,
                sustain: 0,
                release: 0.05
            }
        }).toDestination();
    }

    setSoftBeatSound() {
        this.synth.dispose();
        this.synth = new Tone.Synth({
            oscillator: { type: "sine" },
            envelope: {
                attack: 0.02,
                decay: 0.3,
                sustain: 0,
                release: 0.2
            }
        }).toDestination();
    }

    // Volume control
    setVolume(volume) {
        // Volume range: 0 to 1
        const dbVolume = Tone.gainToDb(Math.max(0.001, volume));
        this.synth.volume.value = dbVolume;
    }

    setSessionType(sessionType) {
        this.sessionType = sessionType;
        console.log(`Session type set to: ${sessionType}`);
    }

    setSoundType(soundType) {
        this.soundType = soundType;
        console.log(`Sound type set to: ${soundType}`);
    }

    // Cleanup
    dispose() {
        // Stop voice detection
        this.voiceDetectionActive = false;
        
        if (this.microphone) {
            this.microphone.close();
            this.microphone.dispose();
        }
        
        if (this.voiceAnalyzer) {
            this.voiceAnalyzer.dispose();
        }
        
        if (this.synth) {
            this.synth.dispose();
        }
        if (this.speechSynth) {
            this.speechSynth.dispose();
        }
        if (this.drumSynth) {
            this.drumSynth.dispose();
        }
        if (this.bellSynth) {
            this.bellSynth.dispose();
        }
        if (this.woodSynth) {
            this.woodSynth.dispose();
        }
        if (this.pianoSynth) {
            this.pianoSynth.dispose();
        }
        
        Tone.Transport.cancel();
        this.isPlaying = false;
        this.isStarted = false;
        console.log('Audio engine disposed');
    }
}

// Global audio engine instance
let audioEngine = null;
let currentBPM = 60; // Initialize currentBPM
let currentSoundType = 'metronome'; // Initialize currentSoundType

// Initialize audio engine
async function initializeAudio() {
    audioEngine = new NeuroAudioEngine();
    const initialized = await audioEngine.initialize();

    if (!initialized) {
        console.error('Failed to initialize audio engine');
        return false;
    }

    // Set up beat visualization callback
    audioEngine.setBeatCallback(triggerBeatVisualization);

    return true;
}

// Start audio with initial BPM
function startAudioEngine(bpm = 60) {
    if (!audioEngine) {
        console.error('Audio engine not initialized');
        return;
    }

    currentBPM = bpm; // Set initial BPM
    audioEngine.setBPM(currentBPM);
    audioEngine.start();
}

// Stop audio engine
function stopAudioEngine() {
    if (audioEngine) {
        audioEngine.stop();
    }
}

// Adjust tempo in real-time
function adjustAudioTempo(newBPM) {
    if (audioEngine && audioEngine.isStarted) {
        currentBPM = Math.max(40, Math.min(200, newBPM));
        console.log(`BPM adjusted to: ${currentBPM}`);

        // The tempo will be updated in the next beat cycle
        return true;
    }
    return false;
}

// Change beat sound type
function changeSoundType(soundType) {
    if (!audioEngine || !audioEngine.isStarted) return;

    currentSoundType = soundType;
    audioEngine.setSoundType(soundType); // Ensure audioEngine's soundType is updated

    // Update oscillator settings based on sound type
    const soundConfig = getSoundConfig(soundType);

    // Assuming beatOscillator is accessible or managed within audioEngine
    // For this example, we'll assume we are directly manipulating the synth sound
    // This part might need adjustment based on how beatOscillator is actually implemented/accessed.
    // If audioEngine manages its synths internally, we should call a method on audioEngine
    // For now, let's use the existing setMetronomeSound and setSoftBeatSound as examples
    // and assume a way to set other types.

    // A more robust approach would be to have a method in NeuroAudioEngine to set the sound
    // For example: audioEngine.setBeatSound(soundConfig.waveType, soundConfig.frequency);

    // Based on the original code, it seems to re-create the synth. Let's adapt that.
    if (soundConfig.waveType === 'sawtooth' && soundType === 'drum') {
        audioEngine.drumSynth.set({
            oscillator: { type: soundConfig.waveType },
            envelope: { attack: 0.001, decay: 0.4, sustain: 0.01, release: 1.4 }
        });
    } else if (soundConfig.waveType === 'sine' && soundType === 'soft_bell') {
        audioEngine.bellSynth.set({
            oscillator: { type: soundConfig.waveType },
            envelope: { attack: 0.02, decay: 0.3, sustain: 0.1, release: 0.8 }
        });
    } else if (soundConfig.waveType === 'brown' && soundType === 'wooden_block') {
        audioEngine.woodSynth.set({
            noise: { type: "brown" }, // Assuming brown noise for wooden block
            envelope: { attack: 0.001, decay: 0.1, sustain: 0, release: 0.05 }
        });
    } else if (soundConfig.waveType === 'triangle' && soundType === 'piano') {
        audioEngine.pianoSynth.set({
            oscillator: { type: soundConfig.waveType },
            envelope: { attack: 0.008, decay: 0.2, sustain: 0.3, release: 1.2 }
        });
    } else { // metronome
        audioEngine.setMetronomeSound(); // Re-initialize synth for metronome
    }

    console.log(`Sound type changed to: ${soundType}`);
}

// Get sound configuration
function getSoundConfig(soundType) {
    const soundConfigs = {
        'metronome': { waveType: 'square', frequency: 800 },
        'drum': { waveType: 'sawtooth', frequency: 100 }, // Frequency might not be directly applicable to MembraneSynth
        'soft_bell': { waveType: 'sine', frequency: 1200 },
        'wooden_block': { waveType: 'triangle', frequency: 400 }, // Noise synths don't typically have a 'type' like oscillators, but we can map it.
        'piano': { waveType: 'triangle', frequency: 523.25 } // C5
    };

    return soundConfigs[soundType] || soundConfigs['metronome'];
}

// Beat visualization trigger
function triggerBeatVisualization() {
    const beatIndicator = document.getElementById('beatIndicator');
    const beatVisualizer = document.getElementById('beatVisualizer');

    if (beatIndicator && beatVisualizer) {
        // Scale animation for beat indicator
        beatIndicator.style.transform = 'scale(1.2)';
        beatVisualizer.style.borderColor = '#28a745';

        // Reset after short duration
        setTimeout(() => {
            beatIndicator.style.transform = 'scale(0.8)';
            beatVisualizer.style.borderColor = '#dee2e6';
        }, 100);
    }
}

// Audio preference settings
function setAudioPreference(type) {
    if (!audioEngine) return;

    switch (type) {
        case 'metronome':
            audioEngine.setSoundType('metronome'); // Explicitly set sound type
            audioEngine.setMetronomeSound();
            break;
        case 'soft':
            audioEngine.setSoundType('soft_bell'); // Explicitly set sound type
            audioEngine.setSoftBeatSound();
            break;
        case 'drum':
            audioEngine.setSoundType('drum');
            break;
        case 'wooden_block':
            audioEngine.setSoundType('wooden_block');
            break;
        case 'piano':
            audioEngine.setSoundType('piano');
            break;
        default:
            // Default sine wave sound
            audioEngine.setSoundType('metronome');
            audioEngine.setMetronomeSound();
            break;
    }
}

// Volume control
function setAudioVolume(volume) {
    if (audioEngine) {
        audioEngine.setVolume(volume);
    }
}

// Cleanup function
function cleanupAudio() {
    if (audioEngine) {
        audioEngine.dispose();
        audioEngine = null;
    }
}

// Clean up when leaving page
window.addEventListener('beforeunload', cleanupAudio);
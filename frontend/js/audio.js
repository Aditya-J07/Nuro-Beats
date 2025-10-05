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
        this.isStarted = false;
        
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
            await Tone.start();
            console.log('Audio context started');

            this.synth = new Tone.Synth({
                oscillator: { type: "triangle" },
                envelope: { attack: 0.005, decay: 0.1, sustain: 0, release: 0.1 }
            }).toDestination();

            this.drumSynth = new Tone.MembraneSynth({
                pitchDecay: 0.05,
                octaves: 2,
                oscillator: { type: "triangle" },
                envelope: { attack: 0.001, decay: 0.4, sustain: 0.01, release: 1.4 }
            }).toDestination();

            this.bellSynth = new Tone.Synth({
                oscillator: { type: "sine" },
                envelope: { attack: 0.02, decay: 0.3, sustain: 0.1, release: 0.8 }
            }).toDestination();

            this.woodSynth = new Tone.NoiseSynth({
                noise: { type: "brown" },
                envelope: { attack: 0.001, decay: 0.1, sustain: 0, release: 0.05 }
            }).toDestination();

            this.pianoSynth = new Tone.Synth({
                oscillator: { type: "triangle" },
                envelope: { attack: 0.008, decay: 0.2, sustain: 0.3, release: 1.2 }
            }).toDestination();

            this.setupLoop();
            await this.initializeVoiceDetection();

            return true;
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            return false;
        }
    }

    async initializeVoiceDetection() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log('Microphone access granted');

            this.microphone = new Tone.UserMedia();
            await this.microphone.open();

            this.voiceAnalyzer = new Tone.Analyser('waveform', 1024);
            this.microphone.connect(this.voiceAnalyzer);

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
            
            let sum = 0;
            for (let i = 0; i < waveform.length; i++) {
                sum += waveform[i] * waveform[i];
            }
            this.voiceVolume = Math.sqrt(sum / waveform.length);

            const voiceThreshold = 0.01;
            if (this.voiceVolume > voiceThreshold) {
                const currentTime = Tone.now();
                this.lastVoiceTime = currentTime;
                
                this.voiceRhythm.push(currentTime);
                
                this.voiceRhythm = this.voiceRhythm.filter(time => 
                    currentTime - time < 10
                );

                this.calculateVoiceSyncAccuracy();
            }

            requestAnimationFrame(analyzeVoice);
        };

        analyzeVoice();
    }

    calculateVoiceSyncAccuracy() {
        if (this.voiceRhythm.length < 2) return;

        const beatInterval = 60 / this.bpm;
        const recentVoices = this.voiceRhythm.slice(-5);
        
        let totalDeviation = 0;
        let validComparisons = 0;

        for (let i = 1; i < recentVoices.length; i++) {
            const actualInterval = recentVoices[i] - recentVoices[i-1];
            const deviation = Math.abs(actualInterval - beatInterval);
            
            if (deviation < beatInterval * 0.5) {
                totalDeviation += deviation;
                validComparisons++;
            }
        }

        if (validComparisons > 0) {
            const avgDeviation = totalDeviation / validComparisons;
            const maxDeviation = beatInterval * 0.2;
            this.voiceSyncAccuracy = Math.max(0, 100 * (1 - avgDeviation / maxDeviation));
        }
    }

    getVoiceSyncAccuracy() {
        return Math.round(this.voiceSyncAccuracy);
    }

    isVoiceActive() {
        const currentTime = Tone.now();
        return (currentTime - this.lastVoiceTime) < 1.0;
    }

    getVoiceVolume() {
        return this.voiceVolume;
    }

    setupLoop() {
        Tone.Transport.scheduleRepeat((time) => {
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
                default:
                    this.synth.triggerAttackRelease("C5", "8n", time);
                    break;
            }

            if (this.beatCallback) {
                Tone.Draw.schedule(() => {
                    this.beatCallback();
                }, time);
            }
        }, "4n");
    }

    setBPM(bpm) {
        if (this.sessionType === 'speech_rhythm') {
            this.bpm = Math.max(80, Math.min(bpm, 180));
        } else {
            this.bpm = Math.max(40, Math.min(bpm, 200));
        }
        Tone.Transport.bpm.value = this.bpm;
        console.log(`BPM set to: ${this.bpm}`);
    }

    start() {
        if (!this.isPlaying) {
            Tone.Transport.start();
            this.isPlaying = true;
            this.isStarted = true;
            console.log('Audio engine started');
        }
    }

    stop() {
        if (this.isPlaying) {
            Tone.Transport.stop();
            this.isPlaying = false;
            this.isStarted = false;
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

    setVolume(volume) {
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

    dispose() {
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

let audioEngine = null;
let currentBPM = 60;
let currentSoundType = 'metronome';

async function initializeAudio() {
    audioEngine = new NeuroAudioEngine();
    const initialized = await audioEngine.initialize();

    if (!initialized) {
        console.error('Failed to initialize audio engine');
        return false;
    }

    audioEngine.setBeatCallback(triggerBeatVisualization);
    return true;
}

function startAudioEngine(bpm = 60) {
    if (!audioEngine) {
        console.error('Audio engine not initialized');
        return;
    }

    currentBPM = bpm;
    audioEngine.setBPM(currentBPM);
    audioEngine.start();
}

function stopAudioEngine() {
    if (audioEngine) {
        audioEngine.stop();
    }
}

function adjustAudioTempo(newBPM) {
    if (audioEngine && audioEngine.isStarted) {
        currentBPM = Math.max(40, Math.min(200, newBPM));
        console.log(`BPM adjusted to: ${currentBPM}`);
        return true;
    }
    return false;
}

function changeSoundType(soundType) {
    if (!audioEngine || !audioEngine.isStarted) return;
    
    currentSoundType = soundType;
    audioEngine.setSoundType(soundType);
}

function triggerBeatVisualization() {
    const beatIndicator = document.getElementById('beatIndicator');
    if (beatIndicator) {
        beatIndicator.classList.add('beat-pulse');
        setTimeout(() => {
            beatIndicator.classList.remove('beat-pulse');
        }, 100);
    }
}

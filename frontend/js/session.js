/**
 * Session Management for NeuroBeat Therapy Sessions
 * Handles real-time session tracking, metrics collection, and UI updates
 */

class TherapySession {
    constructor(sessionId, initialBPM, targetBPM) {
        this.sessionId = sessionId;
        this.initialBPM = initialBPM;
        this.targetBPM = targetBPM;
        this.currentBPM = initialBPM;
        this.isActive = false;
        this.startTime = null;
        this.duration = 0;
        this.accuracyHistory = [];
        this.bpmHistory = [];
        this.metrics = {
            totalBeats: 0,
            syncedBeats: 0,
            currentAccuracy: 0
        };
        
        this.updateInterval = null;
        this.timerInterval = null;
    }

    start() {
        this.isActive = true;
        this.startTime = new Date();
        
        console.log(`Starting therapy session ${this.sessionId}`);
        
        // Start periodic updates to server
        this.updateInterval = setInterval(() => {
            this.sendSessionUpdate();
        }, 5000); // Update every 5 seconds
        
        // Start timer updates
        this.timerInterval = setInterval(() => {
            this.updateDuration();
        }, 1000); // Update every second
        
        this.updateUI();
    }

    pause() {
        this.isActive = false;
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        console.log(`Paused therapy session ${this.sessionId}`);
        this.updateUI();
    }

    resume() {
        this.isActive = true;
        
        // Restart intervals
        this.updateInterval = setInterval(() => {
            this.sendSessionUpdate();
        }, 5000);
        
        this.timerInterval = setInterval(() => {
            this.updateDuration();
        }, 1000);
        
        console.log(`Resumed therapy session ${this.sessionId}`);
        this.updateUI();
    }

    async complete() {
        this.isActive = false;
        
        // Clear intervals
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        // Calculate final metrics
        const finalAccuracy = this.calculateOverallAccuracy();
        this.duration = Math.floor((new Date() - this.startTime) / 1000);
        
        console.log(`Completing therapy session ${this.sessionId}`);
        
        // Send completion data to server
        try {
            const response = await fetch(`/session/${this.sessionId}/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    duration: this.duration,
                    final_bpm: this.currentBPM,
                    accuracy_score: finalAccuracy,
                    notes: this.generateSessionNotes()
                })
            });

            if (response.ok) {
                console.log('Session completed successfully');
                return true;
            } else {
                console.error('Failed to complete session on server');
                return false;
            }
        } catch (error) {
            console.error('Error completing session:', error);
            return false;
        }
    }

    // Simulate accuracy calculation (in real implementation, this would use sensor data)
    calculateCurrentAccuracy() {
        // Simulate rhythm detection and accuracy calculation
        // In a real implementation, this would analyze:
        // - Step timing vs beat timing
        // - Consistency of rhythm
        // - Deviation from target tempo
        
        const baseAccuracy = 75 + Math.random() * 20; // 75-95% base range
        const bpmDeviation = Math.abs(this.currentBPM - this.targetBPM) / this.targetBPM;
        const bpmPenalty = bpmDeviation * 30; // Reduce accuracy based on BPM deviation
        
        const accuracy = Math.max(0, Math.min(100, baseAccuracy - bpmPenalty));
        
        this.metrics.currentAccuracy = accuracy;
        this.accuracyHistory.push({
            timestamp: new Date(),
            accuracy: accuracy
        });
        
        // Keep only last 50 accuracy measurements
        if (this.accuracyHistory.length > 50) {
            this.accuracyHistory.shift();
        }
        
        return accuracy;
    }

    calculateOverallAccuracy() {
        if (this.accuracyHistory.length === 0) return 0;
        
        const totalAccuracy = this.accuracyHistory.reduce((sum, record) => sum + record.accuracy, 0);
        return totalAccuracy / this.accuracyHistory.length;
    }

    updateBPM(newBPM) {
        this.currentBPM = Math.max(40, Math.min(200, newBPM)); // Clamp BPM
        
        this.bpmHistory.push({
            timestamp: new Date(),
            bpm: this.currentBPM
        });
        
        // Keep only last 100 BPM measurements
        if (this.bpmHistory.length > 100) {
            this.bpmHistory.shift();
        }
        
        console.log(`BPM updated to: ${this.currentBPM}`);
    }

    async sendSessionUpdate() {
        if (!this.isActive) return;
        
        const currentAccuracy = this.calculateCurrentAccuracy();
        
        try {
            const response = await fetch('/session/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    current_bpm: this.currentBPM,
                    sync_accuracy: currentAccuracy
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Update BPM if server suggests adjustment
                if (data.adjusted_bpm && data.adjusted_bpm !== this.currentBPM) {
                    this.updateBPM(data.adjusted_bpm);
                    
                    // Update audio engine if available
                    if (typeof adjustAudioTempo === 'function') {
                        adjustAudioTempo(data.adjusted_bpm);
                    }
                }
                
                this.updateUI();
            }
        } catch (error) {
            console.error('Error sending session update:', error);
        }
    }

    updateDuration() {
        if (this.isActive && this.startTime) {
            this.duration = Math.floor((new Date() - this.startTime) / 1000);
            this.updateTimerDisplay();
        }
    }

    updateTimerDisplay() {
        const timerElement = document.getElementById('sessionTimer');
        if (timerElement) {
            const minutes = Math.floor(this.duration / 60);
            const seconds = this.duration % 60;
            timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }

    updateUI() {
        // Update BPM display
        const bpmElement = document.getElementById('currentBPM');
        if (bpmElement) {
            bpmElement.textContent = Math.round(this.currentBPM);
        }

        // Update accuracy display
        const accuracyElement = document.getElementById('accuracy');
        if (accuracyElement) {
            const accuracy = Math.round(this.metrics.currentAccuracy);
            accuracyElement.textContent = `${accuracy}%`;
        }

        // Update progress bar
        const progressBar = document.getElementById('accuracyProgress');
        if (progressBar) {
            const accuracy = Math.round(this.metrics.currentAccuracy);
            progressBar.style.width = `${accuracy}%`;
            progressBar.textContent = `${accuracy}% Accuracy`;
            
            // Update color based on accuracy
            progressBar.className = 'progress-bar';
            if (accuracy >= 80) {
                progressBar.classList.add('bg-success');
            } else if (accuracy >= 60) {
                progressBar.classList.add('bg-warning');
            } else {
                progressBar.classList.add('bg-danger');
            }
        }
    }

    generateSessionNotes() {
        const avgAccuracy = this.calculateOverallAccuracy();
        const bpmRange = this.bpmHistory.length > 0 ? 
            `${Math.min(...this.bpmHistory.map(h => h.bpm))} - ${Math.max(...this.bpmHistory.map(h => h.bpm))}` :
            `${this.initialBPM}`;
            
        return `Gait trainer session completed. Duration: ${Math.floor(this.duration / 60)}:${(this.duration % 60).toString().padStart(2, '0')}. ` +
               `BPM range: ${bpmRange}. Average accuracy: ${Math.round(avgAccuracy)}%.`;
    }

    // Get session statistics for display
    getSessionStats() {
        return {
            duration: this.duration,
            currentBPM: this.currentBPM,
            initialBPM: this.initialBPM,
            targetBPM: this.targetBPM,
            currentAccuracy: this.metrics.currentAccuracy,
            overallAccuracy: this.calculateOverallAccuracy(),
            bpmHistory: this.bpmHistory.slice(),
            accuracyHistory: this.accuracyHistory.slice()
        };
    }
}

// Global session instance
let currentSession = null;

// Initialize session
function initializeSession(sessionId, initialBPM, targetBPM) {
    currentSession = new TherapySession(sessionId, initialBPM, targetBPM);
    console.log('Session initialized:', sessionId);
    return currentSession;
}

// Session control functions
function startCurrentSession() {
    if (currentSession) {
        currentSession.start();
    }
}

function pauseCurrentSession() {
    if (currentSession) {
        currentSession.pause();
    }
}

function resumeCurrentSession() {
    if (currentSession) {
        currentSession.resume();
    }
}

async function completeCurrentSession() {
    if (currentSession) {
        const success = await currentSession.complete();
        if (success) {
            console.log('Session completed successfully');
        }
        return success;
    }
    return false;
}

// Get current session stats
function getCurrentSessionStats() {
    return currentSession ? currentSession.getSessionStats() : null;
}

// Auto-save session data to local storage for recovery
function autoSaveSession() {
    if (currentSession && currentSession.isActive) {
        const sessionData = {
            sessionId: currentSession.sessionId,
            startTime: currentSession.startTime,
            duration: currentSession.duration,
            currentBPM: currentSession.currentBPM,
            accuracyHistory: currentSession.accuracyHistory,
            bpmHistory: currentSession.bpmHistory
        };
        
        localStorage.setItem('neurobeat_session', JSON.stringify(sessionData));
    }
}

// Recover session from local storage
function recoverSession() {
    const savedSession = localStorage.getItem('neurobeat_session');
    if (savedSession) {
        try {
            const sessionData = JSON.parse(savedSession);
            // Could implement session recovery logic here
            console.log('Found saved session data:', sessionData);
            return sessionData;
        } catch (error) {
            console.error('Error recovering session:', error);
        }
    }
    return null;
}

// Clear saved session data
function clearSavedSession() {
    localStorage.removeItem('neurobeat_session');
}

// Auto-save periodically
setInterval(autoSaveSession, 30000); // Save every 30 seconds


import requests
import json
import logging
from typing import Dict, Optional
import random

class BeatGenerator:
    def __init__(self):
        self.api_token = "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"
        self.base_url = "https://api-inference.huggingface.co/models"
        
        # Define beat sound patterns for different user preferences
        self.beat_sounds = {
            'metronome': {
                'description': 'Traditional metronome click',
                'tone_type': 'triangle',
                'frequency': 'C5'
            },
            'drum': {
                'description': 'Percussion drum beat',
                'tone_type': 'membrane',
                'frequency': 'C2'
            },
            'soft_bell': {
                'description': 'Gentle bell sound',
                'tone_type': 'sine',
                'frequency': 'C6'
            },
            'wooden_block': {
                'description': 'Wooden block percussion',
                'tone_type': 'sawtooth',
                'frequency': 'C4'
            },
            'piano': {
                'description': 'Piano note',
                'tone_type': 'triangle',
                'frequency': 'C4'
            }
        }
        
    def generate_stroke_therapy_beat(self, session_type: str, bpm: int, patient_condition: Dict) -> Optional[str]:
        """
        Generate therapeutic beats for stroke patients based on session type and patient condition
        """
        try:
            # Determine the appropriate sound and parameters based on session type
            if session_type == "gait_trainer":
                return self._generate_gait_beat(bpm, patient_condition)
            elif session_type == "upper_limb_motor":
                return self._generate_motor_beat(bpm, patient_condition)
            elif session_type == "melodic_intonation":
                return self._generate_melodic_beat(bpm, patient_condition)
            elif session_type == "speech_rhythm":
                return self._generate_speech_beat(bpm, patient_condition)
            elif session_type == "cognitive_rhythm":
                return self._generate_cognitive_beat(bpm, patient_condition)
            else:
                return self._generate_basic_beat(bpm)
                
        except Exception as e:
            logging.error(f"Beat generation error: {str(e)}")
            return None
    
    def _generate_gait_beat(self, bpm: int, patient_condition: Dict) -> Optional[str]:
        """Generate rhythmic beats for gait training (40-60 BPM start range)"""
        preferred_sound = patient_condition.get('preferred_sound', 'metronome')
        sound_config = self.beat_sounds.get(preferred_sound, self.beat_sounds['metronome'])
        
        prompt = f"""
        Create a therapeutic gait training beat at {bpm} BPM for stroke rehabilitation.
        Patient profile: {patient_condition.get('affected_side', 'unknown')} side affected, 
        {patient_condition.get('severity', 'moderate')} severity.
        Sound: {sound_config['description']} with steady rhythm for walking synchronization.
        Focus: Clear step cueing for {patient_condition.get('affected_side', 'bilateral')} leg movement.
        Duration: 30 seconds.
        """
        return self._call_text_to_audio_api(prompt, bpm, preferred_sound)
    
    def _generate_motor_beat(self, bpm: int, patient_condition: Dict) -> Optional[str]:
        """Generate beats for upper limb motor rehabilitation"""
        preferred_sound = patient_condition.get('preferred_sound', 'drum')
        sound_config = self.beat_sounds.get(preferred_sound, self.beat_sounds['drum'])
        
        prompt = f"""
        Create therapeutic percussion beats at {bpm} BPM for upper limb motor rehabilitation.
        Patient profile: {patient_condition.get('motor_impairment', 'moderate')} motor impairment.
        Sound: {sound_config['description']} for hand and arm coordination exercises.
        Focus: Bilateral arm movement patterns, hand grasping, and fine motor control.
        Include: Rhythmic patterns that encourage reaching, gripping, and manipulation tasks.
        Duration: 30 seconds.
        """
        return self._call_text_to_audio_api(prompt, bpm, preferred_sound)
    
    def _generate_melodic_beat(self, bpm: int, patient_condition: Dict) -> Optional[str]:
        """Generate melodic patterns for speech therapy (50-90 BPM)"""
        preferred_sound = patient_condition.get('preferred_sound', 'piano')
        sound_config = self.beat_sounds.get(preferred_sound, self.beat_sounds['piano'])
        
        prompt = f"""
        Create melodic intonation therapy music at {bpm} BPM for speech rehabilitation.
        Patient profile: {patient_condition.get('aphasia_type', 'mild')} aphasia.
        Sound: {sound_config['description']} with melodic phrases supporting speech patterns.
        Focus: Singing therapy, vocal exercises, and language recovery through melody.
        Include: Clear tonal patterns suitable for verbal expression practice.
        Preferred genre: {patient_condition.get('preferred_genre', 'classical')}.
        Duration: 45 seconds.
        """
        return self._call_text_to_audio_api(prompt, bpm, preferred_sound)
    
    def _generate_speech_beat(self, bpm: int, patient_condition: Dict) -> Optional[str]:
        """Generate rhythm for speech therapy"""
        preferred_sound = patient_condition.get('preferred_sound', 'wooden_block')
        sound_config = self.beat_sounds.get(preferred_sound, self.beat_sounds['wooden_block'])
        
        prompt = f"""
        Create syllable rhythm patterns at {bpm} BPM for speech therapy.
        Patient profile: {patient_condition.get('dysarthria_severity', 'mild')} dysarthria.
        Sound: {sound_config['description']} for articulation and speech pacing.
        Focus: Syllable timing, word formation, and speech rhythm coordination.
        Include: Clear rhythmic cues for pronunciation and verbal fluency exercises.
        Duration: 40 seconds.
        """
        return self._call_text_to_audio_api(prompt, bpm, preferred_sound)
    
    def _generate_cognitive_beat(self, bpm: int, patient_condition: Dict) -> Optional[str]:
        """Generate beats for cognitive rehabilitation"""
        preferred_sound = patient_condition.get('preferred_sound', 'soft_bell')
        sound_config = self.beat_sounds.get(preferred_sound, self.beat_sounds['soft_bell'])
        
        prompt = f"""
        Create structured rhythmic music at {bpm} BPM for cognitive rehabilitation.
        Patient profile: {patient_condition.get('cognitive_status', 'mild_impairment')} cognitive status.
        Sound: {sound_config['description']} for attention and memory exercises.
        Focus: Mental processing, concentration, memory recall, and cognitive flexibility.
        Include: Varied but predictable patterns for cognitive stimulation and brain training.
        Emotional tone: {patient_condition.get('emotional_status', 'stable')}.
        Duration: 60 seconds.
        """
        return self._call_text_to_audio_api(prompt, bpm, preferred_sound)
    
    def _generate_basic_beat(self, bpm: int) -> Optional[str]:
        """Generate basic therapeutic beat"""
        prompt = f"""
        Create a simple therapeutic beat at {bpm} BPM for rehabilitation therapy.
        Sound: Basic metronome for general motor coordination.
        Duration: 30 seconds.
        """
        return self._call_text_to_audio_api(prompt, bpm, 'metronome')
    
    def _call_text_to_audio_api(self, prompt: str, bpm: int, sound_type: str) -> Optional[str]:
        """Call Hugging Face text-to-audio API - Currently using local fallback due to API permissions"""
        try:
            # Try a different audio generation model
            model_url = f"{self.base_url}/facebook/musicgen-small"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # More specific prompt for music generation
            audio_prompt = f"{sound_type} rhythm {bpm} BPM therapeutic beat medical rehabilitation"
            
            payload = {
                "inputs": audio_prompt,
                "parameters": {
                    "max_new_tokens": 512,
                    "do_sample": True
                }
            }
            
            response = requests.post(model_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                logging.info("Successfully generated audio via API")
                return f"api_audio:{sound_type}:{bpm}"
            else:
                logging.warning(f"API request failed: {response.status_code} - {response.text}")
                # Return local audio generation instead
                return self._generate_local_audio_url(bpm, sound_type)
                
        except Exception as e:
            logging.warning(f"Audio API unavailable, using local generation: {str(e)}")
            # Fallback to local audio generation
            return self._generate_local_audio_url(bpm, sound_type)
    
    def _generate_local_audio_url(self, bpm: int, sound_type: str) -> str:
        """Generate local audio configuration for client-side generation"""
        return f"local_audio:{sound_type}:{bpm}"
    
    def get_optimal_bpm_for_stroke_therapy(self, session_type: str, patient_condition: Dict) -> int:
        """Get optimal BPM based on stroke therapy guidelines"""
        severity = patient_condition.get('severity', 'moderate')
        
        if session_type == "gait_trainer":
            if severity == 'severe':
                return 40
            elif severity == 'moderate':
                return 50
            else:  # mild
                return 60
                
        elif session_type in ["upper_limb_motor", "cognitive_rhythm"]:
            if severity == 'severe':
                return 45
            elif severity == 'moderate':
                return 55
            else:  # mild
                return 65
                
        elif session_type in ["melodic_intonation", "speech_rhythm"]:
            dysarthria = patient_condition.get('dysarthria_severity', 'mild')
            if dysarthria == 'severe':
                return 50
            elif dysarthria == 'moderate':
                return 65
            else:  # mild or none
                return 80
                
        return 60  # default
    
    def get_available_sounds(self) -> Dict:
        """Get list of available beat sounds"""
        return self.beat_sounds

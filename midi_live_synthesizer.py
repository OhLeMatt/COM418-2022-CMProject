# ----------------------------------------------------------
# Pure prototype, not even half-way to first test
# ----------------------------------------------------------



import mido
from threading import Thread, Event
import sounddevice as sd
import numpy as np
import midi_utils as mu
import time
from utils import stereo_sound


# def fade(start_fade, end_fade, sample_count, )


MAX_SAMPLE_COUNT = 4096
DEFAUT_SF = MAX_SAMPLE_COUNT * 8
MIDI_FREQ_SINES = []

t = np.arange(MAX_SAMPLE_COUNT*4) / DEFAUT_SF
for freq in mu.MIDI_FREQS:
    k = int(MAX_SAMPLE_COUNT*2 / (DEFAUT_SF / freq)) + 1
    circular_frames = int(k * DEFAUT_SF / freq)
    MIDI_FREQ_SINES.append(np.sin(2 * np.pi * freq * t[:circular_frames])[:MAX_SAMPLE_COUNT*2]) 

MIDI_FREQ_SINES = np.array(MIDI_FREQ_SINES)

def fast_synthesize(midi_ids, start_index, sample_count, envelope=1.0):
    
    if sample_count > MAX_SAMPLE_COUNT:
        raise ValueError(f"sample_count should be below MAX_SAMPLE_COUNT={MAX_SAMPLE_COUNT}")
    
    local_start_index = start_index % MAX_SAMPLE_COUNT
    local_end_index = local_start_index + sample_count
    sounds = MIDI_FREQ_SINES[midi_ids, local_start_index:local_end_index]
    if type(envelope) is float or type(envelope) is np.ndarray and envelope.shape[0] == sample_count:
        return np.sum(sounds, axis=0) * envelope
    elif type(envelope) is dict:
        for selec, envlp in envelope.items():
            sounds[selec] *= envlp
            
        return np.sum(sounds, axis=0)
    

class MidiLiveSynthesizer(mido.ports.BaseOutput):
    
    def __init__(self, sample_count=1024, **kwargs):
        super().__init__(**kwargs)
            
        self.last_sound_update_time = time.time()
        self.idx = 0
        self.midx = 0
        self.stop_now = False
        self.mute = False
        self.volume = False
        self.exit_event = Event()
        
        self.balance = 0
        self.interval_duration = 0.4
        self.midi_ids_on = {}
        self.midi_ids_off = {}
        self.current_envelope = 1
        
        def play_output_stream():
            def output_callback(outdata, frames, time, status):
                if self.mute:
                    outdata[:] = np.zeros((frames, 2))
                elif self.stop_now:
                    self.stop_now = True
                    raise sd.CallbackAbort()
                else:
                    current_active_midi_ids = []
                    sound = fast_synthesize(current_active_midi_ids, self.idx, frames, self.current_envelope)
                    
                    outdata[:] = stereo_sound(sound, sound, min(1-self.balance, 1.0), min(1+self.balance, 1.0))
                self.last_sound_update_time = time.time()
                self.idx += frames
                for i in range(16):
                    self.midi_ids_off[i].clear()
                    self.midi_ids_on[i].clear()
                
            with sd.OutputStream(channels=2, callback=output_callback, blocksize=sample_count, samplerate=DEFAUT_SF):
                while not self.exit_event.is_set():
                    self.exit_event.wait(self.interval_duration)
        
    def send(self, message):
        byts = message.bytes()
        self.midx = self.idx + int((time.time() - self.last_sound_update_time) * DEFAUT_SF)
        typ = byts[0] & 0xF0
        channel = byts[0] & 0x0F
        if typ == 144: # note_on
            self.midi_ids_on[channel].append(byts[1])
            
        elif byts[0] & 0xF0 == 128:  # note_off
            self.midi_ids_off[channel].append(byts[1])
        
        print(message, byts)
    


a = MidiLiveSynthesizer()
a.send(mido.Message("note_on", note=50))
a.send(mido.Message("note_off", note=50, time=20, channel=2))
a.send(mido.Message("note_on", note=50, time=20))
a.send(mido.Message("note_off", note=50, time=20))

# with mido.open_input() as test:
#     print(test)




import mido
import midi_utils as mu
import scales
from midi_frame import MidiFrame
from pretty_midi import PrettyMIDI
import sounddevice as sd
import numpy as np
from utils import stereo_sound

class MidiPlayer: 
    def __init__(self, 
                 file_name, 
                 path,
                 volume=0.5,
                 sample_frequency=22050):
        self.file_name = file_name 
        self.path = path
        self.playing = False
        self.cursor = {
            "idx": 0,
            "time": 0,
            "bartime": 0,
            "ticks": 0
        }
        
        self.on_cursor_change_listeners = set()
        
        self.channels = [i for i in range(16)]
        self.as_mido = mido.MidiFile(filename=self.file_name)
        
        self.midiframe = MidiFrame(self.as_mido)

        self.Fs = sample_frequency
        
        self.stop_now = False
        self.mute = False
        self.volume = volume
        
        self.balance = 0
        
        self.ctx = sd._CallbackContext(loop=False)
        self.ctx.output_channels = 2
        
        def output_callback(outdata, frame_count, time, status):
            assert len(outdata) == frame_count
            self.ctx.callback_enter(status, outdata)

            if self.playing:
                if self.stop_now:
                    self.stop_now = True
                    raise sd.CallbackAbort()
                elif not self.mute:
                    sound = self.volume * self.audio_data[self.cursor["idx"]:self.cursor["idx"]+frame_count]
                    outdata[:len(sound)] = stereo_sound(sound, sound, min(1-self.balance, 1.0), min(1+self.balance, 1.0))
            
                self.update_cursor(self.cursor["idx"] + frame_count, call_listeners=True)
            self.ctx.callback_exit()

        self.output_callback = output_callback
    
        self.refresh_dataframe()
        
    
    def refresh_dataframe(self):
        self.midiframe.make_playing_track_frame(self.channels)
        self.df = self.midiframe.playing_track_frame.dataframe
        
        #self.displayable = True if ('note' in self.df and self.df["time_duration"].iloc[1] is not None) else False
        # self.displayable = True if 'note' in self.df else False
        self.displayable = True
        
        if self.displayable and len(self.df) > 0: 
            self.min_note = self.df['note'].min()
            self.max_note = self.df['note'].max()
            self.length = self.df["ticks"].iloc[-1] + 5
            print("midi length: " + str(self.length))
        self.midiframe.export_playing_track()
        
        # music = PrettyMIDI(midi_file=file_name)
        music = PrettyMIDI(midi_file="MIDI_Files/tmp.mid")
        was_playing = self.playing
        self.stop()
        self.audio_data = music.synthesize(fs=self.Fs)
        self.ctx.frames = self.ctx.check_data(self.audio_data, None, sd.default.device)
        if was_playing:
            self.play()
            
    def update_cursor(self, cursor, call_listeners=False):
        if cursor != self.cursor["idx"]:
            if cursor < 0:
                cursor = 0
            self.cursor["idx"] = cursor
            self.cursor["time"] = self.cursor["idx"]/self.Fs
            
            if cursor == 0:
                self.cursor["ticks"] = 0
                self.cursor["bartime"] = 0
            else:
                self.cursor["ticks"] = self.midiframe.converters["time"].to_ticks(self.cursor["time"])
                self.cursor["bartime"] = self.midiframe.converters["bartime"].to_bartime(self.cursor["ticks"])
            
            if call_listeners:
                for callback in self.on_cursor_change_listeners:
                    callback(self)
        
        
        # print(self.df.iloc[self.df_cursor])
    def add_channel(self, channel):
        if channel not in self.channels: 
            self.channels.append(channel)
            self.refresh_dataframe()
        
    def remove_channel(self, channel):
        if channel in self.channels: 
            self.channels.remove(channel)
            self.refresh_dataframe()

    def play(self):
        if not self.playing:
            self.playing = True
            self.ctx.start_stream(sd.OutputStream, self.Fs, 2, 
                                self.ctx.output_dtype, self.output_callback, False,
                                prime_output_buffers_using_stream_callback=False)
            
    def pause(self):
        if self.playing:
            self.playing = False
            sd.stop()

    def stop(self):
        self.update_cursor(0, call_listeners=True)
        self.playing = False
        sd.stop()
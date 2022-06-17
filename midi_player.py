
from turtle import update
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
        self.analysis_window = [0, 0]
        self.analysis_window_extent = [-2, 2]
        
        self.on_cursor_change_listeners = []
        
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
            
                self.update_cursor(self.cursor["idx"] + frame_count, exclude_listeners=False)
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
            
    def update_cursor(self, cursor, metric="idx", exclude_listeners=True):
        if cursor <= 0:
            for k in self.cursor:
                self.cursor[k] = 0
        elif metric == "idx" and cursor != self.cursor["idx"]:
            self.cursor["idx"] = cursor
            
            self.cursor["time"] = self.cursor["idx"]/self.Fs
            self.cursor["ticks"] = self.midiframe.converters["time"].to_ticks(self.cursor["time"])
            self.cursor["bartime"] = self.midiframe.converters["bartime"].to_bartime(self.cursor["ticks"])
        elif metric == "ticks" and cursor != self.cursor["ticks"]:
            self.cursor["ticks"] = cursor
            
            self.cursor["bartime"] = self.midiframe.converters["bartime"].to_bartime(self.cursor["ticks"])
            self.cursor["time"] = self.midiframe.converters["time"].to_time(self.cursor["ticks"])
            self.cursor["idx"] = int(self.cursor["time"] * self.Fs)
        elif metric == "time" and cursor != self.cursor["time"]:
            self.cursor["time"] = cursor

            self.cursor["idx"] = int(self.cursor["time"] * self.Fs)
            self.cursor["ticks"] = self.midiframe.converters["time"].to_ticks(self.cursor["time"])
            self.cursor["bartime"] = self.midiframe.converters["bartime"].to_bartime(self.cursor["ticks"])
        elif metric == "bartime" and cursor != self.cursor["bartime"]:
            self.cursor["bartime"] = cursor
            
            self.cursor["ticks"] = self.midiframe.converters["bartime"].to_ticks(self.cursor["bartime"])
            self.cursor["time"] = self.midiframe.converters["time"].to_time(self.cursor["ticks"])
            self.cursor["idx"] = int(self.cursor["time"] * self.Fs)
        
        self.update_window()   
         
        if exclude_listeners == False:
            for callback in self.on_cursor_change_listeners:
                callback(self)
        elif type(exclude_listeners) is list:
            for listener_index, callback in enumerate(self.on_cursor_change_listeners):
                if listener_index not in exclude_listeners:
                    callback(self)
    
    def update_window(self, barsize=None):
        if barsize is not None:
            self.analysis_window_extent[1] = barsize//2
            self.analysis_window_extent[0] = barsize - self.analysis_window_extent[1]
        self.analysis_window[0] = int(self.cursor["bartime"]) - self.analysis_window_extent[0]
        self.analysis_window[1] = int(self.cursor["bartime"]) + self.analysis_window_extent[1]
        
    def convert_unit(self, value, from_metric, to_metric):
        if from_metric == to_metric:
            return value
        if from_metric == "bartime":
            ticks = self.midiframe.converters["bartime"].to_ticks(value)
            if to_metric == "ticks":
                return ticks
            else:
                time = self.midiframe.converters["time"].to_time(ticks)
                return time if to_metric == "time" else int(time * self.Fs)
        elif from_metric == "ticks":
            if to_metric == "bartime":
                return self.midiframe.converters["bartime"].to_bartime(value)
            else:
                time = self.midiframe.converters["time"].to_time(value)
                return time if to_metric == "time" else int(time * self.Fs)
        elif from_metric == "time":
            if to_metric in ("ticks", "bartime"):
                ticks = self.midiframe.converters["time"].to_ticks(value)
                return ticks if to_metric == "ticks" else self.midiframe.converters["bartime"].to_bartime(ticks)
            else:
                return int(value * self.Fs)
        elif from_metric == "idx":
            time = value / self.Fs
            if to_metric == "time":
                return time
            else:
                ticks = self.midiframe.converters["time"].to_ticks(time)
                return ticks if to_metric == "ticks" else self.midiframe.converters["bartime"].to_bartime(ticks)
            
    def add_channel(self, channel):
        if channel not in self.channels: 
            self.channels.append(channel)
            self.refresh_dataframe()
            return True
        return False
        
    def remove_channel(self, channel):
        if channel in self.channels: 
            self.channels.remove(channel)
            self.refresh_dataframe()
            return True
        return False

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
        self.update_cursor(0, exclude_listeners=False)
        self.playing = False
        sd.stop()

    def get_suggestion(self):
        dummy = [{"name": "Hard Japan descending", "accuracy": 0.9, "note_count": 5, "alternate_names": "Raga Malkauns, Blues Pentatonic Minor"}, 
        {"name": "Enigmatic Descending", "accuracy": 0.78, "note_count": 7, "alternate_names": "Katadianas"}, 
        {"name": "Major Lydian", "accuracy": 0.53, "note_count": 8, "alternate_names": "Genus Diatonicum Veterum Correctum, Zylyllic, Ishikotsucho (Japan)"}]

        return dummy 
    
    def set_volume(self, volume):
        self.volume = max(min(volume, 10.0), 0.0)/10

from cv2 import trace
import mido
import midi_utils as mu
import numpy as np
import pandas as pd
import scales
import os
import tempfile

class MidiTrackFrame:

    def __init__(self, 
                 track: mido.MidiTrack, 
                 ticks_per_beat,
                 tempos, 
                 time_signatures,
                 track_name=None, 
                 compute_dataframe=True,
                 related_track_names=[]):
        self.name = track.name.strip() if track_name is None else track_name
        self.ticks_per_beat = ticks_per_beat
        self.meta_only =  True
        self.channel_count = {}
        self.unique_channel = None
        # self.cc_count = {}
        self.meta_count = 0
        self.typeset = set()
        self.track = track
        
        self.dataframe : pd.DataFrame = None #type:ignore
        if compute_dataframe:
            self.dataframe = mu.track_to_dataframe(track, ticks_per_beat, tempos, time_signatures)
        self.related_track_names = related_track_names
        
        for message in track:    
            self.typeset.add(message.type)
            if message.is_meta:
                self.meta_count += 1
            else:
                if message.type != "sysex":
                    self.meta_only = False
                    if message.channel not in self.channel_count:
                        self.channel_count[message.channel] = 0
                    self.channel_count[message.channel] += 1
                    
                    # if message.is_cc():
                    #     if message.channel not in self.cc_count:
                    #         self.cc_count[message.channel] = 0
                    #     self.cc_count[message.channel] += 1
        if len(self.channel_count.keys()) == 1:
            self.unique_channel = list(self.channel_count.keys())[0]

    def __repr__(self):
        rep = self.name
        if self.meta_only:
            rep += " (Meta Track):"
        else:    
            rep += ":\n\tMessage count/channel: "
            for channel, count in sorted(self.channel_count.items(), key=lambda a: a[0]):
                rep += f"{channel} ({count}), "
            rep = rep[:-2]
            # rep += "\n\tCC Message count/channel: "
            # for channel, count in sorted(self.cc_count.items(), key=lambda a: a[0]):
            #     rep += f"{channel} ({count}), "
            # rep = rep[:-2]
        
        rep += f"\n\tMeta Message count: {self.meta_count}"
        rep += f"\n\tUsed Message types: "
        for typ in self.typeset:
            rep += f"{typ}, "
        rep = rep[:-2]
        if len(self.related_track_names) > 0:
            rep += f"\n\tRelated Track names: "
            for n in self.related_track_names:
                rep += n + ", "
            rep = rep[:-2]
        return rep + "\n"
    
    def get_sub_dataframe(self,
                          start,
                          end,
                          metric="bartime"):
        mask = (self.dataframe[metric] >= start) & (self.dataframe[metric] < end)
        return self.dataframe[mask]
    
    def suggest_scale(self, 
                      start,
                      end,
                      metric="bartime",
                      weighted=False,
                      **kwargs):
        if start >= end:
            raise ValueError("Argument start should be below end")
        if metric not in ("ticks", "bartime"):
            raise ValueError("Argument metric should be ")
        weights = None
        
        mask = (self.dataframe[metric] >= start) & (self.dataframe[metric] < end)
        found_scales = {}
        if True in np.unique(mask):
            if weighted:
                weights = self.dataframe.custom_beat_weight[mask].to_numpy()
            
            found_scales = scales.suggest_scales(mu.to_chroma(self.dataframe.note[mask].to_numpy()), 
                                weights=weights, 
                                **kwargs)
            
        return found_scales


class MidiFrame:
    
    def __init__(self, 
                 midofile: mido.MidiFile, 
                 info_type="dispatched", 
                 **kwargs):
        
        if info_type not in ("all", "filtered", "dispatched"):
            raise ValueError("info_type should be among 'all', 'filtered', 'dispatched")
        
        self.midi_type = midofile.type
        self.midi_clip = midofile.clip
        self.midi_charset = midofile.charset
        self.info_type = info_type
        self.filename = midofile.filename
        self.midi_type = midofile.type
        self.track_count = len(midofile.tracks)
        self.time_signatures = []
        self.tempos = []
        self.music_track_count = 0
        self.ticks_per_beat = midofile.ticks_per_beat
        self.length = midofile.length
        self.track_frames = []
        self.playing_track_frame: MidiTrackFrame = None #type:ignore
        self.playing_midi_file = tempfile.TemporaryFile()
        
        time = 0
        for message in mido.merge_tracks(midofile.tracks):
            time += message.time
            if message.is_meta:
                if message.type == "set_tempo" \
                    and (len(self.tempos) == 0 or self.tempos[-1].tempo != message.tempo):
                    new_msg = message.copy()
                    new_msg.time = time
                    self.tempos.append(new_msg)
                elif message.type == "time_signature" \
                    and (len(self.time_signatures) == 0 \
                        or not (self.time_signatures[-1].numerator == message.numerator and self.time_signatures[-1].denominator == message.denominator)):
                    new_msg = message.copy()
                    new_msg.time = time
                    self.time_signatures.append(new_msg)
        
        if info_type in ("all", "filtered"):
            for t in midofile.tracks:
                mtf = MidiTrackFrame(t, 
                                     self.ticks_per_beat, 
                                     self.tempos, 
                                     self.time_signatures,
                                     compute_dataframe=False)
                self.track_frames.append(mtf)
                if not mtf.meta_only:
                    self.music_track_count += 1
            if info_type == "filtered":
                self.filter_track_frames(**kwargs)
        else:
            self.dispatch_tracks_by_channel(midofile, **kwargs)
        
        self.track_frames = sorted(self.track_frames, key=lambda a: a.name)
        self.make_playing_track_frame(kwargs.get("channels", {0}), 
                                      kwargs.get("only_unique_channel", False))
            

    def __repr__(self):
        rep = ""
        for k in ("info_type", "filename", "midi_type", "track_count", "music_track_count", "ticks_per_beat", "length"):
            key_name = k.replace("_", " ").capitalize()
            rep += f"{key_name}: {self.__dict__[k]}\n"
        for track_frame in self.track_frames:
            rep += track_frame.__repr__()
        if len(self.time_signatures) > 0:
            rep += f"\n\tTime signatures: "
            for message in self.time_signatures:
                rep += f"{message.numerator}/{message.denominator} ({message.time}), "
            rep = rep[:-2]
        
        if len(self.tempos) > 0:
            rep += f"\n\tTempos: "
            for message in self.tempos:
                rep += f"{message.tempo} ({message.time}), "
            rep = rep[:-2]
        
        return rep + "\n"
        
    def make_playing_track_frame(self, channels, only_unique_channel=False):
        tracks = []
        channels = set(channels)
        for track_frame in self.track_frames:
            if (only_unique_channel and track_frame.unique_channel in channels) \
                    or (not only_unique_channel and not set(track_frame.channel_count.keys()).isdisjoint(channels)):
                tracks.append(track_frame.track)
        
        self.playing_track_frame = MidiTrackFrame(mido.merge_tracks(tracks), 
                                                  self.ticks_per_beat, 
                                                  self.tempos, 
                                                  self.time_signatures, 
                                                  "Playing Track")

    def export_playing_track(self):
        tracks = []
        for track_frame in self.track_frames:
            if track_frame.meta_only:
                tracks.append(track_frame.track)
        tracks.append(self.playing_track_frame.track)
        
        playing_midi = mido.MidiFile(type=0 if len(tracks) == 1 else min(1, self.midi_type), 
                                     ticks_per_beat=self.ticks_per_beat, 
                                     charset=self.midi_charset,
                                     debug=False,
                                     clip =self.midi_clip,
                                     tracks=tracks)
        playing_midi.save("MIDI_Files/tmp.mid")
        

    def filter_track_frames(self,
                            only=False,
                            filter_irrelevant_meta_tracks=True):

        for ti in range(self.track_count)[::-1]:
            track_frame = self.track_frames[ti]
            if track_frame.meta_only:
                if only == "meta" \
                    or filter_irrelevant_meta_tracks \
                        and track_frame.typeset.isdisjoint({'smpte_offset', 'set_tempo', 'key_signature', 'time_signature'}):
                    
                    del self.track_frames[ti]
                    self.track_count -= 1
            elif only == "music":
                del self.track_frames[ti]
                self.track_count -= 1
                self.music_track_count -= 1
                

    def dispatch_tracks_by_channel(self, midofile, **kwargs):
        time = 0
        channel_set = set()
        sorted_track = mido.MidiTrack()
        for message in mido.merge_tracks(midofile.tracks):
            timed_message = message.copy()
            time += message.time
            timed_message.time = time
            sorted_track.append(timed_message)
            if "channel" in message.__dict__:
                channel_set.add(message.channel)
        
        channel_tracks = dict((channel, mido.MidiTrack()) for channel in channel_set)
        meta_track = mido.MidiTrack()
        
        for message in sorted_track:
            if message.is_meta and "track_name" not in message.__dict__ :
                meta_track.append(message.copy())
            elif "channel" in message.__dict__:
                channel_tracks[message.channel].append(message.copy())
        
        if len(meta_track) > 0:
            previous_time = 0
            for message in meta_track:
                tmp_time = message.time
                message.time = tmp_time - previous_time
                previous_time = tmp_time
            
            self.track_frames.append(MidiTrackFrame(meta_track,
                                                    self.ticks_per_beat, 
                                                    self.tempos, 
                                                    self.time_signatures,
                                                    compute_dataframe=False,
                                                    track_name="Meta"))
        
        related_track_names = [[] for _ in range(16)]
        for track in midofile.tracks:
            channels = set()
            for m in track:
                try:
                    channels.add(m.channel)
                except:
                    pass
            for channel in channels:
                related_track_names[channel].append(track.name.strip())
        
        for channel, channel_track in channel_tracks.items():
            if len(channel_track) > 0:
                previous_time = 0
                for message in channel_track:
                    tmp_time = message.time
                    message.time = tmp_time - previous_time
                    previous_time = tmp_time
                
                self.track_frames.append(MidiTrackFrame(channel_track,
                                                        ticks_per_beat=self.ticks_per_beat, 
                                                        tempos=self.tempos, 
                                                        time_signatures=self.time_signatures,
                                                        track_name=f"Channel {channel:02}",
                                                        compute_dataframe=False,
                                                        related_track_names=related_track_names[channel]))
                
        for track_frame in self.track_frames:
            if not track_frame.meta_only:
                self.music_track_count += 1

            
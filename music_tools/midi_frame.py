import mido
import numpy as np
import pandas as pd
import os

import music_tools.midi_utils as mu
import music_tools.scales as scales
from music_tools.chords import ChordSuggester

class MidiTrackFrame:

    def __init__(self, 
                 track: mido.MidiTrack, 
                 converters,
                 track_name=None, 
                 compute_dataframe=True,
                 related_track_names=[]):
        self.name = track.name.strip() if track_name is None else track_name
        
        self.meta_only =  True
        self.channel_count = {}
        self.unique_channel = None
        # self.cc_count = {}
        self.meta_count = 0
        self.typeset = set()
        self.track = track
        self.related_track_names = related_track_names
        
        self.dataframe : pd.DataFrame = None #type:ignore
        
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
            
        if compute_dataframe:
            self.dataframe = mu.track_to_dataframe(track, 
                                                   converters["time"],
                                                   converters["bartime"])

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
                          metric="bartime",
                          columns=[]):
        
        mask = (self.dataframe[metric] >= start) & (self.dataframe[metric+"_release"] < end)
        if not np.any(mask):
            return None
        if len(columns) == 0:
            return self.dataframe.loc[mask]
        else:
            return self.dataframe.loc[mask, columns]
    
    def suggest_scale(self, 
                      start,
                      end,
                      metric="bartime",
                      weighted=False,
                      **kwargs):
        """Suggest Scale

        Args:
            start (float,int): The beggining of the analysis window in the metric you want ("bartime", "time", "ticks")
            end (float,int): The end of the analysis window in the metric you want ("bartime", "time", "ticks")
            metric (str, optional): The metric for start and end. Defaults to "bartime".
            weighted (bool, optional): If the weight should be applied in the analysis. Defaults to False.
        Kwargs:
            normalize_score(bool): Normalize the score, 
            threshold (float): Between 0 and 1, the threshold on scores to filter suggestions. Default to 0.99.
            normalize_accuracy (float): If True, will normalize all scores before threshold pass. Default to True.
            tonic_chromas (list(int)): List of allowed chroma for being the tonic. Default to mu.CHROMA_IDS.
            general_scale_subset (list(scales.GeneralScale)): Set of scale on which the analysis will be performed. Default to ALL_GENERAL_SCALES.
            
        
        Raises:
            ValueError: start should be strictly inferior to end
            ValueError: metric should be in ("ticks", "bartime", "time")

        Returns:
            _type_: _description_
        """
        if start >= end:
            raise ValueError(f"Argument start should be below end, current start={start}, end={end}")
        if metric not in ("ticks", "bartime", "time"):
            raise ValueError("Argument metric should be in (ticks, bartime, time)")
        weights = None
        
        mask = (self.dataframe[metric] >= start) & (self.dataframe[metric+"_release"] < end)
        found_scales = []
        
        if np.any(mask):
            
            if weighted:
                weights = self.dataframe.weight[mask].to_numpy()
            
            found_scales = scales.suggest_scales(mu.to_chroma(self.dataframe.note[mask].to_numpy()), 
                                                weights=weights, 
                                                **kwargs)
            
        return found_scales
    
    
    def suggest_chord(self, 
                      start,
                      end,
                      scale,
                      nb_note,
                      nb_chord,
                      w_similarity,
                      w_harmony,
                      w_consonance,
                      metric="bartime"):
        
        if start >= end:
            raise ValueError(f"Argument start should be below end, current start={start}, end={end}")
        if metric not in ("ticks", "bartime", "time"):
            raise ValueError("Argument metric should be in (ticks, bartime, time)")
        
        mask = (self.dataframe[metric] >= start) & (self.dataframe[metric+"_release"] < end)
        found_chords = []
        if True in np.unique(mask):
            sug = ChordSuggester(nb_note, scale, mu.to_chroma(self.dataframe.note[mask].to_numpy()),
                            w_similarity, w_harmony, w_consonance)
            
            found_chords = sug.suggest_chords(nb_chord)    
        return found_chords


class MidiFrame:
    EXPORT_DEFAULT_DIRPATH = "TMP_Files"
    EXPORT_DEFAULT_FILEPATH = "TMP_Files/tmp.mid"
    
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
        self.track_count = len(midofile.tracks)
        self.converters = {}
        self.music_track_count = 0
        self.ticks_per_beat = midofile.ticks_per_beat
        self.length = midofile.length
        self.track_frames = []
        self.playing_track_frame: MidiTrackFrame = None #type:ignore
        # self.playing_midi_file = tempfile.TemporaryFile()
        
        
        ticks = 0
        tempos = []
        timesigs = []
        last_tempo_ticks = 0
        last_timesig_ticks = 0
        for message in mido.merge_tracks(midofile.tracks):
            ticks += message.time
            if message.is_meta:
                if message.type == "set_tempo" \
                    and (len(tempos) == 0 or tempos[-1].tempo != message.tempo):
                    new_msg = message.copy()
                    if len(tempos) > 0 and last_tempo_ticks == ticks:
                        new_msg.time = tempos[-1].time
                        tempos[-1] = new_msg
                    else:
                        new_msg.time = ticks - last_tempo_ticks
                        tempos.append(new_msg)
                    last_tempo_ticks = ticks
                elif message.type == "time_signature" \
                    and (len(timesigs) == 0 \
                        or not (timesigs[-1].numerator == message.numerator and timesigs[-1].denominator == message.denominator)):
                    new_msg = message.copy()
                    if len(timesigs) > 0 and last_timesig_ticks == ticks:
                        new_msg.time = tempos[-1].time
                        timesigs[-1] = new_msg
                    else:
                        new_msg.time = ticks - last_timesig_ticks
                        timesigs.append(new_msg)
                    last_timesig_ticks = ticks
        self.converters["time"] = mu.TicksTimeConverter(tempos_with_ticks=tempos, 
                                                        ticks_per_beat=self.ticks_per_beat)
        self.converters["bartime"] = mu.TicksBartimeConverter(timesigs_with_ticks=timesigs, 
                                                              ticks_per_beat=self.ticks_per_beat)
        
        if info_type in ("all", "filtered"):
            for t in midofile.tracks:
                mtf = MidiTrackFrame(t, 
                                     converters=self.converters,
                                     compute_dataframe=False)
                self.track_frames.append(mtf)
                if not mtf.meta_only:
                    self.music_track_count += 1
            if info_type == "filtered":
                self.filter_track_frames(**kwargs)
        else:
            self.dispatch_tracks_by_channel(midofile, **kwargs)
        
        self.track_frames = sorted(self.track_frames, key=lambda a: a.name)
        
        

    def __repr__(self):
        rep = ""
        for k in ("info_type", "filename", "midi_type", "track_count", "music_track_count", "ticks_per_beat", "length"):
            key_name = k.replace("_", " ").capitalize()
            rep += f"{key_name}: {self.__dict__[k]}\n"
        for track_frame in self.track_frames:
            rep += track_frame.__repr__()
        if self.converters["bartime"].event_count > 0:
            rep += f"\n\tTime signatures: "
            for event in self.converters["bartime"].events:
                rep += "{}/{} ({}), ".format(event[0][0], event[0][1], event[2])
            rep = rep[:-2]
        
        if self.converters["time"].event_count > 0:
            rep += f"\n\tTempos: "
            for event in self.converters["time"].events:
                rep += "{} ({}), ".format(event[0], event[2])
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
                                                  converters=self.converters,
                                                  track_name="Playing Track")

    def export_playing_track(self):
        if not os.path.exists(self.EXPORT_DEFAULT_DIRPATH):
            os.makedirs(self.EXPORT_DEFAULT_DIRPATH)
        
        tracks = []
        for track_frame in self.track_frames:
            if track_frame.meta_only:
                tracks.append(track_frame.track)
        tracks.append(self.playing_track_frame.track)
        
        playing_midi = mido.MidiFile(type=0 if len(tracks) == 1 else max(1, self.midi_type), 
                                     ticks_per_beat=self.ticks_per_beat, 
                                     charset=self.midi_charset,
                                     debug=False,
                                     clip =self.midi_clip,
                                     tracks=tracks)
        playing_midi.save(self.EXPORT_DEFAULT_FILEPATH)

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
                                                    converters=self.converters,
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
                                                        converters=self.converters,
                                                        track_name=f"Channel {channel:02}",
                                                        compute_dataframe=False,
                                                        related_track_names=related_track_names[channel]))
                
        for track_frame in self.track_frames:
            if not track_frame.meta_only:
                self.music_track_count += 1

            
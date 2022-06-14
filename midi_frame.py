import mido
from copy import deepcopy

class MidiTrackFrame:

    def __init__(self, track: mido.MidiTrack, track_name=None, related_track_names=[]):
        
        self.name = track.name.strip() if track_name is None else track_name
        self.meta_only =  True
        self.channel_count = {}
        self.cc_count = {}
        self.meta_count = 0
        self.typeset = set()
        self.track = track
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
                    
                    if message.is_cc():
                        if message.channel not in self.cc_count:
                            self.cc_count[message.channel] = 0
                        self.cc_count[message.channel] += 1

    def __repr__(self):
        rep = self.name
        if self.meta_only:
            rep += " (Meta Track):"
        else:    
            rep += ":\n\tMessage count/channel: "
            for channel, count in sorted(self.channel_count.items(), key=lambda a: a[0]):
                rep += f"{channel} ({count}), "
            else:
                rep = rep[:-2]
            rep += "\n\tCC Message count/channel: "
            for channel, count in sorted(self.cc_count.items(), key=lambda a: a[0]):
                rep += f"{channel} ({count}), "
            rep = rep[:-2]
        
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
    
class MidiFrame:
    
    def __init__(self, 
                 midofile: mido.MidiFile, 
                 info_type="dispatched", 
                 **kwargs):
        
        if info_type not in ("all", "filtered", "dispatched"):
            raise ValueError("info_type should be among 'all', 'filtered', 'dispatched")
        
        self.info_type = info_type
        self.filename = midofile.filename
        self.midi_type = midofile.type
        self.track_count = len(midofile.tracks)
        self.music_track_count = 0
        self.ticks_per_beat = midofile.ticks_per_beat
        self.length = midofile.length
        self.track_frames = []
        
        if info_type in ("all", "filtered"):
            for t in midofile.tracks:
                mtf = MidiTrackFrame(t)
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
        return rep
        

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
        for message in midofile:
            timed_message = message.copy()
            time += message.time
            timed_message.time = time
            sorted_track.append(timed_message)
            if "channel" in message.__dict__:
                channel_set.add(message.channel)
        
        channel_tracks = dict((channel, mido.MidiTrack()) for channel in channel_set)
        meta_track = mido.MidiTrack()
            
        for message in sorted_track:
            if message.is_meta:
                meta_track.append(message.copy())
            elif "channel" in message.__dict__:
                channel_tracks[message.channel].append(message.copy())
        

        
        
        if len(meta_track) > 0:
            previous_time = 0
            for message in meta_track:
                tmp_time = message.time
                message.time = tmp_time - previous_time
                previous_time = tmp_time
            
            self.track_frames.append(MidiTrackFrame(meta_track, "Meta"))
        
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
                                                        f"Channel {channel:02}",
                                                        related_track_names[channel]))
                
        for track_frame in self.track_frames:
            if not track_frame.meta_only:
                self.music_track_count += 1

            
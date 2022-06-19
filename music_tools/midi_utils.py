
import numpy as np
import mido
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from music_tools.temporal_converters import TicksBartimeConverter, TicksTimeConverter
pd.options.mode.chained_assignment = None  # default='warn'

MIDI_IDS = np.arange(128)

def to_chroma(midi_id):
    return midi_id % 12

def to_octave(midi_id):
    return (midi_id // 12) - 1

ALT_NAME_MAP = {"C": "DO", "D": "RE", "E": "MI", "F": "FA", "G": "SOL", "A": "LA", "B":"SI"} 

def name_to_alt_name(name):
    if type(name) is str:
        new_name = ""
        for c in name:
            new_name += ALT_NAME_MAP.get(c, c)
        return new_name
    else:
        new_names = []
        for n in name:
            new_name = ""
            for c in n:
                new_name += ALT_NAME_MAP.get(c, c)
            new_names.append(new_name)
        return new_names

# Midi ids refer here to what people call chroma pitches indices, although we also want to do an analysis being irrelevant of the octave, thus 
# we will also use the "chroma" keyword to designate the 12 different chromatic pitches.

NOTES = {"C": 0, "DO": 0, 
          "C#": 1, "DO#": 1, "Db": 1, "REb":1, "C#/Db":1,
          "D": 2, "RE": 2,
          "D#": 3, "RE#": 3, "Eb": 3, "MIb": 3, "D#/Eb":3,
          "E": 4, "MI": 4,
          "F": 5, "FA": 5,
          "F#": 6, "FA#": 6, "Gb": 6, "SOLb": 6, "F#/Gb":6,
          "G": 7, "SOL": 7,
          "G#": 8, "SOL#": 8, "Ab": 8, "LAb": 8, "G#/Ab":8,
          "A": 9, "LA": 9,
          "A#": 10, "LA#": 10, "Bb": 10, "SIb": 10, "A#/Bb":10,
          "B": 11, "SI": 11}

CHROMA_IDS = np.arange(12)
CHROMA_SHARP_NAMES = np.array(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
CHROMA_FLAT_NAMES = np.array(["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"])
CHROMA_NAMES = np.array([(sharp_name + "/" + flat_name) if sharp_name != flat_name else sharp_name 
                            for sharp_name, flat_name in zip(CHROMA_SHARP_NAMES, CHROMA_FLAT_NAMES)])

CHROMA_ALT_NAMES = np.array(name_to_alt_name(CHROMA_NAMES))

MIDI_SHARP_NAMES = np.array([CHROMA_SHARP_NAMES[to_chroma(midi_id)] + np.str_(to_octave(midi_id)) if midi_id >= 12 else "" 
                                for midi_id in MIDI_IDS])
MIDI_FLAT_NAMES = np.array([CHROMA_FLAT_NAMES[to_chroma(midi_id)] + np.str_(to_octave(midi_id)) if midi_id >= 12 else "" 
                                for midi_id in MIDI_IDS])
MIDI_NAMES = np.array([(sharp_name + "/" + flat_name) if sharp_name != flat_name else sharp_name 
                            for sharp_name, flat_name in zip(MIDI_SHARP_NAMES, MIDI_FLAT_NAMES)])

MIDI_ALT_NAMES = np.array(name_to_alt_name(MIDI_NAMES))

def name_to_midi_id(name):
    octave = -1
    for c in name:
        if c.isnumeric():
            octave = int(c)
    if octave == -1:
        return NOTES[name]
    
    start = (octave + 1)*12
    end = min(start + 12, 128)
    
    indices = np.where(np.char.rfind(a=MIDI_NAMES[start:end], sub=name) >= 0)[0]

    if len(indices) == 0:
        indices = np.where(np.char.rfind(a=MIDI_ALT_NAMES[start:end], sub=name) >= 0)[0]
    if len(indices) == 0:
        raise ValueError("The given name is not correct")
    
    return start + indices[0]

def to_corrected_chroma_names(chroma_names):
    new_chroma_names = []   
    seen_diatonic_tones = set([name.strip("#b") for name in chroma_names if "/" not in name])
    
    for name in chroma_names:
        keep = name
        if "/" in name: 
            splits = name.split("/")
            throw_sharp = splits[0][:-1] in seen_diatonic_tones
            throw_flat = splits[1][:-1] in seen_diatonic_tones
            if throw_sharp and not throw_flat:
                keep = splits[1]
            elif throw_flat and not throw_sharp:
                keep = splits[0]
            
            seen_diatonic_tones.add(keep.strip("#b"))

        new_chroma_names.append(keep)
        
    return np.array(new_chroma_names)
    
        

def to_freq(midi_id):
    return np.power(2, (midi_id-69)/12)*440

MIDI_FREQS = to_freq(MIDI_IDS)

def to_midi_id(freq):
    return np.rint(69 + np.log2(np.maximum(1,freq)/440)*12).astype(np.int16)

def to_continuous_midi_id(freq):
    return 69 + np.log2(np.maximum(1,freq)/440)*12

def closest_midi_freq(f):
    return to_freq(to_midi_id(f))

def harmonics_from_midi_id(midi_id, k=8, include_id=False):
    p = np.unique(to_midi_id(to_freq(midi_id) * np.arange(1, k+2)))
    return p[include_id | (p != midi_id)]



def track_to_dataframe(track: mido.MidiTrack, 
                       time_conv: TicksTimeConverter,
                       bartime_conv: TicksBartimeConverter):
    records = []
    current_ticks = 0
    
    pressed_notes = {}
    id = 0
    
    for x in track:
        new_dict = x.__dict__.copy()
        new_dict["ticks"] = new_dict["time"]
        del new_dict["time"]
        
        current_ticks += new_dict["ticks"]
        
        if new_dict["type"] == "note_off" or new_dict["type"] == "note_on" and new_dict["velocity"] == 0:
            former_pressed_note = pressed_notes[new_dict["note"]]
            if former_pressed_note is None:
                # raise ValueError("The given track has a released note that was never pressed in the first place")
                # print("\rThe given track has a released note that was never pressed in the first place")
                pass
            else:
                pressed_record = records[former_pressed_note["id"]]
                pressed_record["ticks_release"] = current_ticks
                pressed_record["velocity_release"] = new_dict["velocity"]
                pressed_notes[new_dict["note"]] = None
        elif new_dict["type"] == "note_on":
            new_dict["ticks"] = current_ticks
            new_dict["ticks_release"] = None
            new_dict["velocity_release"] = None
            pressed_notes[new_dict["note"]] = {"id": id}
            del new_dict["type"]
            records.append(new_dict)
            id += 1
    
    df = pd.DataFrame(records)
    if len(df) > 0:
        df = df.dropna(subset=["ticks_release"]).reset_index()
        
        df["time"] = time_conv.to_time(df["ticks"])
        df["time_release"] = df["time"]
        df["bartime"] = bartime_conv.to_bartime(df["ticks"])
        df["bartime_release"] = df["bartime"]
        mapping = np.argsort(df["ticks_release"])
        
        df["time_release"].iloc[mapping] =  time_conv.to_time(df["ticks_release"][mapping])
        df["bartime_release"].iloc[mapping] = bartime_conv.to_bartime(df["ticks_release"][mapping])
        df["onset"] = df["bartime"] - np.floor(df["bartime"])
        
        weights = []
        last_timesig = bartime_conv.events[0][0]
        updown_beats = get_updown_beats(last_timesig[0])
        for row in df[["ticks", "onset"]].itertuples():
            timesig = bartime_conv.to_timesig(row.ticks)
            if timesig != last_timesig:
                updown_beats = get_updown_beats(timesig[0])
                last_timesig = timesig
            
            weights.append(updown_beats[int(row.onset * len(updown_beats))])
        
        df["weight"] = weights
    
    return df

def get_updown_beats(num, normalized=True):
    """Borrowed from Matthieu's Semester Project
    
        Returns a list of int describing the beat importance/level.
        The process is completely arbitrary, don't refer to it. 
        It's simply based on the prime number decomposition of the numerator of the timesig. 
        Args:
            timesig (str): The time signature giving us information on bar and beat information.
                It is always represented always as a string because signature such as 4/4 exists and would be 
                simplified by the Fraction module.
        Returns:
            list(int): List of n values (n being the numerator of the timesig), filled with weighted value
                showing the beat importance. The lowest value will be 1 (any upbeat) and the highest depends on the complexity 
                of the time signature (the first downbeat)
    """
    
    results = []

    n = int(num)
    for _ in range(n):
        results.append(0)
    
    results[0] = 1

    i = 2
    j = 1
    while i * i <= n:
        if n % i == 0:
            n //= i
            j *= i
            for k in range(j):
                results[k*n] += 1
        else:
            i += 1
            
    if n > 1:
        j *= n
        for k in range(j):
            results[k] += 1
    
    if normalized:
        for i in range(1,num):
            results[i] /= results[0]
        results[0] = 1.0
    
    return results

def plot_music(track_df: pd.DataFrame, 
               chroma_plot=False,
               metric="ticks",
               ax=None, 
               cmap=plt.get_cmap("gist_rainbow")):
    if ax is None:
        _, ax = plt.subplots()
    
    metric_release = metric + "_release"
    
    df_copy = track_df[[metric, "note", metric_release]]
    if chroma_plot:
        df_copy.loc[:, "note"] = to_chroma(df_copy["note"])
    for i, x in df_copy.iterrows():
        rect = patches.Rectangle((x[metric], x.note - 0.5), 
                                 width=x[metric_release] - x[metric], 
                                 height=1, 
                                 linewidth=0.2, 
                                 edgecolor=(0,0,0), 
                                 facecolor=cmap(x.note))
        ax.add_patch(rect)
    
    plt.xlim(df_copy[metric].min() - 1, df_copy[metric_release].max() + 1)
    plt.ylim(df_copy.note.min() - 3, df_copy.note.max() + 3)
    

#   
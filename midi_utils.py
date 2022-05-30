import numpy as np
import mido
import pandas as pd

MIDI_IDS = np.arange(128)

def to_chroma(midi_id):
    return midi_id % 12

def to_octave(midi_id):
    return (midi_id // 12) - 1

ALT_NAME_MAP = {"C": "DO", "D": "RE", "E": "MI", "F": "FA", "G": "SOL", "A": "LA", "B":"SI"} 

def name_to_alt_name(name):
    new_name = ""
    for c in name:
        new_name += ALT_NAME_MAP.get(c, c)
    return new_name

# Midi ids refer here to what people call chroma pitches indices, although we also want to do an analysis being irrelevant of the octave, thus 
# we will also use the "chroma" keyword to designate the 12 different chromatic pitches.

NOTES = {"C": 0, "DO": 0, 
          "C#": 1, "DO#": 1, "Db": 1, "REb"
          "D": 2, "RE": 2,
          "D#": 3, "RE#": 3, "Eb": 3, "MIb": 3,
          "E": 4, "MI": 4,
          "F": 5, "FA": 5,
          "F#": 6, "FA#": 6, "Gb": 6, "SOLb": 6,
          "G": 7, "SOL": 7,
          "G#": 8, "SOL#": 8, "Ab": 8, "LAb": 8,
          "A": 9, "LA": 9,
          "A#": 10, "LA#": 10, "Bb": 10, "SIb": 10,
          "B": 11, "SI": 11}

CHROMA_IDS = np.arange(12)
CHROMA_SHARP_NAMES = np.array(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
CHROMA_FLAT_NAMES = np.array(["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"])
CHROMA_NAMES = np.array([(sharp_name + "/" + flat_name) if sharp_name != flat_name else sharp_name 
                            for sharp_name, flat_name in zip(CHROMA_SHARP_NAMES, CHROMA_FLAT_NAMES)])
CHROMA_ALT_NAMES = np.array([name_to_alt_name(name) for name in CHROMA_NAMES])

MIDI_SHARP_NAMES = np.array([CHROMA_SHARP_NAMES[to_chroma(midi_id)] + np.str_(to_octave(midi_id)) if midi_id >= 12 else "" 
                                for midi_id in MIDI_IDS])
MIDI_FLAT_NAMES = np.array([CHROMA_FLAT_NAMES[to_chroma(midi_id)] + np.str_(to_octave(midi_id)) if midi_id >= 12 else "" 
                                for midi_id in MIDI_IDS])
MIDI_NAMES = np.array([(sharp_name + "/" + flat_name) if sharp_name != flat_name else sharp_name 
                            for sharp_name, flat_name in zip(MIDI_SHARP_NAMES, MIDI_FLAT_NAMES)])

MIDI_ALT_NAMES = np.array([name_to_alt_name(name) for name in MIDI_NAMES])

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

def track_to_dataframe(track, event_style=False):
    records = []
    track_name = ""
    current_time = 0
    # Event style dataframe
    if event_style:
        for x in track:
            new_dict = x.__dict__.copy()
            if not x.is_meta():
                #Swapping name for coherence
                new_dict["time_diff"] = new_dict["time"] 
                current_time += new_dict["time_diff"]
                new_dict["time"] = current_time
                new_dict["pressed"] = new_dict["type"] == "note_on"
                new_dict["released"] = new_dict["type"] == "note_off"
                records.append(new_dict)
    else:
        # Streaming style dataframe
        pressed_notes = {}
        id = 0
        for x in track:
            new_dict = x.__dict__.copy()
            if new_dict["type"] == "track_name":
                track_name = new_dict["name"]
            else:
                current_time += new_dict["time"]
                new_dict["time"] = current_time
                new_dict["time_release"] = None
                new_dict["time_duration"] = None
                new_dict["velocity_release"] = None
                if new_dict["type"] == "note_off":
                    former_pressed_note = pressed_notes[new_dict["note"]]
                    if former_pressed_note is None:
                        raise ValueError("The given track has a released note that was never pressed in the first place")
                    pressed_record = records[former_pressed_note["id"]]
                    pressed_record["time_release"] = current_time
                    pressed_record["time_duration"] = current_time - pressed_record["time"]
                    pressed_record["velocity_release"] = new_dict["velocity"]
                    pressed_notes[new_dict["note"]] = None
                elif new_dict["type"] == "note_on":
                    pressed_notes[new_dict["note"]] = {"id": id}
                    del new_dict["type"]
                    records.append(new_dict)
                    id += 1
                                        
    return pd.DataFrame(records)

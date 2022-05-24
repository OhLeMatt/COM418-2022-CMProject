from re import sub
from matplotlib.style import available
import numpy as np
from scipy.fftpack import shift, ss_diff
import pandas as pd
from sklearn.preprocessing import scale
import midi_utils as mu
from utils import base_to_list

def music_to_tonic_chroma(midi_ids):
    """Difficult and WIP heuristic to find the tonic. Needs accurate research

    Args:
        midi_ids (np.ndarray(int)): the music in midi id notes

    Returns:
        int: tonic in chroma id notes (0 to 11)
    """
    notes, counts = np.unique(mu.to_chroma(midi_ids), return_counts=True)
    
    return notes[counts.argmax()]

def music_to_chroma_shifts(midi_ids, tonic_chroma):
    shifts = np.diff(np.unique(mu.to_chroma(midi_ids) - tonic_chroma))
    remainder = 12 - shifts.sum()
    if remainder > 0:
        shifts = np.append(shifts, remainder)
    
    return shifts

class ChromaBitmap:
    
    def __init__(self, sucessive_shifts=[]) -> None:
        self.bitmap = 0
        self.set(np.array(sucessive_shifts))
        
    def set(self, index) -> None:
        self.bitmap |= np.sum(1 << (np.array(index) % 12))
        
    def set_map(self, other) -> None:
        self.bitmap |= other
        
    def unset(self, index) -> None:
        self.bitmap &= ~np.sum((1 << np.array(index)))
        
    def unset_map(self, other) -> None:
        self.bitmap &= ~other
    
    def on(self, index) -> bool:
        return (1 << np.array(index)) & self.bitmap != 0
    
    def off(self, index) -> bool:
        return ~(1 << np.array(index)) & self.bitmap != 0
    
    def contains(self, other) -> bool:
        return self.bitmap & other == other
    
    def is_contained(self, other) -> bool:
        return self.bitmap & other == self.bitmap
    
    def union(self, other) -> bool:
        return self.bitmap | other
    
    def inter(self, other) -> bool:
        return self.bitmap & other
    
    def indices_on(self) -> list:
        return mu.CHROMA_IDS[self.on(mu.CHROMA_IDS)]
    
    def indices_off(self) -> list:
        return mu.CHROMA_IDS[self.off(mu.CHROMA_IDS)]
    
    def __str__(self):
        return f"{self.bitmap:012b}"
    
    def __repr__(self):
        return self.__str__()
    
    def __call__(self):
        return self.bitmap
    
class Scale:
    def __init__(self, shifts, tonic_chroma, name="Untitled"):
        self.tonic_chroma = mu.to_chroma(tonic_chroma)
        self.shifts = np.array(shifts)
        if len(self.shifts) != 0:
            self.successive_shifts = Scale.compute_successive_shifts(self.shifts)
            self.chromas = mu.to_chroma(self.successive_shifts + self.tonic_chroma)
            self.names = mu.to_corrected_chroma_names(mu.CHROMA_NAMES[self.chromas])
        self.name = name
        self.chromabitmap = ChromaBitmap(sucessive_shifts=self.chromas)
    
    @staticmethod
    def compute_successive_shifts(shifts):
        succ = []
        if len(shifts) == 0:
            return succ
        succ.append(0)
        for s in shifts[:-1]:
            succ.append(succ[-1] + s)
        if succ[-1] + shifts[-1] != 12:
            raise ValueError("shifts: " + str(shifts) + " should sum up to 12")
        return np.array(succ)

    def compute_match(self, midi_ids):
        midi_ids = np.array(midi_ids)
        metric = 0
        for chroma, count in zip(*np.unique(mu.to_chroma(midi_ids), return_counts=True)):
            if chroma in self.chromas:
                metric += count
            else:
                metric -= count
        return metric/len(midi_ids)
    
    def __call__(self, scale_id, octave=0):
        return octave * 12 + self.chromas[np.array(scale_id) % len(self.chromas)] if len(self.chromas) > 0 else None
    
    def __repr__(self):
        return self.name + " Scale in " + mu.CHROMA_NAMES[self.tonic_chroma]
    
        

# DODECATONIC SCALES

CHROMATIC_SHIFTS = np.ones(12, dtype=int) 
def chromatic_scale():
    return Scale(shifts=CHROMATIC_SHIFTS, tonic_chroma=0, name="Chromatic")

# HEPTATONIC SCALES

# https://en.wikipedia.org/wiki/Heptatonic_scale        
# https://en.wikipedia.org/wiki/Diatonic_scale#:~:text=In%20music%20theory%2C%20a%20diatonic,their%20position%20in%20the%20scale.
# https://en.wikipedia.org/wiki/Circle_of_fifths_text_table

class Tetrachord:
    # https://en.wikipedia.org/wiki/Tetrachord
    T5 = [[3, 1, 1], [2, 2, 1], [1, 3, 1], [2, 1, 2], [1, 2, 2], [1, 1, 3]]
    T6 = [[3, 2, 1], [3, 1, 2], [2, 2, 2], [1, 3, 2], [2, 1, 3], [1, 2, 3]]
    
    MAJOR = 1; MINOR = 3; HARMONIC = 2; UPPER_MINOR = 4
    """Correct only for T5, in otherwords, either separator=2 or it is used for upper_tetra """

def ditetrachordic_shifts(lower_tetra=Tetrachord.MAJOR, upper_tetra=Tetrachord.MAJOR, separator=2):
    if separator not in [1, 2]:
        raise ValueError("Separator is the number of halftone between the two tetrachord it can be either 1 or 2")
    if lower_tetra < 0 or lower_tetra > 5 :
        raise ValueError("Lower tetra can either be one of the six possibilities so in range [0, 5]")
    if upper_tetra < 0 or upper_tetra > 5 :
        raise ValueError("Upper tetra can either be one of the six possibilities so in range [0, 5]")
    
    if separator == 2:
        shifts = Tetrachord.T5[lower_tetra]
    else:
        shifts = Tetrachord.T6[lower_tetra]
    
    return shifts + [separator] + Tetrachord.T5[upper_tetra]

def ditetrachordic_scale(tonic_chroma, **kwargs):
    return Scale(shifts=ditetrachordic_shifts(**kwargs), tonic_chroma=tonic_chroma, name="Ditetrachordic")

class Mode:
    IONIAN = 0
    MAJOR = 0
    DORIAN = 1
    PHRYGIAN = 2
    LYDIAN = 3
    MIXOLYDIAN = 4
    AEOLIAN = 5
    MINOR = 5 # Natural Minor Scale
    LOCRIAN = 6
    
    NAMES = ["Major", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Natural Minor", "Locrian"]
    MODES = [MAJOR, DORIAN, PHRYGIAN, LYDIAN, MIXOLYDIAN, MINOR, LOCRIAN]
    

DIATONIC_SHIFTS = ditetrachordic_shifts(Tetrachord.MAJOR, Tetrachord.MAJOR)
HARMONIC_MAJOR_SHIFTS = ditetrachordic_shifts(Tetrachord.MAJOR, Tetrachord.HARMONIC)
HARMONIC_MINOR_SHIFTS = ditetrachordic_shifts(Tetrachord.MINOR, Tetrachord.HARMONIC)
MELODIC_MAJOR_SHIFTS = ditetrachordic_shifts(Tetrachord.MAJOR, Tetrachord.UPPER_MINOR)
MELODIC_MINOR_SHIFTS = ditetrachordic_shifts(Tetrachord.MINOR, Tetrachord.MAJOR)
GIPSY_MAJOR_SHIFTS = ditetrachordic_shifts(Tetrachord.HARMONIC, Tetrachord.HARMONIC)
NEAPOLITAN_MINOR_SHIFTS = ditetrachordic_shifts(Tetrachord.UPPER_MINOR, Tetrachord.HARMONIC)
ALTERED_SHIFTS = np.roll(MELODIC_MINOR_SHIFTS, -1)


def diatonic_shifts(mode):
    return np.roll(DIATONIC_SHIFTS, -mode)

def diatonic_scale(tonic_chroma, mode=Mode.MAJOR):    
    return Scale(shifts=diatonic_shifts(mode), tonic_chroma=tonic_chroma, name=Mode.NAMES[mode])

def harmonic_scale(tonic_chroma, major=True):
    return Scale(shifts=HARMONIC_MAJOR_SHIFTS if major else HARMONIC_MINOR_SHIFTS,
                 tonic_chroma=tonic_chroma,
                 name="Harmonic " + ("Major" if major else "Minor"))

def melodic_scale(tonic_chroma, major=True):
    return Scale(shifts=MELODIC_MAJOR_SHIFTS if major else MELODIC_MINOR_SHIFTS,
                 tonic_chroma=tonic_chroma, 
                 name="Melodic " + ("Major" if major else "Minor"))

def gipsy_major_scale(tonic_chroma):
    return Scale(shifts=GIPSY_MAJOR_SHIFTS, tonic_chroma=tonic_chroma, name="Gipsy Major")

def neapolitan_minor_scale(tonic_chroma):
    return Scale(shifts=NEAPOLITAN_MINOR_SHIFTS, tonic_chroma=tonic_chroma, name="Neapolitan Major")

def altered_scale(tonic_chroma):
    return Scale(shifts=ALTERED_SHIFTS, tonic_chroma=tonic_chroma, name="Altered")

# PENTATONIC SCALES

# https://en.wikipedia.org/wiki/Pentatonic_scale

# DERIVED SCALES

# ALL SCALES

SCALE_LIST = pd.read_csv("scale-list.csv") 
SCALE_LIST.semitones = [base_to_list(x) for x in SCALE_LIST.semitones.tolist()]
SCALE_LIST["scale_id"] = [ChromaBitmap(Scale.compute_successive_shifts(x)).bitmap for x in SCALE_LIST.semitones.tolist()]
SCALE_LIST = SCALE_LIST.set_index("scale_id")

def scale(tonic_chroma, scale_id):
    scale_infos = SCALE_LIST.loc[scale_id].to_dict()
    return Scale(shifts=scale_infos["semitones"], 
                 tonic_chroma=tonic_chroma, 
                 name=scale_infos["mode_name"]) 

print(scale(0, 291))

# https://plucknplay.github.io/en/scale-list.html
from itertools import count
from re import sub
from cv2 import threshold
from matplotlib.style import available
import numpy as np
from scipy.fftpack import shift, ss_diff
import pandas as pd
from sklearn.preprocessing import scale
import midi_utils as mu
from utils import base_to_list
import pickle

FOLDER = "scale_researches/"
SCALE_DATA = pd.read_csv(FOLDER + "scale_final_data.csv")
SCALE_DATA = SCALE_DATA.set_index("scale_id")

SCALE_FOREST = {}
with open(FOLDER + "scale_forest.pkl", "rb") as file:
    SCALE_FOREST = pickle.load(file)
    
SCALE_PARENTS = {}
with open(FOLDER + "scale_parents.pkl", "rb") as file:
    SCALE_PARENTS = pickle.load(file)
    

def music_to_tonic_chroma(midi_ids):
    """Difficult and WIP heuristic to find the tonic. Needs accurate research

    Args:
        midi_ids (np.ndarray(int)): the music in midi id notes

    Returns:
        int: tonic in chroma id notes (0 to 11)
    """
    notes, counts = np.unique(mu.to_chroma(midi_ids), return_counts=True)
    
    return notes[counts.argmax()]

def music_to_chroma_semitones(midi_ids, tonic_chroma):
    semitones = np.diff(np.unique(mu.to_chroma(midi_ids) - tonic_chroma))
    remainder = 12 - semitones.sum()
    if remainder > 0:
        semitones = np.append(semitones, remainder)
    
    return semitones

def compute_semitone_intervals(semitones):
    succ = []
    if len(semitones) == 0:
        return succ
    succ.append(0)
    for s in semitones[:-1]:
        succ.append(succ[-1] + s)
    if succ[-1] + semitones[-1] != 12:
        raise ValueError("semitones: " + str(semitones) + " should sum up to 12")
    return np.array(succ)

def compute_semitones(semitone_intervals):
    return np.diff(np.append(semitone_intervals, 12))


def compute_match(chromas, midi_ids):
    midi_ids = np.array(midi_ids)
    
    # Naive Version: Works for subscale, but not for superscale
    # metric = 0
    # for chroma, count in zip(*np.unique(mu.to_chroma(midi_ids), return_counts=True)):
    #     if chroma in chromas:
    #         metric += count
    #     else:
    #         metric -= count
    # return metric/len(midi_ids)
    
    # V2
    # chmap = dict((chromas[i], i) for i in range(len(chromas)))
    # metric = np.array([0] * len(chromas))
    # match_count = 0
    # for chroma, count in zip(*np.unique(mu.to_chroma(midi_ids), return_counts=True)):
    #     if chroma in chromas:
    #         match_count += 1
    #         metric[chmap[chroma]] += count
    # return metric.mean()/len(midi_ids) * match_count
    
    #V2.1
    metric = np.array([0] * 12)
    match_count = 0
    for chroma, count in zip(*np.unique(mu.to_chroma(midi_ids), return_counts=True)):
        if chroma in chromas:
            match_count += 1
            metric[chroma] += count
        else:
            metric[chroma] -= count
    return metric.sum() / len(chromas) * match_count / len(midi_ids)
    
    

class ChromaBitmap:
    
    BIT_FILTER = 0x0FFF
    
    def __init__(self, bitmap=0) -> None:
        """Construct ChromaBitmap, if you pass both parameters, it will merge both.

        Args:
            chromas (list, optional): list of chroma defining a scale. Defaults to [].
            bitmap (int, optional): bitmap as a list of chroma bit (C is the most bit, B is the least bit). Defaults to 0.
        """
        self.bitmap = bitmap
    
    def set(self, index) -> None:
        self.bitmap |= (np.sum(1 << ((11 - np.array(index)) % 12)) & ChromaBitmap.BIT_FILTER)
        
    def set_map(self, other) -> None:
        self.bitmap |= (other & ChromaBitmap.BIT_FILTER)
        
    def unset(self, index) -> None:
        self.bitmap &= ~np.sum((1 << ((11 - np.array(index)) % 12)))
        
    def unset_map(self, other) -> None:
        self.bitmap &= ~(other & ChromaBitmap.BIT_FILTER)
    
    def on(self, index) -> bool:
        return (1 << ((11 - np.array(index)) % 12)) & self.bitmap != 0
    
    def off(self, index) -> bool:
        return ~(1 << ((11 - np.array(index)) % 12)) & self.bitmap != 0
    
    def contains(self, other) -> bool:
        return self.bitmap & other & ChromaBitmap.BIT_FILTER== other
    
    def is_contained(self, other) -> bool:
        return self.bitmap & other & ChromaBitmap.BIT_FILTER == self.bitmap
    
    def union(self, other) -> bool:
        return self.bitmap | other & ChromaBitmap.BIT_FILTER
    
    def inter(self, other) -> bool:
        return self.bitmap & other & ChromaBitmap.BIT_FILTER
    
    def chromas(self) -> list:
        return mu.CHROMA_IDS[self.on(mu.CHROMA_IDS)]

    def semitones(self) -> list:
        return compute_semitones(self.chromas()) #type: ignore
    
    def inverse_chromas(self) -> list:
        return mu.CHROMA_IDS[self.off(mu.CHROMA_IDS)]
    
    def roll(self, n: int) -> int:
        n = (n%12)
        a = self.bitmap << n
        b = self.bitmap >> (12 - n)
        return (a | b) & ChromaBitmap.BIT_FILTER

    def circular_distance(self, other):
        other &= ChromaBitmap.BIT_FILTER
        for i in range(12):
            if self.roll(i) == other:
                return i
        return None
    
    def note_count(self) -> int:
        n = int(self.bitmap)
        i = 0
        while(n):
            i += n % 2
            n //= 2
        return i
    
    @staticmethod
    def from_semitones(semitones):
        cb = ChromaBitmap()
        if len(semitones) > 0:
            cb.set(np.array(compute_semitone_intervals(semitones=semitones)))
        return cb
    
    @staticmethod
    def from_chromas(chromas):
        cb = ChromaBitmap()
        if len(chromas) > 0:
            cb.set(np.array(chromas))
        return cb
    
    def __str__(self):
        return f"{self.bitmap:012b}"
    
    def __repr__(self):
        return self.__str__()
    
    def __call__(self):
        return self.bitmap
    
    
    
    
class GeneralScale:
    def __init__(self, semitones, name="Untitled"):
        self.semitones = np.array(semitones)
        if len(self.semitones) != 0:
            self.semitone_intervals = compute_semitone_intervals(self.semitones)
            
        self.name = name
        self.names = name.split(",")
        self.scale_bitmap = ChromaBitmap.from_chromas(self.semitone_intervals)
        self.note_count = self.scale_bitmap.note_count()
        self.scale_id = self.scale_bitmap.bitmap
        
        self.rotation_id = None
        self.circular_distance = None
        if self.scale_id in SCALE_DATA.index:
            infos = SCALE_DATA.loc[self.scale_id]
            self.rotation_id = infos.rotation_id
            self.circular_distance = infos.circular_distance

    def __repr__(self):
        return self.names[0] + " General Scale"
    
    def alt_name(self, i):
        return self.names[max(0, min(i, len(self.names)))] + " General Scale"
    
    def parent_scales_bitmaps(self):
        return [ChromaBitmap(bitmap=scale_id) for scale_id in SCALE_PARENTS[self.scale_bitmap.bitmap]] 
    
    def parent_scales(self):
        return [scale(scale_id) for scale_id in SCALE_PARENTS[self.scale_bitmap.bitmap]]
    
    def child_scales_bitmaps(self):
        return [ChromaBitmap(bitmap=scale_id) for scale_id in SCALE_FOREST[self.scale_bitmap.bitmap] if scale_id != "self"] 
    
    def child_scales(self):
        return [scale(scale_id) for scale_id in SCALE_FOREST[self.scale_bitmap.bitmap] if scale_id != "self"]
    
    def scale_in(self, tonic_chroma):
        return Scale(self.semitones, tonic_chroma, name=self.name)
    
    @staticmethod
    def from_scale_id(scale_id, name="Untitled"):
        return GeneralScale(semitones=ChromaBitmap(scale_id).semitones(), name=name)
    
    @staticmethod
    def from_semitones_intervals(semitone_intervals, name="Untitled"):
        return GeneralScale(semitones=compute_semitones(semitone_intervals), name=name) 

    def suggest_tonic_chroma(self, midi_ids, return_match=False):
        max = -1
        tonic_chroma = None
        for chroma in mu.CHROMA_IDS:
            score = compute_match(mu.to_chroma(self.semitone_intervals + chroma), midi_ids)
            if score > max:
                max = score
                tonic_chroma = chroma
                
        if return_match:
            return tonic_chroma, max
        else:
            return tonic_chroma
        
    def __eq__(self, other):
        return self.scale_id == other.scale_id
    
    def __hash__(self) -> int:
        return hash(self.scale_id)    
    
class Scale(GeneralScale):
    def __init__(self, semitones, tonic_chroma, name="Untitled"):
        super().__init__(semitones, name)
        self.tonic_chroma = mu.to_chroma(tonic_chroma)
        if len(self.semitones) != 0:
            self.chromas = mu.to_chroma(self.semitone_intervals + self.tonic_chroma)
            self.chromas_name = mu.to_corrected_chroma_names(mu.CHROMA_NAMES[self.chromas])
        
        self.chroma_bitmap = ChromaBitmap.from_chromas(self.chromas)
        self.identifier = (self.scale_id, self.tonic_chroma)
    
    def __call__(self, scaled_id, octave=0):
        return octave * 12 + self.chromas[np.array(scaled_id) % len(self.chromas)] if len(self.chromas) > 0 else None
    
    def __repr__(self):
        return self.names[0] + " Scale in " + mu.CHROMA_NAMES[self.tonic_chroma]
    
    def alt_name(self, i):
        return self.names[max(0, min(i, len(self.names)))] + " Scale in " + mu.CHROMA_NAMES[self.tonic_chroma]
    
    def parent_scales_bitmaps(self):
        return [ChromaBitmap(bitmap=scale_id) for scale_id in SCALE_PARENTS[self.scale_bitmap.bitmap]] 
    
    def parent_scales(self):
        return [scale(scale_id, tonic_chroma=self.tonic_chroma) for scale_id in SCALE_PARENTS[self.scale_bitmap.bitmap]]
    
    def child_scales_bitmaps(self):
        return [ChromaBitmap(bitmap=scale_id) for scale_id in SCALE_FOREST[self.scale_bitmap.bitmap] if scale_id != "self"] 
    
    def child_scales(self):
        return [scale(scale_id, tonic_chroma=self.tonic_chroma) for scale_id in SCALE_FOREST[self.scale_bitmap.bitmap] if scale_id != "self"]

    def compute_match(self, midi_ids):
        return compute_match(self.chromas, midi_ids)

    def general_scale(self):
        return GeneralScale(self.semitones, self.name)
    
    def __eq__(self, other):
        return self.identifier == other.identifier
    
    def __hash__(self) -> int:
        return hash(self.identifier)
    
    @staticmethod
    def from_scale_id(scale_id, tonic_chroma, name="Untitled"):
        return Scale(semitones=ChromaBitmap(scale_id).semitones(), tonic_chroma=tonic_chroma, name=name)
    
    @staticmethod
    def from_semitones_intervals(semitone_intervals, tonic_chroma, name="Untitled"):
        return Scale(semitones=compute_semitones(semitone_intervals), tonic_chroma=tonic_chroma, name=name) 

# SELECTION OF SCALES
# See scale_final_data.csv

def scale(scale_id, tonic_chroma=None, name=None):
    if name is None:
        name = "Untitled"
        if scale_id in SCALE_DATA.index:
            name = SCALE_DATA.at[scale_id, "name"]
    if tonic_chroma is None:
        return GeneralScale.from_scale_id(scale_id=scale_id, name=name)
    else:
        return Scale.from_scale_id(scale_id=scale_id, tonic_chroma=tonic_chroma, name=name)
    
# Alias for typing and efficiency
def general_scale(scale_id, name=None):
    if name is None:
        name = "Untitled"
        if scale_id in SCALE_DATA.index:
            name = SCALE_DATA.at[scale_id, "name"]
    return GeneralScale.from_scale_id(scale_id=scale_id, name=name)

# DODECATONIC SCALES

CHROMATIC_SEMITONES = np.ones(12, dtype=int) 
def chromatic_scale():
    return scale(ChromaBitmap.from_semitones(CHROMATIC_SEMITONES).bitmap, tonic_chroma=0, name="Chromatic")

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

def ditetrachordic_semitones(lower_tetra=Tetrachord.MAJOR, upper_tetra=Tetrachord.MAJOR, separator=2):
    if separator not in [1, 2]:
        raise ValueError("Separator is the number of halftone between the two tetrachord it can be either 1 or 2")
    if lower_tetra < 0 or lower_tetra > 5 :
        raise ValueError("Lower tetra can either be one of the six possibilities so in range [0, 5]")
    if upper_tetra < 0 or upper_tetra > 5 :
        raise ValueError("Upper tetra can either be one of the six possibilities so in range [0, 5]")
    
    if separator == 2:
        semitones = Tetrachord.T5[lower_tetra]
    else:
        semitones = Tetrachord.T6[lower_tetra]
    
    return semitones + [separator] + Tetrachord.T5[upper_tetra]

def ditetrachordic_scale(tonic_chroma=None, **kwargs):
    return scale(ChromaBitmap.from_semitones(ditetrachordic_semitones(**kwargs)).bitmap, 
                 tonic_chroma=tonic_chroma, 
                 name="Ditetrachordic")

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
    

DIATONIC_SEMITONES = ditetrachordic_semitones(Tetrachord.MAJOR, Tetrachord.MAJOR)
HARMONIC_MAJOR_SEMITONES = ditetrachordic_semitones(Tetrachord.MAJOR, Tetrachord.HARMONIC)
HARMONIC_MINOR_SEMITONES = ditetrachordic_semitones(Tetrachord.MINOR, Tetrachord.HARMONIC)
MELODIC_MAJOR_SEMITONES = ditetrachordic_semitones(Tetrachord.MAJOR, Tetrachord.UPPER_MINOR)
MELODIC_MINOR_SEMITONES = ditetrachordic_semitones(Tetrachord.MINOR, Tetrachord.MAJOR)
GIPSY_MAJOR_SEMITONES = ditetrachordic_semitones(Tetrachord.HARMONIC, Tetrachord.HARMONIC)
NEAPOLITAN_MINOR_SEMITONES = ditetrachordic_semitones(Tetrachord.UPPER_MINOR, Tetrachord.HARMONIC)
ALTERED_SEMITONES = np.roll(MELODIC_MINOR_SEMITONES, -1)


def diatonic_semitones(mode):
    return np.roll(DIATONIC_SEMITONES, -mode)

def diatonic_scale(tonic_chroma=None, mode=Mode.MAJOR):    
    return scale(ChromaBitmap.from_semitones(diatonic_semitones(mode)).bitmap, tonic_chroma=tonic_chroma, name=Mode.NAMES[mode])

def harmonic_scale(tonic_chroma=None, major=True):
    return scale(ChromaBitmap.from_semitones(HARMONIC_MAJOR_SEMITONES if major else HARMONIC_MINOR_SEMITONES).bitmap,
                 tonic_chroma=tonic_chroma,
                 name="Harmonic " + ("Major" if major else "Minor"))

def melodic_scale(tonic_chroma=None, major=True):
    return scale(ChromaBitmap.from_semitones(MELODIC_MAJOR_SEMITONES if major else MELODIC_MINOR_SEMITONES).bitmap,
                 tonic_chroma=tonic_chroma, 
                 name="Melodic " + ("Major" if major else "Minor"))

def gipsy_major_scale(tonic_chroma=None):
    return scale(ChromaBitmap.from_semitones(GIPSY_MAJOR_SEMITONES).bitmap, tonic_chroma=tonic_chroma, name="Gipsy Major")

def neapolitan_minor_scale(tonic_chroma=None):
    return scale(ChromaBitmap.from_semitones(NEAPOLITAN_MINOR_SEMITONES).bitmap, tonic_chroma=tonic_chroma, name="Neapolitan Minor")

def altered_scale(tonic_chroma=None):
    return scale(ChromaBitmap.from_semitones(ALTERED_SEMITONES).bitmap, tonic_chroma=tonic_chroma, name="Altered")

# PENTATONIC SCALES

# https://en.wikipedia.org/wiki/Pentatonic_scale

# DERIVED SCALES


# Additional sources
# https://plucknplay.github.io/en/scale-list.html


ALL_GENERAL_SCALES = [general_scale(scale_id) for scale_id in SCALE_DATA.index]

def create_general_scale_subset(note_counts=None, 
                                contained_bitmap=None, 
                                container_bitmap=None,
                                scale_ids=None):
    general_scale_subset = ALL_GENERAL_SCALES
    if scale_ids is not None:
        if type(scale_ids) is int:
            scale_ids = [scale_ids]
        general_scale_subset = [scale for scale in general_scale_subset if scale.scale_id in scale_ids]
    if container_bitmap is not None:
        general_scale_subset = [scale for scale in general_scale_subset if scale.scale_bitmap.is_contained(container_bitmap)]
    if contained_bitmap is not None:
        general_scale_subset = [scale for scale in general_scale_subset if scale.scale_bitmap.contains(contained_bitmap)]
    if note_counts is not None:
        if type(note_counts) is int:
            note_counts = [note_counts]
        general_scale_subset = [scale for scale in general_scale_subset if scale.note_count in note_counts]    
    return general_scale_subset
    

def suggest_scales(midi_ids, 
                   threshold=0.99, 
                   normalize_scores=True,
                   tonic_chromas=mu.CHROMA_IDS,
                   general_scale_subset=ALL_GENERAL_SCALES):
    
    if normalize_scores:
        results = {}
        min_score = 1
        max_score = -1
        for gs in general_scale_subset:
            tonic_chroma, score = gs.suggest_tonic_chroma(midi_ids, return_match=True)
            results[gs.scale_in(tonic_chroma)] = score
            min_score = min(score, min_score)
            max_score = max(score, max_score)
            
        amplitude_score = max_score - min_score
        if amplitude_score != 0.0:
            for scale in results:
                results[scale] = (results[scale] - min_score)/amplitude_score
        
        filtered_results = {}
        for scale in results:
            if results[scale] > threshold:
                filtered_results[scale] = results[scale]
        return filtered_results
    else:
        results = {}
        for gs in general_scale_subset:
            tonic_chroma, score = gs.suggest_tonic_chroma(midi_ids, return_match=True)  # type: ignore
            if score > threshold and tonic_chroma in tonic_chromas:
                results[gs.scale_in(tonic_chroma)] = score
        return results


def windowed_suggest_scales(midi_ids, 
                            threshold=0.9, 
                            normalize_scores=True,
                            window_size=30, 
                            window_threshold=0.95,
                            **kwargs):
    
    results = {}
    counts = {}
    for i in range(window_size, len(midi_ids), window_size):
        for scale, score in suggest_scales(midi_ids[i-40:i], 
                                           threshold=window_threshold,
                                           normalize_scores=normalize_scores,
                                           tonic_chromas=kwargs.get("tonic_chromas", mu.CHROMA_IDS), 
                                           general_scale_subset=kwargs.get("general_scale_subset", ALL_GENERAL_SCALES)).items():
            if scale not in results:
                results[scale] = 0
                counts [scale] = 0
            results[scale] += score
            counts[scale] += 1
    
    
    
    if len(results.keys()) > 0:
        filtered_results = {}     
        if normalize_scores:
            max_score = results[max(results, key=results.get)]
            min_score = results[min(results, key=results.get)]
            amplitude_score = max_score - min_score
            if amplitude_score != 0.0:
                for scale in results:
                    results[scale] = (results[scale] - min_score)/amplitude_score
        else:
            max_score_count = counts[max(results, key=results.get)]
            for scale in results:
                results[scale] /= max_score_count
        
        for scale in results:
            if results[scale] > threshold:
                filtered_results[scale] = results[scale]
        
        return filtered_results
    else:
        return {}
    
import numpy as np
import pandas as pd
from itertools import combinations
import music_tools.midi_utils as mu
import music_tools.scales as scales
from music_tools.utils import normalize

class ChordSuggester:
    DEFAULT_SIMILARITY = 1
    DEFAULT_HARMONY = 0.8
    DEFAULT_CONSONANCE = 1
    DEFAULT_NOTE_COUNT = 3
    DEFAULT_BEAT_WEIGHTED = False
    
    # 2nd weighting : promote chords with important notes from the scale
    SCALE_IMP = np.array([3, 1, 1, 3, 3, 1, 1, 3, 1, 1, 1, 1])
    SCALE_IMP = SCALE_IMP / SCALE_IMP.sum()
    
    # 3rd weighting : promote chords with good sounding intervals according to EQ
    # Equal temperament fraction numerators used as metric for interval quality
    EQ_NUM = np.array([1/1, 1/16, 1/9, 1/6, 1/5, 1/4, 1/64, 1/3, 1/8, 1/5, 1/16, 1/15])
       
    def __init__(self, 
                 scale, 
                 music_dataframe, 
                 note_count=DEFAULT_NOTE_COUNT, 
                 w_similarity=DEFAULT_SIMILARITY, 
                 w_harmony=DEFAULT_HARMONY, 
                 w_consonance=DEFAULT_CONSONANCE,
                 beat_weighted=DEFAULT_BEAT_WEIGHTED):
                 
        assert note_count <= scale.note_count, "Cannot make a chord with more notes than the scale has!"
        self.note_count = note_count
        self.scale = scale
        self.df = music_dataframe
        self.w_similarity = w_similarity
        self.w_harmony = w_harmony
        self.w_consonance = w_consonance
        self.beat_weighted = beat_weighted
        
        self.most_influent = 0
        self.chroma_stats = np.zeros(0)
        self.chords = np.zeros(0)
        self.chords_matrix = np.zeros(0)
        self.intervals = np.zeros(0)
        
        self.similarity = np.zeros(0)
        self.harmony = np.zeros(0)
        self.consonance = np.zeros(0)
        
        self.dirty = False
        self.__update_chord_combinations()
        self.dirty = True
        self.__update_music_stats()

    def set_note_count(self, note_count):
        assert note_count <= self.scale.note_count, "Cannot make a chord with more notes than the scale has!"
        self.note_count = note_count
        self.dirty = True
        self.__update_chord_combinations()
        
    def set_scale(self, scale):
        assert self.note_count <= scale.note_count, "Cannot make a chord with more notes than the scale has!"
        self.scale = scale
        self.dirty = True
        self.__update_chord_combinations()
    
    def set_music_dataframe(self, music_dataframe):
        self.df = music_dataframe
        self.dirty = True
        self.__update_music_stats()
        
    def set_beat_weighted(self, beat_weighted):
        self.beat_weighted = beat_weighted
        self.dirty = True
        self.__update_music_stats()
        
    def __update_chord_combinations(self):
        # Generate all chords on the detected scale with the given number of notes, max = C(12, 6) = 924
        self.chords = np.array([c for c in combinations(self.scale.chromas, self.note_count)])
        i = np.arange(len(self.chords))
        self.chords_matrix = np.zeros((len(self.chords), 12))
        self.chords_matrix[np.tile(i, (self.note_count,1)).T, self.chords[i]] = 1
        self.intervals = np.diff(self.chords, append=self.chords[:,0][:, np.newaxis], axis=1)
        self.compute_individual_scores()

    def __update_music_stats(self):
        if self.df is not None:
            chroma_counts, total = scales.music_chroma_counts(mu.to_chroma(self.df.note.to_numpy()), 
                                                            self.df.weight.to_numpy() if self.beat_weighted else None)
            self.chroma_stats = chroma_counts / total
            self.most_influent = chroma_counts.argmax()
            self.compute_individual_scores()

    def compute_individual_scores(self):
        if self.dirty and self.df is not None:
            # 1st weighting: Similarity (how close the chords should be from the other notes played)
            self.similarity = self.chords_matrix @ self.chroma_stats
            
            # 2nd weighting: Harmony (or how we benefit from being close to the most played note)
            self.harmony = self.SCALE_IMP[self.chords - self.most_influent].sum(axis=1) #type:ignore
            
            # 3rd weighting: Consonance (or how we avoid dissonant intervals as much as possible)
            self.consonance = self.EQ_NUM[self.intervals].sum(axis=1)
            # self.consonance = normalize(self.consonance)
            
            self.dirty = False
        
    def suggest_chords(self, chord_count):
        if self.df is None:
            return []
        else:
            scores = self.w_similarity * self.similarity\
                    + self.w_harmony * self.harmony\
                    + self.w_consonance * self.consonance
            
            return self.chords[scores.argsort()[-chord_count:][::-1]]

import numpy as np
import pandas as pd
import midi_utils as mu
from itertools import combinations
import scales

class Suggestion:
    
    # 2nd weighting : promote chords with important notes from the scale
    SCALE_IMP = np.array([3, 1, 1, 3, 3, 1, 1, 3, 1, 1, 1, 1])
    SCALE_IMP = SCALE_IMP / SCALE_IMP.sum()
    
    # 3rd weighting : promote chords with good sounding intervals according to EQ
    # Equal temperament fraction numerators used as metric for interval quality
    EQ_NUM = [1, 16, 9, 6, 5, 4, 64, 3, 8, 5, 16, 15]
       
    def __init__(self, nb_note, scale, notes, w_similarity=1, w_harmony=0.8, w_consonance=1):
        self.nb_note = nb_note
        self.scale = scale
        self.notes = notes
        self.w_similarity = w_similarity
        self.w_harmony = w_harmony
        self.w_consonance = w_consonance
        assert nb_note <= len(self.scale.chromas), "Cannot make a chord with more notes than the scale has!"

    def suggest_chord(self, nb_chord):
        # Generate all chords on the detected scale with the given number of notes, max = C(12, 6) = 924
        chords = np.array([c for c in combinations(self.scale.chromas, self.nb_note)])
        # Keep track of the score of each chord
        scores = np.zeros(len(chords))
        
        # 1st weighting : promote chords with similar notes as in the selected window
        chroma_counts, tot = scales.music_chroma_counts(mu.to_chroma(self.notes))
        chroma_counts = chroma_counts / tot
        most_played = chroma_counts.argmax()
        
        for idx, chord in enumerate(chords): # avg cost = 175, max cost ~ 10k
            for note in chord:
                # 1st weighting
                scores[idx] += self.w_similarity * chroma_counts[note]
                # 2nd weighting
                scores[idx] += self.w_harmony * self.SCALE_IMP[note - most_played]
            # 3rd weighting
            intervals = np.diff(np.append(chord, chord[0])) % 12            
            for i in intervals:
                scores[idx] += self.w_consonance / self.EQ_NUM[i]

        return chords[scores.argsort()[-nb_chord:][::-1]]

from os import listdir
from os.path import isfile, join

import numpy as np
import music_tools.scales as scales
import music_tools.midi_utils as mu
from music_tools.chords import ChordSuggester

###########################    Init Variables     ########################### 
MIDIPLAYER = None 

MIDI_PATH = "./MIDI_Files"
MIDIFILES = [f for f in listdir(MIDI_PATH) if isfile(join(MIDI_PATH, f))]
PLOT_DISPLAYED = False
NORMALIZE_ACCURACY = True
WEIGHTED = False
THRESHOLD = 0.9
METRIC = "ticks"

WINDOW = [0,0]
NUM_BARS = 4
NOTE_COUNTS = set(i for i in range(5,13))
FOLLOW_CURSOR = False

TABLE_SCALE_NAME_WIDTH = 350
TABLE_ACCURACY_WIDTH = 30
TABLE_NOTECOUNT_WIDTH = 30
TABLE_ALTNAMES_WIDTH = 400

LAST_SELECTED_SCALE_UI_ELEMENT = ""
SELECTED_GENERAL_SCALE = scales.scale(2773)
SELECTED_TONIC_CHROMA = 0
SELECTED_SCALE = SELECTED_GENERAL_SCALE.scale_in(SELECTED_TONIC_CHROMA)

GENERAL_SCALE_ROTZERO_SUBSET, GENERAL_SCALE_SUBSET = scales.create_general_scale_subset(NOTE_COUNTS, not_only_rotation_zero=True)
TONIC_CHROMA_SUBSET = mu.CHROMA_IDS
ROTATIONS_SCALES = SELECTED_SCALE.rotated_scales()
CHILDREN_SCALES = SELECTED_SCALE.child_scales()
PARENTS_SCALES = SELECTED_SCALE.parent_scales()

EN_NOTES_DISPLAY = mu.CHROMA_SHARP_NAMES
FR_NOTES_DISPLAY = mu.name_to_alt_name(EN_NOTES_DISPLAY)

CHORD_WEIGHTED = ChordSuggester.DEFAULT_BEAT_WEIGHTED
CHORD_NOTE_COUNT = ChordSuggester.DEFAULT_NOTE_COUNT
SIMILARITY_FACTOR = ChordSuggester.DEFAULT_SIMILARITY
HARMONY_FACTOR = ChordSuggester.DEFAULT_HARMONY
CONSONANCE_FACTOR = ChordSuggester.DEFAULT_CONSONANCE

CHORD_SUGGESTER = ChordSuggester(SELECTED_SCALE, None)
CHORD_SUGGESTIONS = []

NOTE_COLORS = np.array([
        [217, 31, 28], # C
        [217, 97, 28],  # C#
        [217, 151, 28],  # D
        [179, 217, 28], # D#
        [47, 217, 28],  # E
        [28, 217, 132],  # F
        [28, 208, 217], # F#
        [28, 126, 217],  # G
        [28, 47, 217], # G#
        [141, 28, 217], # A 
        [208, 28, 217], # A#
        [217, 28, 135] # B
    ])
# Get colour texture for each note (in progress)
def get_note_colour(note, weight=1.0):
    return tuple(NOTE_COLORS[int(note) % 12]*weight)

def combo_getter(item, list):
    for x in list:
        if str(x) == item:
            return x
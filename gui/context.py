from os import listdir
from os.path import isfile, join

import music_tools.scales as scales
import music_tools.midi_utils as mu

###########################    Init Variables     ########################### 
MIDIPLAYER = None 

MIDI_PATH = "./MIDI_Files"
MIDIFILES = [f for f in listdir(MIDI_PATH) if isfile(join(MIDI_PATH, f))]
PLOT_DISPLAYED = False
NORMALIZE_SCORES = True
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

GENERAL_SCALE_SUBSET = scales.create_general_scale_subset(NOTE_COUNTS)
TONIC_CHROMA_SUBSET = mu.CHROMA_IDS
ROTATIONS_SCALES = SELECTED_SCALE.rotated_scales()
CHILDREN_SCALES = SELECTED_SCALE.child_scales()
PARENTS_SCALES = SELECTED_SCALE.parent_scales()

NOTE_COLORS = [
        [255,0,0], # C
        [255,127,0],  # C#
        [255,255,0],  # D
        [0,127,0], # D#
        [0,255,0],  # E
        [0,255,147],  # F
        [0,255,255], # F#
        [0,127,255],  # G
        [0,0,255], # G#
        [127,0,255], # A 
        [255,0,255], # A#
        [255,0,127] # B
    ]
# Get colour texture for each note (in progress)
def get_note_colour(note):
    return NOTE_COLORS[int(note) % 12].copy()

def combo_getter(item, list):
    for x in list:
        if str(x) == item:
            return x
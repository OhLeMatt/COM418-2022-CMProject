import dearpygui.dearpygui as dpg
import random

from music_tools.midi_player import MidiPlayer
import gui.context as gc
from gui.interactive_callbacks import display, compute_suggestions, \
                        update_ui_cursor, update_ui_window, update_ui_suggestions
                        
# Utility function to load selected midi file 
def load_midi(midi_file, path, name):
    
    print("Filename: ", midi_file)
    
    if gc.MIDIPLAYER is not None:
        gc.MIDIPLAYER.stop()

    gc.MIDIPLAYER = MidiPlayer(midi_file, 
                           path,
                           on_cursor_change_callback=update_ui_cursor,
                           on_window_change_callback=update_ui_window,
                           on_analysis_change_callback=update_ui_suggestions)
    
    for i in range(16):
        item = f"channel_{i}"
        dpg.set_value(item, True)
        dpg.enable_item(item)
        
        if i in gc.MIDIPLAYER.midiframe.playing_track_frame.channel_count:
            dpg.show_item(item)
        else:
            dpg.hide_item(item)
    
    gc.MIDIPLAYER.analysis_parameters["general_scale_subset"] = gc.GENERAL_SCALE_SUBSET
    gc.MIDIPLAYER.analysis_parameters["weighted"] = gc.WEIGHTED
    gc.MIDIPLAYER.analysis_parameters["threshold"] = gc.THRESHOLD
    gc.MIDIPLAYER.analysis_parameters["normalize_accuracy"] = gc.NORMALIZE_SCORES
    gc.MIDIPLAYER.update_window(barsize=gc.NUM_BARS)
    gc.MIDIPLAYER.set_volume(dpg.get_value("volume"))
    compute_suggestions(None, None, None)    

    dpg.set_value("PlayText", "Selected: " + name.replace(".mid", "").replace("_", " "))
    dpg.set_item_label("PlayButton", "Play")
    
    display(None, None, None)
    
    
def random_midi(sender, app_data, user_data):
    midi_name = random.choice(gc.MIDIFILES)
    random_file = gc.MIDI_PATH + "/" + midi_name

    load_midi(random_file, gc.MIDI_PATH, midi_name)

def select_file(sender, app_data, user_data):
    path = app_data['current_path']  # path to sound font file
    midi_file = app_data['file_path_name']
    load_midi(midi_file, path, app_data['file_name'])


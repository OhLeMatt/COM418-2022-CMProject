import dearpygui.dearpygui as dpg

import gui.context as gc
import music_tools.midi_utils as mu
import music_tools.scales as scales
from gui.interactive_callbacks import display, update_selected_scale, compute_chord_suggestions
            
def set_channels(sender, app_data, user_data):
    if gc.MIDIPLAYER is not None:
        change = False
        if app_data:
            change = gc.MIDIPLAYER.add_channel(user_data)
        else: 
            change = gc.MIDIPLAYER.remove_channel(user_data)
        if change:
            display(None, None, None)
        print("channels: " + str(gc.MIDIPLAYER.channels))

def set_threshold(sender, app_data, user_data):
    gc.THRESHOLD = app_data
    if gc.MIDIPLAYER is not None:
        gc.MIDIPLAYER.analysis_parameters["threshold"] = gc.THRESHOLD

def set_normalize(sender, app_data, user_data):
    gc.NORMALIZE_ACCURACY = app_data
    if gc.MIDIPLAYER is not None:
        gc.MIDIPLAYER.analysis_parameters["normalize_accuracy"] = gc.NORMALIZE_ACCURACY

def set_weighted(sender, app_data, user_data):    
    gc.WEIGHTED = app_data
    display(None, None, None)
    if gc.MIDIPLAYER is not None:
        gc.MIDIPLAYER.analysis_parameters["weighted"] = gc.WEIGHTED

def set_cursor(sender, app_data, user_data):
    if gc.MIDIPLAYER is not None:
        gc.MIDIPLAYER.update_cursor(dpg.get_value(sender), metric=gc.METRIC, on_cursor_callback=False)

def set_notecounts(sender, app_data, user_data):
    if app_data:
        gc.NOTE_COUNTS.add(user_data)
    else:
        gc.NOTE_COUNTS.remove(user_data)

    gc.GENERAL_SCALE_ROTZERO_SUBSET, gc.GENERAL_SCALE_SUBSET = scales.create_general_scale_subset(gc.NOTE_COUNTS, not_only_rotation_zero=True)
    dpg.configure_item("general_scale_list", items=gc.GENERAL_SCALE_SUBSET)
    
    if gc.MIDIPLAYER is not None:
        gc.MIDIPLAYER.analysis_parameters["general_scale_subset"] = gc.GENERAL_SCALE_ROTZERO_SUBSET
    print(f"note counts selected: {gc.NOTE_COUNTS} | number of general scales: {len(gc.GENERAL_SCALE_ROTZERO_SUBSET)}")
    print("note counts selected: " + str(user_data))

def set_metric(sender, app_data, user_data):
    gc.METRIC = app_data.lower()
    dpg.set_item_label("imgx", app_data.capitalize())
    display(None, None, None)

def set_num_bars(sender, app_data, user_data):
    dpg.show_item("ui_window")
    
    if user_data:
        gc.NUM_BARS += 1
    else:
        gc.NUM_BARS -= 1
    dpg.set_value("num_bars", gc.NUM_BARS)
    if gc.MIDIPLAYER is not None and not gc.MIDIPLAYER.analysis_window_entire:
        gc.MIDIPLAYER.update_window(barsize=gc.NUM_BARS)

def set_volume(sender, app_data, user_data):
    if gc.MIDIPLAYER is not None: 
        gc.MIDIPLAYER.set_volume(app_data/100)

def set_follow_cursor(sender, app_data, user_data):
    gc.FOLLOW_CURSOR = app_data
    if not gc.FOLLOW_CURSOR:
        dpg.set_axis_limits_auto("imgx")

def set_entire_window(sender, app_data, user_data):
    if gc.MIDIPLAYER is not None:
        if gc.MIDIPLAYER.analysis_window_entire:
            gc.MIDIPLAYER.set_entire_window(False)
            dpg.set_item_label(sender, "Entire Window Suggestions")
        else:
            gc.MIDIPLAYER.set_entire_window(True)
            dpg.set_item_label(sender, "Cursor Window Suggestions")

def set_scale_from_suggestions(sender, app_data, user_data):
    
    try:
        dpg.set_value(gc.LAST_SELECTED_SCALE_UI_ELEMENT, False)
    except:
        pass
    gc.LAST_SELECTED_SCALE_UI_ELEMENT = sender
    dpg.set_value(sender, True)
    gc.SELECTED_GENERAL_SCALE = user_data[0]
    gc.SELECTED_TONIC_CHROMA = user_data[1]
    update_selected_scale()

def set_general_scale_from_all(sender, app_data, user_data):
    print(app_data)
    gc.SELECTED_GENERAL_SCALE = gc.combo_getter(app_data, gc.GENERAL_SCALE_SUBSET)
    update_selected_scale()

def set_tonic_chroma_from_all(sender, app_data, user_data):
    gc.SELECTED_TONIC_CHROMA = mu.NOTES[gc.combo_getter(app_data, mu.CHROMA_NAMES[gc.TONIC_CHROMA_SUBSET])] #type:ignore
    update_selected_scale()

def set_scale_from_navigation(sender, app_data, user_data):
    scale = gc.SELECTED_SCALE
    if user_data=="rotations":
        scale = gc.combo_getter(app_data, gc.ROTATIONS_SCALES)
    elif user_data=="parents":
        scale = gc.combo_getter(app_data, gc.PARENTS_SCALES)
    elif user_data=="children":
        scale = gc.combo_getter(app_data, gc.CHILDREN_SCALES)
        
    gc.SELECTED_GENERAL_SCALE = scale.general_scale() #type:ignore
    gc.SELECTED_TONIC_CHROMA = scale.tonic_chroma #type:ignore
    update_selected_scale()

def set_chord_weighted(sender, app_data, user_data):
    gc.CHORD_WEIGHTED = app_data
    gc.CHORD_SUGGESTER.set_beat_weighted(gc.CHORD_WEIGHTED)
    for prefix in ("chroma", "piano"):
        dpg.set_value(prefix+"_chord_weighted", app_data)
    compute_chord_suggestions()

def set_chord_note_count(sender, app_data, user_data):
    gc.CHORD_NOTE_COUNT = int(app_data)
    gc.CHORD_SUGGESTER.set_note_count(gc.CHORD_NOTE_COUNT)
    for prefix in ("chroma", "piano"):
        dpg.set_value(prefix+"_chord_note_count", app_data)
    compute_chord_suggestions()

def set_similarity_factor(sender, app_data, user_data):
    gc.SIMILARITY_FACTOR = app_data/100
    gc.CHORD_SUGGESTER.w_similarity = gc.SIMILARITY_FACTOR 
    for prefix in ("chroma", "piano"):
        dpg.set_value(prefix+"_similarity", app_data)
    compute_chord_suggestions()
    
def set_harmony_factor(sender, app_data, user_data):
    gc.HARMONY_FACTOR = app_data/100
    gc.CHORD_SUGGESTER.w_harmony = gc.HARMONY_FACTOR
    for prefix in ("chroma", "piano"):
        dpg.set_value(prefix+"_harmony", app_data)
    compute_chord_suggestions()
    
def set_consonance_factor(sender, app_data, user_data):
    gc.CONSONANCE_FACTOR = app_data/100
    gc.CHORD_SUGGESTER.w_consonance = gc.CONSONANCE_FACTOR
    for prefix in ("chroma", "piano"):
        dpg.set_value(prefix+"_consonance", app_data)
    compute_chord_suggestions()
    
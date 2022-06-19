import dearpygui.dearpygui as dpg
import numpy as np

import gui.context as gc
import music_tools.midi_utils as mu
from gui.visualizations import update_piano_display, update_chroma_display

def _log(sender, app_data, user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")

def update_ui_cursor(midiplayer):
    dpg.set_value("ui_cursor", midiplayer.cursor[gc.METRIC])
    limits = dpg.get_axis_limits("imgx")
    view_width = limits[1] - limits[0]
    if gc.FOLLOW_CURSOR:
        dpg.set_axis_limits("imgx", 
                        midiplayer.cursor[gc.METRIC] - view_width/2,
                        midiplayer.cursor[gc.METRIC] + view_width/2)
    
def update_ui_window(midiplayer):
    gc.WINDOW[0] = midiplayer.convert_unit(midiplayer.analysis_window[0], "bartime", gc.METRIC)
    gc.WINDOW[1] = midiplayer.convert_unit(midiplayer.analysis_window[1], "bartime", gc.METRIC)
    
    dpg.configure_item("ui_window", bounds_min=(gc.WINDOW[0], 0), bounds_max=(gc.WINDOW[1], 128))
    
    df_copy = midiplayer.midiframe.playing_track_frame.get_sub_dataframe(midiplayer.analysis_last_bar, 
                                                                         midiplayer.analysis_last_bar+1,
                                                                         columns=["note", "weight"])
    gc.CHORD_SUGGESTER.set_music_dataframe(df_copy)
    compute_chord_suggestions()
        
def update_ui_suggestions(midiplayer):
    # To avoid circular dep:
    from gui.setter_callbacks import set_scale_from_suggestions
    suggestions = []
    if midiplayer is not None:
        suggestions = midiplayer.get_suggestions()
    
    dpg.delete_item("suggestion_content", children_only=True, slot=1)
        
    for i, (scale, tonic, accuracy) in enumerate(suggestions):
        with dpg.table_row(parent="suggestion_content"):
            dpg.add_selectable(label=repr(scale)+ " in " + mu.CHROMA_NAMES[tonic], 
                                callback=set_scale_from_suggestions, 
                                user_data=(scale, tonic))
            dpg.add_text(f"{int(accuracy * 100)}%")
            dpg.add_text(scale.note_count)
            dpg.add_text(scale.name)    
            if accuracy == 1.0:
                dpg.highlight_table_row("suggestion_content", i, [10, 0, 50, 100])

def update_ui_chord_suggestions():
    
    for i, chord in enumerate(gc.CHORD_SUGGESTIONS):
        prefix = f"chord{i}"
        update_chroma_display(chord, prefix)
        update_piano_display(chord, prefix)
    
    for i in range(len(gc.CHORD_SUGGESTIONS), 4):
        prefix = f"chord{i}"
        update_chroma_display([], prefix)
        update_piano_display([], prefix)

def play_midi(sender, app_data, user_data):
    if gc.MIDIPLAYER is not None:
        # user_data is either playpause at True, stop at False
        if user_data:
            if gc.MIDIPLAYER.playing:
                gc.MIDIPLAYER.pause()
                dpg.configure_item("PlayButton", texture_tag="play")
            else:
                gc.MIDIPLAYER.play()
                dpg.configure_item("PlayButton", texture_tag="pause")
        else:
            gc.MIDIPLAYER.stop()
            dpg.configure_item("PlayButton", texture_tag="play")

def display(sender, app_data, user_data):
    dpg.show_item("loading_indicator")
    if gc.MIDIPLAYER is not None and gc.MIDIPLAYER.displayable:
        if gc.PLOT_DISPLAYED:
            dpg.delete_item("imgy", children_only=True)
            gc.PLOT_DISPLAYED = False
        
        if not gc.PLOT_DISPLAYED: 
            gc.PLOT_DISPLAYED = True
            dpg.set_axis_limits("imgy", gc.MIDIPLAYER.min_note - 1, gc.MIDIPLAYER.max_note + 1)
                    
            if len(gc.MIDIPLAYER.df) > 0:
                metric_release = gc.METRIC + "_release"
                df_copy = gc.MIDIPLAYER.df.loc[:,[gc.METRIC, "note", metric_release, "weight"]]
                if not gc.WEIGHTED:
                    df_copy.weight = 1
                
                tints = np.einsum("ij,i->ij", gc.NOTE_COLORS[mu.to_chroma(df_copy.note)], df_copy.weight)
                
                df_copy["min_bound_y"] = df_copy.note - 0.5
                df_copy["max_bound_y"] = df_copy.note + 0.5
                for i, x in df_copy.iterrows():                                        
                    dpg.add_image_series("Texture_C", 
                                         [x[gc.METRIC], x.min_bound_y], [x[metric_release], x.max_bound_y], 
                                         label="C", tag=f"MidiNote{i}", parent="imgy", tint_color=tuple(tints[i]))
                dpg.fit_axis_data("imgx")
    dpg.hide_item("loading_indicator")        
        

def compute_suggestions(sender, app_data, user_data):
    if gc.MIDIPLAYER:
        gc.MIDIPLAYER.analyse()
        
def compute_chord_suggestions(sender=None, app_data=None, user_data=None):
    gc.CHORD_SUGGESTIONS = gc.CHORD_SUGGESTER.suggest_chords(4)
    update_ui_chord_suggestions()

def update_selected_scale():
    gc.SELECTED_SCALE = gc.SELECTED_GENERAL_SCALE.scale_in(gc.SELECTED_TONIC_CHROMA)
    gc.ROTATIONS_SCALES = gc.SELECTED_SCALE.rotated_scales()
    gc.PARENTS_SCALES = gc.SELECTED_SCALE.parent_scales()
    gc.CHILDREN_SCALES = gc.SELECTED_SCALE.child_scales()
    dpg.configure_item("general_scale_list", default_value=repr(gc.SELECTED_GENERAL_SCALE))
    dpg.configure_item("tonic_chroma_list", default_value=mu.CHROMA_NAMES[gc.SELECTED_TONIC_CHROMA])
    dpg.configure_item("scale_rotations_list", items=gc.ROTATIONS_SCALES, default_value=repr(gc.SELECTED_SCALE))
    dpg.configure_item("scale_parents_list", items=gc.PARENTS_SCALES)
    dpg.configure_item("scale_children_list", items=gc.CHILDREN_SCALES)
    dpg.configure_item("scale_alternative_names", default_value=gc.SELECTED_SCALE.name) 
    update_chroma_display(gc.SELECTED_SCALE.chromas)
    update_piano_display(gc.SELECTED_SCALE.chromas)
    update_piano_display(gc.SELECTED_SCALE.chromas, prefix="+")
    
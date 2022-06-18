import dearpygui.dearpygui as dpg
from music_tools.midi_frame import MidiFrame
# import music_tools.scales as scales
import music_tools.midi_utils as mu

import gui.context as gc
from gui.file_loading_callbacks import *
from gui.setter_callbacks import *
from gui.interactive_callbacks import *

dpg.create_context()

dpg.add_texture_registry(label="Texture Container", tag="texture_container")
dpg.add_static_texture(1, 1, [1,1,1,1], parent="texture_container", tag="Texture_C", label="Texture_C")
dpg.add_static_texture(1, 1, [1,1,1,0.05], parent="texture_container", tag="TransparentWindowTexture", label="TransparentWindowTexture")

###########################    UI     ########################### 

with dpg.file_dialog(directory_selector=False, show=False, callback=select_file, id="file_dialog_id", height=300):
    dpg.add_file_extension(".mid")
    dpg.add_file_extension("", color=(150, 255, 150, 255))

with dpg.window(label="Improvisation Tool", 
                width=1200, 
                height=700, 
                tag="primary_window",
                no_title_bar=True, 
                no_move=True):
    
    with dpg.collapsing_header(label="Midi Player", default_open=True):
        with dpg.group(horizontal=True):
            dpg.add_button(label="File Selector", callback=lambda: dpg.show_item("file_dialog_id"))
            dpg.add_button(label="Random", callback=random_midi)
        dpg.add_text(label="PlayText", default_value="No file selected", tag="PlayText")
        
        with dpg.group(horizontal=True):
            dpg.add_button(label="Play", callback=play_midi, tag="PlayButton", user_data=True)
            dpg.add_button(label="Stop", callback=play_midi, tag="StopButton", user_data=False)
            dpg.add_checkbox(label="Follow Cursor", callback=set_follow_cursor, tag="FollowCursor", default_value=gc.FOLLOW_CURSOR)
            dpg.add_slider_int(format="volume = %d ", tag="volume", min_value=0, max_value=10, default_value=1, callback=set_volume, width=100)
            dpg.add_combo(("Ticks", "Time", "Bartime"), label="", tag="MetricSelector", default_value="Bartime", callback=set_metric, width=80)
            dpg.add_text("colour code")
            with dpg.tooltip(dpg.last_item()):
                with dpg.table(tag="colour-code", header_row=False):
                    for i in range(12):
                        dpg.add_table_column()
                
                    with dpg.table_row():
                        for name in mu.CHROMA_SHARP_NAMES:
                            dpg.add_text(name)

                    with dpg.table_row():
                        for colour in gc.NOTE_COLORS:
                            dpg.add_image("Texture_C", width=12, height=12, tint_color=tuple(colour))

        with dpg.plot(label="Midi Visualiser", height=400, width=-1, tag="midiviz"):
            
            xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="Bartime", tag="imgx")
            yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="Note", tag="imgy")
            dpg.add_drag_line(label="ui_cursor",
                                color=[100, 164, 255, 200],
                                tag="ui_cursor",
                                parent="midiviz",
                                default_value=0,
                                thickness=1,
                                callback=set_cursor)
            
            dpg.add_image_series("TransparentWindowTexture", 
                                [0, 0], [1,128], 
                                tag="ui_window", parent="imgx")
        
        with dpg.group(horizontal=True): 
            dpg.add_text(label="label", default_value="Select Midi Channels: ")
            for i in range(0,16):
                dpg.add_checkbox(label=str(i), tag=f"channel_{i}", callback=set_channels, default_value=True, user_data=i)

    with dpg.collapsing_header(label="Suggestion Settings"):
        with dpg.group(horizontal=True): 
            dpg.add_checkbox(label="Normalize Accuracy", callback=set_normalize, default_value=gc.NORMALIZE_SCORES)
            dpg.add_checkbox(label="Weighted by Beat Importance", callback=set_weighted, default_value=gc.WEIGHTED)
        dpg.add_text("Compute suggestions over: ")
        with dpg.group(horizontal=True): 
            dpg.add_text("Bars: ")
            dpg.add_button(arrow=True, direction=dpg.mvDir_Left, user_data=False, callback=set_num_bars)
            dpg.add_text(str(gc.NUM_BARS), tag="num_bars")
            dpg.add_button(arrow=True, direction=dpg.mvDir_Right, user_data=True, callback=set_num_bars)
            dpg.add_text(label="WindowText", default_value="", tag="WindowText")            
            dpg.add_button(label="Entire Window Suggestions", callback=set_entire_window)
        with dpg.group():
            dpg.add_slider_float(label="Accuracy Threshold", 
                                max_value=1.0, 
                                format="threshold = %.3f", 
                                callback=set_threshold, 
                                default_value=gc.THRESHOLD)
        with dpg.group(horizontal=True): 
            dpg.add_text(label="label", default_value="Select amount of notes: ")
            for i in range(5,13):
                dpg.add_checkbox(label=str(i), callback=set_notecounts, default_value=True, user_data=i)

    with dpg.collapsing_header(label="Suggestions", tag="suggestion_tab", default_open=True):
        dpg.add_button(label="Compute Suggestions", callback=compute_suggestions)

        with dpg.table(header_row=False, tag="suggestion_table"):
            # use add_table_column to add columns to the table,
            # table columns use slot 0
            dpg.add_table_column(width=gc.TABLE_SCALE_NAME_WIDTH)
            dpg.add_table_column(width=gc.TABLE_ACCURACY_WIDTH)
            dpg.add_table_column(width=gc.TABLE_NOTECOUNT_WIDTH)
            dpg.add_table_column(width=gc.TABLE_ALTNAMES_WIDTH)

            with dpg.table_row():
                dpg.add_text("Scale")
                dpg.add_text("Accuracy")
                dpg.add_text("Note count")
                dpg.add_text("Alternate names")
            dpg.highlight_table_row("suggestion_table",0, [10, 0, 50, 100])

        with dpg.table(header_row=False, tag="suggestion_content"):    
            dpg.add_table_column()
            
    with dpg.collapsing_header(label="Improvisation Material", tag="improvisation", default_open=True):
        with dpg.child_window(autosize_x=True, height=200, menubar=True):
            with dpg.menu_bar():
                dpg.add_text("Scale Navigation")
            with dpg.group(horizontal=True):
                dpg.add_text("Selected Scale: ")
                dpg.add_combo(gc.GENERAL_SCALE_SUBSET, no_arrow_button=True, width=340, 
                                tag="general_scale_list", callback=set_general_scale_from_all)
                dpg.add_text(" in ")
                dpg.add_combo(mu.CHROMA_NAMES[gc.TONIC_CHROMA_SUBSET].tolist(), no_arrow_button=True, width=60,
                                tag="tonic_chroma_list", callback=set_tonic_chroma_from_all)
                dpg.add_text(" -  Alternative names: ")
                dpg.add_text(gc.SELECTED_SCALE.name, tag="scale_alternative_names")
            dpg.add_separator()
            with dpg.group(horizontal=True):
                with dpg.group(horizontal=False):
                    dpg.add_text("Rotations:", bullet=True)
                    dpg.add_listbox(gc.ROTATIONS_SCALES, width=360, tag="scale_rotations_list", #type:ignore
                                    user_data="rotations", callback=set_scale_from_navigation)
                with dpg.group(horizontal=False):
                    dpg.add_text("Children:", bullet=True)
                    dpg.add_listbox(gc.CHILDREN_SCALES, width=360, tag="scale_children_list", #type:ignore
                                    user_data="children", callback=set_scale_from_navigation)
                with dpg.group(horizontal=False):
                    dpg.add_text("Parents:", bullet=True)
                    dpg.add_listbox(gc.PARENTS_SCALES, width=360, tag="scale_parents_list", #type:ignore
                                    user_data="parents", callback=set_scale_from_navigation) 
        


dpg.set_axis_ticks("imgy", tuple((mu.MIDI_NAMES[i], i) for i in range(0, 120, 12)))
set_metric(None, "bartime", None)
update_selected_scale()

try:
    load_midi(MidiFrame.EXPORT_DEFAULT_FILEPATH, "TMP_Files", "Last played")
except:
    pass

dpg.create_viewport(title='Improvisation Guidance Tool', width=1200, height=800)
dpg.set_primary_window("primary_window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

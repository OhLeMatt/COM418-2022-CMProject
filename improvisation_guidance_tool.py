import dearpygui.dearpygui as dpg
from music_tools.midi_frame import MidiFrame
# import music_tools.scales as scales
import music_tools.midi_utils as mu

import gui.context as gc
from gui.file_loading_callbacks import *
from gui.setter_callbacks import *
from gui.interactive_callbacks import *
from gui.visualizations import *
            
###########################    UI ELEMENTS     ########################### 
            
def draw_midi_player_ui():
    with dpg.collapsing_header(label="Midi Player", default_open=True):
        with dpg.group(horizontal=True):
            dpg.add_button(label="File Selector", callback=lambda: dpg.show_item("file_dialog_id"))
            dpg.add_button(label="Random", callback=random_midi)
            dpg.add_text(label="PlayText", default_value="No file selected", tag="PlayText")
        
        with dpg.group(horizontal=True):
            dpg.add_image_button("play", callback=play_midi, tag="PlayButton", user_data=True, width=15, height=15)
            dpg.add_image_button("stop", callback=play_midi, tag="StopButton", user_data=False, width=15, height=15)
            dpg.add_checkbox(label="Follow Cursor", callback=set_follow_cursor, tag="FollowCursor", default_value=gc.FOLLOW_CURSOR)
            dpg.add_slider_int(format="volume (%d%%) ", tag="volume", min_value=0, max_value=100, default_value=50, callback=set_volume, width=100)
            dpg.add_combo(("Ticks", "Time", "Bartime"), label="", tag="MetricSelector", default_value="Bartime", callback=set_metric, width=80)
            dpg.add_text("Color Legend")
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

        with dpg.plot(label="Midi Visualiser", height=340, width=-1, tag="midiviz"):
            dpg.add_plot_axis(dpg.mvXAxis, label="Bartime", tag="imgx")
            dpg.add_plot_axis(dpg.mvYAxis, label="Note", tag="imgy")
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
            
def draw_suggestions_settings_ui():
    with dpg.collapsing_header(label="Suggestion Settings", indent=12):
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
 
def draw_suggestions_ui():
    with dpg.collapsing_header(label="Suggestions", tag="suggestion_tab", default_open=True):
        draw_suggestions_settings_ui()
        dpg.add_button(label="Compute Suggestions", callback=compute_suggestions)
        
        with dpg.table(header_row=True, 
                tag="suggestion_content", 
                scrollY=True, 
                policy=dpg.mvTable_SizingStretchProp,
                resizable=True, borders_innerV=True):
        
            dpg.add_table_column(label="Scale", width=gc.TABLE_SCALE_NAME_WIDTH, width_fixed=True)
            dpg.add_table_column(label="Accuracy", width=gc.TABLE_ACCURACY_WIDTH, width_fixed=True)
            dpg.add_table_column(label="Notes", width=gc.TABLE_NOTECOUNT_WIDTH, width_fixed=True)
            dpg.add_table_column(label="Alternate names", width_stretch=True, init_width_or_weight=0.0)
 
def draw_improvisation_material_ui():
    with dpg.group(horizontal=True):
        with dpg.child_window(menubar=True, autosize_x=True):
            with dpg.menu_bar():
                dpg.add_text("Scale Navigation")
            with dpg.group(horizontal=True):
                dpg.add_text("Selected Scale: ")
                dpg.add_combo(gc.GENERAL_SCALE_SUBSET, no_arrow_button=True, width=340, 
                                tag="general_scale_list", callback=set_general_scale_from_all)
                dpg.add_text(" in ")
                dpg.add_combo(mu.CHROMA_NAMES[gc.TONIC_CHROMA_SUBSET].tolist(), no_arrow_button=True, width=60,
                                tag="tonic_chroma_list", callback=set_tonic_chroma_from_all)
            with dpg.group(horizontal=True):
                dpg.add_text("Alternative names: ")
                dpg.add_text(gc.SELECTED_SCALE.name, tag="scale_alternative_names")
            dpg.add_separator()
            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text("Rotations:", bullet=True)
                    dpg.add_listbox(gc.ROTATIONS_SCALES, width=300, tag="scale_rotations_list", #type:ignore
                                    num_items=8, user_data="rotations", callback=set_scale_from_navigation)
                with dpg.group():
                    dpg.add_text("Children:", bullet=True)
                    dpg.add_listbox(gc.CHILDREN_SCALES, width=300, tag="scale_children_list", #type:ignore
                                    num_items=3, user_data="children", callback=set_scale_from_navigation)
            
                    dpg.add_text("Parents:", bullet=True)
                    dpg.add_listbox(gc.PARENTS_SCALES, width=300, tag="scale_parents_list", #type:ignore
                                    num_items=3, user_data="parents", callback=set_scale_from_navigation) 
            draw_suggestions_ui()

def draw_scale_visualizations_ui():
    with dpg.child_window():
        with dpg.tab_bar():
            with dpg.tab(label="Chromas"):    
                draw_empty_scale(gc.EN_NOTES_DISPLAY, gc.FR_NOTES_DISPLAY, x_factor=0.9)
                with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
                    dpg.add_table_column()
                    for i in range(4):
                        with dpg.table_row(): 
                            with dpg.group():
                                dpg.add_text(f"Suggested Chord {i+1}:")
                                draw_empty_scale(x_factor=0.5, y_factor=0.45, prefix=f"chord{i}")
                
            with dpg.tab(label="Piano", indent=10):
                with dpg.group(horizontal=True, horizontal_spacing=1):
                    draw_empty_piano(gc.EN_NOTES_DISPLAY, gc.FR_NOTES_DISPLAY)
                    draw_empty_piano(gc.EN_NOTES_DISPLAY, gc.FR_NOTES_DISPLAY, prefix="+")
                with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    for i in range(2):
                        with dpg.table_row():
                            for j in range(2):
                                with dpg.group():
                                    k = i*2 + j + 1
                                    dpg.add_text(f"Suggested Chord {k}:")
                                    draw_empty_piano(x_factor=0.5, y_factor=0.4, prefix=f"chord{k}")


            # with dpg.tab(label="Guitar"):
            #     draw_empty_guitar(gc.EN_NOTES_DISPLAY, gc.FR_NOTES_DISPLAY)

FONTS_FOLDER = "gui/fonts/"
TEXTURES_FOLDER = "gui/textures/"

dpg.create_context()

dpg.add_texture_registry(label="Texture Container", tag="texture_container")
dpg.add_static_texture(1, 1, [1,1,1,1], parent="texture_container", tag="Texture_C", label="Texture_C")
dpg.add_static_texture(1, 1, [1,1,1,0.05], parent="texture_container", tag="TransparentWindowTexture", label="TransparentWindowTexture")
width, height, channels, data = dpg.load_image(TEXTURES_FOLDER+"play.png")
dpg.add_static_texture(width=width, height=height, default_value=data, tag="play", parent="texture_container")
width, height, channels, data = dpg.load_image(TEXTURES_FOLDER+"pause.png")
dpg.add_static_texture(width=width, height=height, default_value=data, tag="pause", parent="texture_container")
width, height, channels, data = dpg.load_image(TEXTURES_FOLDER+"stop.png")
dpg.add_static_texture(width=width, height=height, default_value=data, tag="stop", parent="texture_container")

with dpg.font_registry():
    # first argument ids the path to the .ttf or .otf file
    DEFAULT_FONT = dpg.add_font(FONTS_FOLDER+"OpenSans-SemiBold.ttf", 15)
    dpg.bind_font(DEFAULT_FONT)


with dpg.file_dialog(directory_selector=False, show=False, callback=select_file, id="file_dialog_id", height=300):
    dpg.add_file_extension(".mid")
    dpg.add_file_extension("", color=(150, 255, 150, 255))

with dpg.window(label="Improvisation Tool", 
                width=1200, 
                height=700, 
                tag="primary_window",
                no_title_bar=True, 
                no_move=True):
    
    draw_midi_player_ui()
    with dpg.table(header_row=False, resizable=True, borders_innerV=True):
        dpg.add_table_column()
        dpg.add_table_column()
        with dpg.table_row():
            draw_improvisation_material_ui()
            with dpg.group(horizontal=True):
                draw_scale_visualizations_ui()

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

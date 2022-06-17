
from pickle import GLOBAL
import weakref
import dearpygui.dearpygui as dpg
from sklearn import metrics
from midi_frame import MidiFrame, MidiTrackFrame
from midi_player import MidiPlayer
import scales
from os import listdir
from os.path import isfile, join
import midi_utils as mu
import random
import time


###########################    Init Variables     ########################### 
inputMidi = None

MIDI_PATH = "MIDI_Files"
MIDIFILES = [f for f in listdir(MIDI_PATH) if isfile(join(MIDI_PATH, f))]
PLOT_DISPLAYED = False
NORMALIZE_SCORES = False
WEIGHTED = False
THRESHOLD = 0.9
METRIC = "ticks"
BAR_WINDOW = [0,0]
WINDOW = [0,0]
WIN_POSITION = 10000
NUM_BARS = 4
NOTE_COUNTS = set(i for i in range(5,13))
GENERAL_SCALE_SUBSET = scales.create_general_scale_subset(NOTE_COUNTS)
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

dpg.create_context()

dpg.add_texture_registry(label="Texture Container", tag="texture_container")
dpg.add_static_texture(1, 1, [1,1,1,1], parent="texture_container", tag="Texture_C", label="Texture_C")
dpg.add_static_texture(1, 1, [1,1,1,0.1], parent="texture_container", tag="TransparentWindowTexture", label="TransparentWindowTexture")

###########################    Callback & utility functions     ########################### 

def _log(sender, app_data, user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
        
        
def random_midi(sender, app_data, user_data):
    midi_name = random.choice(MIDIFILES)
    random_file = MIDI_PATH + "/" + midi_name

    load_midi(random_file, MIDI_PATH, midi_name)

def select_file(sender, app_data, user_data):
    path = app_data['current_path']  # path to sound font file
    midi_file = app_data['file_path_name']

    load_midi(midi_file, path, app_data['file_name'])

# Utility function to load selected midi file 
def load_midi(midi_file, path, name):
    print("Filename: ", midi_file)

    global inputMidi 

    if inputMidi is not None: 
        inputMidi.stop()

    inputMidi = MidiPlayer(midi_file, path)
    inputMidi.on_cursor_change_listeners.append(update_ui_cursor)
    inputMidi.on_cursor_change_listeners.append(update_ui_window)

    dpg.set_value("PlayText", "Selected: " + name)
    dpg.set_item_label("PlayButton", "Play")
    display(None, None, None)
    if not inputMidi.displayable:
        dpg.set_value("WarningText", "Warning: this midi file is not displayable")
    else:
        dpg.set_value("WarningText", "")
    

def play_midi(sender, app_data, user_data):
    if inputMidi is not None:
        # user_data is either playpause at True, stop at False
        if user_data:
            if inputMidi.playing:
                inputMidi.pause()
                dpg.set_item_label("PlayButton", "Play")
            else:
                inputMidi.play()
                dpg.set_item_label("PlayButton", "Pause")
        else:
            inputMidi.stop()
            dpg.set_item_label("PlayButton", "Play")
            

def display(sender, app_data, user_data):
    if inputMidi is not None and inputMidi.displayable:
        global PLOT_DISPLAYED, METRIC, WEIGHTED

        if PLOT_DISPLAYED:
            dpg.delete_item("imgy", children_only=True)
            PLOT_DISPLAYED = False

        if not PLOT_DISPLAYED: 
            dpg.set_axis_limits("imgy", inputMidi.min_note - 1, inputMidi.max_note + 1)
            #dpg.set_axis_limits("imgx", 0, 100)
            # dpg.set_axis_limits_auto("imgx")
            #dpg.set_axis_limits_auto("imgx")
                    
            PLOT_DISPLAYED = True
            if len(inputMidi.df) > 0:
                metric_release = METRIC + "_release"
                df_copy = inputMidi.df[[METRIC, "note", metric_release, "weight"]]
                for i, x in df_copy.iterrows():
                    
                    tint = get_note_colour(x.note)
                    if WEIGHTED:
                        tint[0] *= x.weight
                        tint[1] *= x.weight
                        tint[2] *= x.weight
                    
                    dpg.add_image_series("Texture_C", 
                                         [x[METRIC], x.note - 0.5], [x[metric_release], x.note + 0.5], 
                                         label="C", tag=f"MidiNote{i}", parent="imgy", tint_color=tuple(tint))
                dpg.fit_axis_data("imgx")

# Get colour texture for each note (in progress)
def get_note_colour(note):
    return NOTE_COLORS[int(note) % 12].copy()

def channel_selection(sender, app_data, user_data):
    if inputMidi is not None:
        change = False
        if app_data:
            change = inputMidi.add_channel(user_data)
        else: 
            change = inputMidi.remove_channel(user_data)
        if change:
            display(None, None, None)
        print("channels: " + str(inputMidi.channels))

def set_threshold(sender, app_data, user_data):
    global THRESHOLD
    THRESHOLD = app_data

def set_scale(sender, app_data, user_data):
    print("scale: " + str(app_data))

def ui_cursor_change(sender, app_data, user_data):
    if inputMidi is not None:
        inputMidi.update_cursor(dpg.get_value(sender), metric=METRIC, exclude_listeners=[0])


def set_notecounts(sender, app_data, user_data):
    global NOTE_COUNTS, GENERAL_SCALE_SUBSET
    if app_data:
        NOTE_COUNTS.add(user_data)
    else:
        NOTE_COUNTS.remove(user_data)
    GENERAL_SCALE_SUBSET = scales.create_general_scale_subset(NOTE_COUNTS)
    print(f"note counts selected: {NOTE_COUNTS} | number of general scales: {len(GENERAL_SCALE_SUBSET)}")
    print("note counts selected: " + str(user_data))

# def view_change(sender, app_data, user_data):
#     dpg.set_axis_limits("imgx", app_data, app_data + 100)

def set_normalize(sender, app_data, user_data):
    global NORMALIZE
    NORMALIZE = app_data

def set_weighted(sender, app_data, user_data):
    global WEIGHTED
    WEIGHTED = app_data
    print(WEIGHTED)
    display(None, None, None)

def set_metric(sender, app_data, user_data):
    global METRIC
    METRIC = app_data
    dpg.set_item_label("imgx", app_data.capitalize())
    display(None, None, None)

def set_num_bars(sender, app_data, user_data):
    dpg.show_item("ui_window")
    global NUM_BARS, METRIC
    if user_data:
        NUM_BARS = NUM_BARS + 1
    else:
        NUM_BARS = NUM_BARS - 1
    dpg.set_value("num_bars", NUM_BARS)
    if inputMidi is not None:
        inputMidi.update_window(barsize=NUM_BARS)
        update_ui_window(inputMidi)

def update_ui_cursor(midiplayer: MidiPlayer):
    dpg.set_value("ui_cursor", midiplayer.cursor[METRIC])

def update_ui_window(midiplayer: MidiPlayer):
    global WINDOW, METRIC
    WINDOW[0] = midiplayer.convert_unit(midiplayer.analysis_window[0], "bartime", METRIC)
    WINDOW[1] = midiplayer.convert_unit(midiplayer.analysis_window[1], "bartime", METRIC)
    dpg.configure_item("ui_window", bounds_min=(WINDOW[0], 0), bounds_max=(WINDOW[1], 128))

    # WIN_POSITION = int(dpg.get_value("drag_window"))
    # dpg.delete_item("drag_window")
    # dpg.add_drag_line(label="drag_window", color=[0, 164, 255, 50], tag="drag_window", parent="midiviz", default_value=WIN_POSITION, thickness=NUM_BARS)

def remove_win(sender, app_data, user_data):
    dpg.hide_item("ui_window")

def get_suggestion(sender, app_data, user_data):
    if inputMidi is not None: 
        suggestion = inputMidi.get_suggestion()

        dpg.delete_item("suggestion_content")

        with dpg.table(header_row=False, tag="suggestion_content", parent="suggestion_tab"):

            
            # use add_table_column to add columns to the table,
            # table columns use slot 0
            dpg.add_table_column()
            dpg.add_table_column()
            dpg.add_table_column()
            dpg.add_table_column()

            for i in range(len(suggestion)):
                with dpg.table_row(parent="suggestion_content"):
                        dpg.add_text(suggestion[i]["name"])
                        dpg.add_text(suggestion[i]["accuracy"])
                        dpg.add_text(suggestion[i]["note_count"])
                        dpg.add_text(suggestion[i]["alternate_names"])

def set_volume(sender, app_data, user_data):
    if inputMidi is not None: 
        inputMidi.set_volume(app_data)


###########################    UI     ########################### 

with dpg.file_dialog(directory_selector=False, show=False, callback=select_file, id="file_dialog_id", height=300):
    dpg.add_file_extension(".mid")
    dpg.add_file_extension("", color=(150, 255, 150, 255))

with dpg.window(label="Improvisation Tool", 
                width=1000, 
                height=600, 
                tag="primary_window",
                no_title_bar=True, 
                no_move=True):
    
    with dpg.collapsing_header(label="Midi Player", default_open=True):
        with dpg.group(horizontal=True):
            dpg.add_button(label="File Selector", callback=lambda: dpg.show_item("file_dialog_id"))
            dpg.add_button(label="Random", callback=random_midi)
        dpg.add_text(label="PlayText", default_value="No file selected", tag="PlayText")
        dpg.add_text(label="WarningText", default_value="", tag="WarningText")
        with dpg.group(horizontal=True):
            dpg.add_button(label="Play", callback=play_midi, tag="PlayButton", user_data=True)
            dpg.add_button(label="Stop", callback=play_midi, tag="StopButton", user_data=False)
            dpg.add_button(label="Reset Display", callback=display, tag="DisplayButton")
            dpg.add_drag_int(format="volume = %d ", tag="volume", min_value=0, max_value=10, default_value=1, callback=set_volume, width=100)
            dpg.add_combo(("ticks", "time", "bartime"), label="", tag="MetricSelector", default_value="ticks", callback=set_metric, width=80)
            dpg.add_text("colour code")
            with dpg.tooltip(dpg.last_item()):
                with dpg.table(tag="colour-code", header_row=False):
                    
                    for i in range(12):
                        dpg.add_table_column()
                   
                    with dpg.table_row():
                        dpg.add_text("C")
                        dpg.add_text("C#")
                        dpg.add_text("D")
                        dpg.add_text("D#")
                        dpg.add_text("E")
                        dpg.add_text("F")
                        dpg.add_text("F#")
                        dpg.add_text("G")
                        dpg.add_text("G#")
                        dpg.add_text("A")
                        dpg.add_text("A#")
                        dpg.add_text("B")

                    with dpg.table_row():
                        for colour in NOTE_COLORS:
                            dpg.add_image("Texture_C", width=15, height=15, tint_color=tuple(colour))




        with dpg.plot(label="Midi Visualiser", height=400, width=-1, tag="midiviz"):
            
            xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="imgx")
            yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="Note", tag="imgy")
            dpg.add_drag_line(label="ui_cursor",
                                color=[100, 164, 255, 200],
                                tag="ui_cursor",
                                parent="midiviz",
                                default_value=0,
                                thickness=1,
                                callback=ui_cursor_change)
            dpg.add_image_series("TransparentWindowTexture", 
                                 [0, 0], [1,128], 
                                 tag="ui_window", parent="imgx")
        
        # max_len = 100 if inputMidi is None else inputMidi.length
        # dpg.add_slider_int(label="ViewSlider", max_value=max_len, callback=view_change)


    with dpg.collapsing_header(label="Midi Settings"):
        with dpg.group(horizontal=True): 
            dpg.add_text(label="label", default_value="Select Midi Channels: ")
            for i in range(0,16):
                dpg.add_checkbox(label=str(i), callback=channel_selection, default_value=True, user_data=i)


    with dpg.collapsing_header(label="Suggestion Settings"):
        with dpg.group(horizontal=True): 
            dpg.add_checkbox(label="Normalize Accuracy", callback=set_normalize, default_value=False)
            dpg.add_checkbox(label="Weighted by Beat Importance", callback=set_weighted, default_value=False)
        dpg.add_text("Compute suggestion over: ")
        with dpg.group(horizontal=True): 
            # dpg.add_button(label="Choose Window", callback=show_window_select)
            dpg.add_text("Bars: ")
            dpg.add_button(arrow=True, direction=dpg.mvDir_Left, user_data=False, callback=set_num_bars)
            dpg.add_text(str(NUM_BARS), tag="num_bars")
            dpg.add_button(arrow=True, direction=dpg.mvDir_Right, user_data=True, callback=set_num_bars)

            # dpg.add_button(label="Apply", callback=apply_window)
            dpg.add_text(label="WindowText", default_value="", tag="WindowText")
            
            dpg.add_button(label="Entire file", callback=remove_win)
        with dpg.group():
            dpg.add_slider_float(label="Accuracy Threshold", 
                                 max_value=1.0, 
                                 format="threshold = %.3f", 
                                 callback=set_threshold, 
                                 default_value=0.9)

        with dpg.group(horizontal=True): 
            dpg.add_text(label="label", default_value="Select amount of notes: ")
            for i in range(5,13):
                dpg.add_checkbox(label=str(i), callback=set_notecounts, default_value=True, user_data=i)

    with dpg.collapsing_header(label="Suggestion", tag="suggestion_tab"):
        dpg.add_button(label="Compute Suggestion", callback=get_suggestion)

        with dpg.table(header_row=False, tag="suggestion_table"):

            
            # use add_table_column to add columns to the table,
            # table columns use slot 0
            dpg.add_table_column()
            dpg.add_table_column()
            dpg.add_table_column()
            dpg.add_table_column()

            with dpg.table_row():
                dpg.add_text("Scale")
                dpg.add_text("Accuracy")
                dpg.add_text("Note count")
                dpg.add_text("Alternate names")
            dpg.highlight_table_row("suggestion_table",0, [10, 0, 50, 100])

        with dpg.table(header_row=False, tag="suggestion_content"):    
            dpg.add_table_column()
            


        # with dpg.group(horizontal=True):
        #     dpg.add_text(label="label", default_value="None", tag="scale_suggestion_text_0")
        #     dpg.add_text(label="label", default_value="       ")
        #     dpg.add_text(label="label", default_value="Accuracy: ")
        #     dpg.add_text(label="label", default_value="0", tag="suggestion accuracy_0")
        #     dpg.add_text(label="label", default_value="%")
        # with dpg.group(horizontal=True):
        #     dpg.add_text(label="label", default_value="Other", tag="scale_suggestion_text_1")
        #     dpg.add_text(label="label", default_value="       ")
        #     dpg.add_text(label="label", default_value="Accuracy: ")
        #     dpg.add_text(label="label", default_value="23", tag="suggestion accuracy_1")
        #     dpg.add_text(label="label", default_value="%")

# FORCED INIT

set_metric(None, "ticks", None)

dpg.set_axis_ticks("imgy", tuple((mu.MIDI_NAMES[i], i) for i in range(0, 120, 12)))


dpg.create_viewport(title='Improvisation Helper', width=1000, height=600)
dpg.set_primary_window("primary_window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
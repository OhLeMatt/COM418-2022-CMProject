from email.policy import default
import dearpygui.dearpygui as dpg
import mido
from pretty_midi import PrettyMIDI
import sounddevice as sd
import midi_utils as mu
from midi_frame import MidiFrame, MidiTrackFrame
from os import listdir
from os.path import isfile, join
import random
import time

###########################    Init Variables     ########################### 

midi_path = "MIDI_Files"
midifiles = [f for f in listdir(midi_path) if isfile(join(midi_path, f))]
plot_displayed = False
inputMidi = None
normalize = False
weighted = True
window = [0,100]
win_position = 10000
num_bars = 100 

## create static textures
texture_c = []
for i in range(30*30):
    texture_c.append(255/255)
    texture_c.append(255/255)
    texture_c.append(255/255)
    texture_c.append(255/255)

dpg.create_context()

dpg.add_texture_registry(label="Demo Texture Container", tag="__demo_texture_container")
dpg.add_static_texture(30, 30, texture_c, parent="__demo_texture_container", tag="Texture_C", label="Texture_C")

###########################    Midi Class     ########################### 

class Midi: 
    def __init__(self, file_name, path):
        self.file_name = file_name 
        self.path = path
        self.playing = False

        self.channels = [i for i in range(0,16)]
        self.as_mido = mido.MidiFile(filename=self.file_name)
        
        self.midiframe = MidiFrame(self.as_mido)

        self.Fs = 22050
        self.refresh_dataframe()

        

    def refresh_dataframe(self):
        self.midiframe.make_playing_track_frame(self.channels)
        self.df = self.midiframe.playing_track_frame.dataframe
        
        #self.displayable = True if ('note' in self.df and self.df["time_duration"].iloc[1] is not None) else False
        # self.displayable = True if 'note' in self.df else False
        self.displayable = True
        
        if self.displayable and len(self.df) > 0: 
            self.min_note = self.df['note'].min()
            self.max_note = self.df['note'].max()        
            self.length = self.df["ticks"].iloc[-1] + 5
            print("midi length: " + str(self.length))
            global window
            window = [0, self.length]
        self.midiframe.export_playing_track()
        
        # music = PrettyMIDI(midi_file=file_name)
        music = PrettyMIDI(midi_file="MIDI_Files/tmp.mid")
        was_playing = self.playing
        self.stop()
        self.audio_data = music.synthesize(fs=self.Fs)
        if was_playing:
            self.play()

    def add_channel(self, channel):
        if channel not in self.channels: 
            self.channels.append(channel)
            self.refresh_dataframe()
        
    def remove_channel(self, channel):
        if channel in self.channels: 
            self.channels.remove(channel)
            self.refresh_dataframe()

    def play(self):
        if not self.playing:
            sd.play(self.audio_data, self.Fs)
            self.playing = True
        else:
            self.stop()

    def stop(self):
        if self.playing:
            sd.stop()
            self.playing = False
        else: 
            print("Not playing")


###########################    Callback functions     ########################### 

def _log(sender, app_data, user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
        
        
def random_midi(sender, app_data, user_data):
    midi_name = random.choice(midifiles)
    random_file = midi_path + "/" + midi_name

    load_midi(random_file, midi_path, midi_name)


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

    inputMidi = Midi(midi_file, path)

    dpg.set_value("PlayText", "Selected: " + name)
    #dpg.set_item_label("PlayButton", "Play")

    if not inputMidi.displayable:
        dpg.set_value("WarningText", "Warning: this midi file is not displayable")
    else:
        dpg.set_value("WarningText", "")
    

def play_midi(sender, app_data, user_data):
    if inputMidi is not None:
        inputMidi.play()
        
        if inputMidi.playing:
            dpg.set_item_label("PlayButton", "Stop")
        else:
            dpg.set_item_label("PlayButton", "Play")
            

        
def display(sender, app_data, user_data):
    if inputMidi is not None and inputMidi.displayable:
        global plot_displayed

        if plot_displayed:
            dpg.delete_item("imgy", children_only=True)
            plot_displayed = False

        if not plot_displayed: 
            dpg.set_axis_limits("imgy", inputMidi.min_note - 1, inputMidi.max_note + 1)
            #dpg.set_axis_limits("imgx", 0, 100)
            # dpg.set_axis_limits_auto("imgx")
            #dpg.set_axis_limits_auto("imgx")
                    
            plot_displayed = True

            if len(inputMidi.df) > 0:
                df_copy = inputMidi.df[["ticks", "note", "ticks_duration"]]
                for i, x in df_copy.iterrows():
                    td = 0.2 if not x.ticks_duration else x.ticks_duration
                    tint = get_note_colour(x.note)
                    dpg.add_image_series("Texture_C", [x.ticks, x.note - 0.5], [x.ticks + td, x.note + 0.5], label="C", parent="imgy", tint_color=tint)
                
                dpg.fit_axis_data("imgx")

# Get colour texture for each note (in progress)
def get_note_colour(note):
    mod_note = note % 12

    switcher = {
        0: (255,0,0), # C
        1: (255,127,0),  # C#
        2: (255,255,0),  # D
        3: (0,127,0), # D#
        4: (0,255,0),  # E
        5: (0,255,147),  # F
        6: (0,255,255), # F#
        7: (0,127,255),  # G
        8: (0,0,255),  # G#
        9: (127,0,255), # A 
        10: (255,0,255), # A#
        11: (255,0,127), # B
    }
    return switcher.get(mod_note, (255,255,255))

def channel_selection(sender, app_data, user_data):
    if inputMidi is not None:
        if app_data:
            inputMidi.add_channel(user_data)
        else: 
            inputMidi.remove_channel(user_data)
        
        print("channels: " + str(inputMidi.channels))

def set_w_threshold(sender, app_data, user_data):
    print("threshold: " + str(app_data))

def set_t_threshold(sender, app_data, user_data):
    print("threshold: " + str(app_data))

def set_scale(sender, app_data, user_data):
    print("scale: " + str(app_data))

def set_notecounts(sender, app_data, user_data):
    print("note counts selected: " + str(user_data))

# def view_change(sender, app_data, user_data):
#     dpg.set_axis_limits("imgx", app_data, app_data + 100)

def set_normalize(sender, app_data, user_data):
    normalize = app_data

def set_weighted(sender, app_data, user_data):
    weighted = app_data

def show_window_select(sender, app_data, user_data):
    dpg.add_drag_line(label="drag_window", color=[0, 164, 255, 50], tag="drag_window", parent="midiviz", default_value=win_position, thickness=num_bars)
    print("Drag line:" + str(app_data))

def apply_window(sender, app_data, user_data):
    global win_position, window, num_bars
    win_position = int(dpg.get_value("drag_window"))
    dpg.delete_item("drag_window")

    thicc = int(num_bars/2)
    window = [win_position-thicc, win_position+thicc]
    dpg.set_value("WindowText", "Window: " + str(window))

def set_num_bars(sender, app_data, user_data):
    global num_bars, win_position
    if user_data:
        num_bars = num_bars + 1
    else:
        num_bars = num_bars - 1

    dpg.set_value("num_bars", num_bars)

    win_position = int(dpg.get_value("drag_window"))
    dpg.delete_item("drag_window")
    dpg.add_drag_line(label="drag_window", color=[0, 164, 255, 50], tag="drag_window", parent="midiviz", default_value=win_position, thickness=num_bars)

    

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
            dpg.add_button(label="Play", callback=play_midi, tag="PlayButton")
            dpg.add_button(label="Display", callback=display, tag="DisplayButton")



        with dpg.plot(label="Midi Visualiser", height=300, width=-1, tag="midiviz"):
            xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="imgx")
            yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="Note", tag="imgy")
        
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
            dpg.add_checkbox(label="Weighted", callback=set_weighted, default_value=False)
        with dpg.group(horizontal=True): 
            dpg.add_button(label="Choose Window", callback=show_window_select)
            dpg.add_text("Bars: ")
            dpg.add_button(arrow=True, direction=dpg.mvDir_Left, user_data=False, callback=set_num_bars)
            dpg.add_text(str(num_bars), tag="num_bars")
            dpg.add_button(arrow=True, direction=dpg.mvDir_Right, user_data=True, callback=set_num_bars)

            dpg.add_button(label="Apply", callback=apply_window)
            dpg.add_text(label="WindowText", default_value="", tag="WindowText")
        with dpg.group():
            dpg.add_slider_float(label="Window Threshold", max_value=1.0, format="threshold = %.3f", callback=set_w_threshold)
            dpg.add_slider_float(label="Total Threshold", max_value=1.0, format="threshold = %.3f", callback=set_t_threshold)

        with dpg.group(horizontal=True): 
            dpg.add_text(label="label", default_value="Select amount of notes: ")
            for i in range(5,13):
                dpg.add_checkbox(label=str(i), callback=set_notecounts, default_value=True, user_data=i)


    with dpg.collapsing_header(label="Suggestion"):
        dpg.add_text(label="label", default_value="Suggested Scales: ")
        with dpg.group(horizontal=True):
            dpg.add_text(label="label", default_value="None", tag="scale_suggestion_text_0")
            dpg.add_text(label="label", default_value="       ")
            dpg.add_text(label="label", default_value="Accuracy: ")
            dpg.add_text(label="label", default_value="0", tag="suggestion accuracy_0")
            dpg.add_text(label="label", default_value="%")
        with dpg.group(horizontal=True):
            dpg.add_text(label="label", default_value="Other", tag="scale_suggestion_text_1")
            dpg.add_text(label="label", default_value="       ")
            dpg.add_text(label="label", default_value="Accuracy: ")
            dpg.add_text(label="label", default_value="23", tag="suggestion accuracy_1")
            dpg.add_text(label="label", default_value="%")


dpg.create_viewport(title='Improvisation Helper', width=1000, height=600)
dpg.set_primary_window("primary_window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
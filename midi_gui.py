import dearpygui.dearpygui as dpg
import mido
from pretty_midi import PrettyMIDI
import sounddevice as sd
import midi_utils as mu
from midi_frame import MidiFrame, MidiTrackFrame
from os import listdir
from os.path import isfile, join
import random

midi_path = "MIDI_Files"

midifiles = [f for f in listdir(midi_path) if isfile(join(midi_path, f))]

plot_displayed = False

## create static textures
texture_data1 = []
for i in range(100*100):
    texture_data1.append(255/255)
    texture_data1.append(0)
    texture_data1.append(255/255)
    texture_data1.append(255/255)

class Midi: 

    def __init__(self, file_name, path):
        self.file_name = file_name 
        self.path = path
        self.playing = False

        music = PrettyMIDI(midi_file=file_name)
        
        self.Fs = 22050
        self.audio_data = music.synthesize(fs=self.Fs)
        self.x_values = range(0, len(self.audio_data))

        self.channels = [i for i in range(0,16)]

        self.as_mido = mido.MidiFile(filename=self.file_name)
        self.midiframe = MidiFrame(self.as_mido)
        # HARDSCRIPTED FOR NOW
        self.df = self.midiframe.track_frames[0].dataframe

        print(self.df)

        self.displayable = True  if ('note' in self.df and self.df["time_duration"].iloc[1] is not None) else False

        if self.displayable: 
            self.min_note = self.df['note'].min()
            self.max_note = self.df['note'].max()        
            self.length = self.df["time_release"].iloc[-1] if self.df["time_release"].iloc[-1] is not None else self.df["time"].iloc[-1] + self.df["time_duration"].iloc[-1]
            print("midi length: " + str(self.length))


    def add_channel(self, channel):
        if channel not in self.channels: 
            self.channels.append(channel)

        
    def remove_channel(self, channel):
        if channel in self.channels: 
            self.channels.remove(channel)


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

inputMidi = None

dpg.create_context()

dpg.add_texture_registry(label="Demo Texture Container", tag="__demo_texture_container")
dpg.add_static_texture(10, 10, texture_data1, parent="__demo_texture_container", tag="__demo_static_texture_1", label="Static Texture 1")


def select_midi(sender, app_data, user_data):
    global inputMidi 

    if inputMidi is not None: 
        inputMidi.stop()

    path = app_data['current_path']  # path to sound font file
    midi_file = app_data['file_path_name']
    print("Sender: ", sender)
    print("App Data: ", app_data)
    print("Filename: ", midi_file)

    music = PrettyMIDI(midi_file=midi_file)
    Fs = 22050
    audio_data = music.synthesize(fs=Fs)

    inputMidi = Midi(midi_file, path)

    dpg.set_value("PlayText", "Selected: " + app_data['file_name'])
    dpg.set_item_label("PlayButton", "Play")

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
            dpg.set_axis_limits("imgx", 0, inputMidi.length)
        
            plot_displayed = True

            df_copy = inputMidi.df[["time", "note", "time_duration", "time_release"]]

            for i, x in df_copy.iterrows():
                td = 1 if not x.time_duration else x.time_duration
                dpg.add_image_series("__demo_static_texture_1", [x.time, x.note - 0.5], [x.time + x.time_duration, x.note + 0.5], label="static 1", parent="imgy")




def _log(sender, app_data, user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
        

def random_midi(sender, app_data, user_data):
    global inputMidi

    if inputMidi is not None: 
        inputMidi.stop()

    random_file = random.choice(midifiles)
    #random_file = "KCP_Major_1.mid"

    dpg.set_value("PlayText", "Selected: " + random_file)
    dpg.set_item_label("PlayButton", "Play")

    random_file = midi_path + "/" + random_file

    inputMidi = Midi(random_file, midi_path)

    if not inputMidi.displayable:
        dpg.set_value("WarningText", "Warning: this midi file is not displayable")
    else:
        dpg.set_value("WarningText", "")


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

with dpg.file_dialog(directory_selector=False, show=False, callback=select_midi, id="file_dialog_id", height=300):
    dpg.add_file_extension(".mid")
    dpg.add_file_extension("", color=(150, 255, 150, 255))

with dpg.window(label="Improvisation Tool", width=1000, height=600, tag="MidiPlayer"):
    with dpg.collapsing_header(label="Midi Player"):
        with dpg.group(horizontal=True):
            dpg.add_button(label="File Selector", callback=lambda: dpg.show_item("file_dialog_id"))
            dpg.add_button(label="Random", callback=random_midi)
        dpg.add_text(label="PlayText", default_value="No file selected", tag="PlayText")
        dpg.add_text(label="WarningText", default_value="", tag="WarningText")
        with dpg.group(horizontal=True):
            dpg.add_button(label="Play", callback=play_midi, tag="PlayButton")
            dpg.add_button(label="Display", callback=display, tag="DisplayButton")

        # with dpg.plot(label="MidiPlot", height=200, width=1000):
        #     dpg.add_plot_legend()
        #     dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_axis")
        #     dpg.add_plot_axis(dpg.mvYAxis, label="Freq", tag="y_axis")
        #     #dpg.add_line_series([], [-1,0,1], tag="LineSerie", parent="y_axis")
        #     #dpg.add_simple_plot(label="Midi Plot", default_value=inputMidi.audio_data, parent="MidiPlayer")

        with dpg.plot(label="Midi Visualiser", height=200, width=-1):

            xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="imgx")
            yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="Note", tag="imgy")


    with dpg.collapsing_header(label="Midi Settings"):
        with dpg.group(horizontal=True): 
            dpg.add_text(label="label", default_value="Select Midi Channels: ")
            dpg.add_checkbox(label="0", callback=channel_selection, default_value=True, user_data=0)
            dpg.add_checkbox(label="1", callback=channel_selection, default_value=True, user_data=1)
            dpg.add_checkbox(label="2", callback=channel_selection, default_value=True, user_data=2)
            dpg.add_checkbox(label="3", callback=channel_selection, default_value=True, user_data=3)
            dpg.add_checkbox(label="4", callback=channel_selection, default_value=True, user_data=4)
            dpg.add_checkbox(label="5", callback=channel_selection, default_value=True, user_data=5)
            dpg.add_checkbox(label="6", callback=channel_selection, default_value=True, user_data=6)
            dpg.add_checkbox(label="7", callback=channel_selection, default_value=True, user_data=7)
            dpg.add_checkbox(label="8", callback=channel_selection, default_value=True, user_data=8)
            dpg.add_checkbox(label="9", callback=channel_selection, default_value=True, user_data=9)
            dpg.add_checkbox(label="10", callback=channel_selection, default_value=True, user_data=10)
            dpg.add_checkbox(label="11", callback=channel_selection, default_value=True, user_data=11)
            dpg.add_checkbox(label="12", callback=channel_selection, default_value=True, user_data=12)
            dpg.add_checkbox(label="13", callback=channel_selection, default_value=True, user_data=13)
            dpg.add_checkbox(label="14", callback=channel_selection, default_value=True, user_data=14)
            dpg.add_checkbox(label="15", callback=channel_selection, default_value=True, user_data=15)

    with dpg.collapsing_header(label="Suggestion Settings"):
        with dpg.group():
            #dpg.add_combo(("AAAA", "BBBB", "CCCC", "DDDD", "EEEE", "FFFF", "GGGG", "HHHH", "IIII", "JJJJ", "KKKK"), label="Scale", default_value="AAAA", callback=set_scale)
            dpg.add_slider_float(label="Window Threshold", max_value=1.0, format="threshold = %.3f", callback=set_w_threshold)
            dpg.add_slider_float(label="Total Threshold", max_value=1.0, format="threshold = %.3f", callback=set_t_threshold)

        with dpg.group(horizontal=True): 
            dpg.add_text(label="label", default_value="Select amount of notes: ")
            dpg.add_checkbox(label="5", callback=set_notecounts, default_value=True, user_data=5)
            dpg.add_checkbox(label="6", callback=set_notecounts, default_value=True, user_data=6)
            dpg.add_checkbox(label="7", callback=set_notecounts, default_value=True, user_data=7)
            dpg.add_checkbox(label="8", callback=set_notecounts, default_value=True, user_data=8)
            dpg.add_checkbox(label="9", callback=set_notecounts, default_value=True, user_data=9)
            dpg.add_checkbox(label="10", callback=set_notecounts, default_value=True, user_data=10)
            dpg.add_checkbox(label="11", callback=set_notecounts, default_value=True, user_data=11)
            dpg.add_checkbox(label="12", callback=set_notecounts, default_value=True, user_data=12)

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


dpg.create_viewport(title='Custom Title', width=1000, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
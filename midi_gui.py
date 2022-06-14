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
            sd.stop()
            self.playing = False

inputMidi = None

dpg.create_context()

def select_midi(sender, app_data, user_data):

    path = app_data['current_path']  # path to sound font file
    midi_file = app_data['file_path_name']
    print("Sender: ", sender)
    print("App Data: ", app_data)
    print("Filename: ", midi_file)

    music = PrettyMIDI(midi_file=midi_file)
    Fs = 22050
    audio_data = music.synthesize(fs=Fs)

    global inputMidi 
    inputMidi = Midi(midi_file, path)

    dpg.set_value("Text", "Playing: " + app_data['file_name'])
    dpg.set_item_label("PlayButton", "Play")
    

def play_midi(sender, app_data, user_data):
    if inputMidi is not None:
        inputMidi.play()

        if inputMidi.playing:
            dpg.set_item_label("PlayButton", "Stop")
        else:
            dpg.set_item_label("PlayButton", "Play")

        global plot_displayed
        if not plot_displayed: 
            dpg.add_line_series(x=inputMidi.audio_data, y=[-1,0,1] ,label="Test", parent="y_axis")
            plot_displayed = True

            df_copy = inputMidi.df[["time", "note", "time_duration", "time_release"]]

            # for i, x in df_copy.iterrows():
            #     rect = patches.Rectangle((x.time, x.note - 0.5), width=x.time_duration, height=1, linewidth=0.2, edgecolor=(0,0,0), facecolor=cmap(x.note))
            #     dpg.add_image_series(2, [300, 300], [400, 400], label="font atlas")

            # plt.xlim(0, df_copy.time_release.max())
            # plt.ylim(df_copy.note.min() - 3, df_copy.note.max() + 3)

def _log(sender, app_data, user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
        

def random_midi(sender, app_data, user_data):
    random_file = random.choice(midifiles)

    dpg.set_value("Text", "Playing: " + random_file)
    dpg.set_item_label("PlayButton", "Play")

    random_file = midi_path + "/" + random_file

    global inputMidi
    inputMidi = Midi(random_file, midi_path)

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
        dpg.add_text(label="Text", default_value="No file selected", tag="Text")
        dpg.add_button(label="Play", callback=play_midi, tag="PlayButton")

        with dpg.plot(label="MidiPlot", height=200, width=1000):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Freq", tag="y_axis")
            #dpg.add_line_series([], [-1,0,1], tag="LineSerie", parent="y_axis")
            #dpg.add_simple_plot(label="Midi Plot", default_value=inputMidi.audio_data, parent="MidiPlayer")

        with dpg.plot(label="Image Plot", height=200, width=-1):
            dpg.add_plot_legend()
            xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="imgx")
            yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="imgy")
            # with dpg.plot_axis(dpg.mvYAxis, label="y axis"):
            #     dpg.add_image_series(2, [300, 300], [400, 400], label="font atlas")
            #     dpg.add_image_series("__demo_static_texture_2", [150, 150], [200, 200], label="static 2")
            #     dpg.add_image_series("__demo_dynamic_texture_1", [-200, 100], [-100, 200], label="dynamic 1")
            #     dpg.fit_axis_data(dpg.top_container_stack())
            #dpg.fit_axis_data(xaxis)

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
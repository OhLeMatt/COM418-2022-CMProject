import dearpygui.dearpygui as dpg
import mido
from pretty_midi import PrettyMIDI
import sounddevice as sd
from os import listdir
from os.path import isfile, join
import random

midi_path = "MIDI_Files"

midifiles = [f for f in listdir(midi_path) if isfile(join(midi_path, f))]

plot_displayed = False

class InputMidi: 

    def __init__(self, file_name, path):
        self.file_name = file_name 
        self.path = path
        self.playing = False

        music = PrettyMIDI(midi_file=file_name)
        self.Fs = 22050
        self.audio_data = music.synthesize(fs=self.Fs)

        self.channels = [i for i in range(0,16)]


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
    #file_name = app_data['file_name']

    path = app_data['current_path']  # path to sound font file
    midi_file = app_data['file_path_name']
    #m = mido.MidiFile(filename=file_name)
    print("Sender: ", sender)
    print("App Data: ", app_data)
    print("Filename: ", midi_file)

    music = PrettyMIDI(midi_file=midi_file)
    Fs = 22050
    audio_data = music.synthesize(fs=Fs)

    global inputMidi 
    inputMidi = InputMidi(midi_file, path)

    dpg.set_value("Text", "Playing: " + app_data['file_name'])
    #dpg.set_value("MidiPlot", audio_data)
    

def play_midi(sender, app_data, user_data):
    if inputMidi is not None:
        inputMidi.play()
        if inputMidi.playing:
            dpg.set_value("PlayButton", "Pause")
        else:
            dpg.set_value("PlayButton", "Play")

        #dpg.add_simple_plot(label="Midi Plot", default_value=inputMidi.audio_data, parent="MidiPlayer")
        if not plot_displayed: 
            dpg.add_line_series(inputMidi.audio_data, [-1,0,1], label="Test", parent="y_axis")
        #dpg.set_value("LineSerie", inputMidi.audio_data)


        

def random_midi(sender, app_data, user_data):
    random_file = random.choice(midifiles)

    dpg.set_value("Text", "Playing: " + random_file)

    random_file = midi_path + "/" + random_file

    global inputMidi
    inputMidi = InputMidi(random_file, midi_path)

def channel_selection(sender, app_data, user_data):
    if inputMidi is not None:
        if app_data:
            inputMidi.add_channel(user_data)
        else: 
            inputMidi.remove_channel(user_data)

        print("channels: " + str(inputMidi.channels))


with dpg.file_dialog(directory_selector=False, show=False, callback=select_midi, id="file_dialog_id", height=300):
    dpg.add_file_extension(".mid")
    dpg.add_file_extension("", color=(150, 255, 150, 255))

with dpg.window(label="Midi Player", width=800, height=400, tag="MidiPlayer"):
    with dpg.group(horizontal=True):
        dpg.add_button(label="File Selector", callback=lambda: dpg.show_item("file_dialog_id"))
        dpg.add_button(label="Random", callback=random_midi)
    dpg.add_text(label="Text", default_value="No file selected", tag="Text")
    dpg.add_button(label="Play", callback=play_midi, tag="PlayButton")

    with dpg.plot(label="MidiPlot", height=200, width=800):
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Freq", tag="y_axis")
        #dpg.add_line_series([], [-1,0,1], tag="LineSerie", parent="y_axis")
        #dpg.add_simple_plot(label="Midi Plot", default_value=inputMidi.audio_data, parent="MidiPlayer")

    

with dpg.window(label="Menu", width=800, height=200, pos=(0,400)):
    with dpg.menu(label="Midi Channels"):
        with dpg.table(header_row=False, borders_innerH=False, 
                               borders_outerH=False, borders_innerV=False, borders_outerV=False):
                    
                    dpg.add_table_column()
                    dpg.add_table_column()
                    dpg.add_table_column()
                    dpg.add_table_column()

                    
                    with dpg.table_row():
                        dpg.add_checkbox(label="0", callback=channel_selection, default_value=True, user_data=0)
                        dpg.add_checkbox(label="1", callback=channel_selection, default_value=True, user_data=1)
                        dpg.add_checkbox(label="2", callback=channel_selection, default_value=True, user_data=2)
                        dpg.add_checkbox(label="3", callback=channel_selection, default_value=True, user_data=3)

                    with dpg.table_row(): 
                        dpg.add_checkbox(label="4", callback=channel_selection, default_value=True, user_data=4)
                        dpg.add_checkbox(label="5", callback=channel_selection, default_value=True, user_data=5)
                        dpg.add_checkbox(label="6", callback=channel_selection, default_value=True, user_data=6)
                        dpg.add_checkbox(label="7", callback=channel_selection, default_value=True, user_data=7)

                    with dpg.table_row(): 
                        dpg.add_checkbox(label="8", callback=channel_selection, default_value=True, user_data=8)
                        dpg.add_checkbox(label="9", callback=channel_selection, default_value=True, user_data=9)
                        dpg.add_checkbox(label="10", callback=channel_selection, default_value=True, user_data=10)
                        dpg.add_checkbox(label="11", callback=channel_selection, default_value=True, user_data=11)

                    with dpg.table_row(): 
                        dpg.add_checkbox(label="12", callback=channel_selection, default_value=True, user_data=12)
                        dpg.add_checkbox(label="13", callback=channel_selection, default_value=True, user_data=13)
                        dpg.add_checkbox(label="14", callback=channel_selection, default_value=True, user_data=14)
                        dpg.add_checkbox(label="15", callback=channel_selection, default_value=True, user_data=15)



dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
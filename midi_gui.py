import dearpygui.dearpygui as dpg
import mido
from pretty_midi import PrettyMIDI
import sounddevice as sd
from os import listdir
from os.path import isfile, join
import random

midi_path = "/Users/manon/Downloads/EPFL/MA4/Computers & Music/COM418-2022-CMProject/MIDI_Files"

midifiles = [f for f in listdir(midi_path) if isfile(join(midi_path, f))]


class InputMidi: 

    def __init__(self, file_name, path):
        self.file_name = file_name 
        self.path = path
        self.playing = False

        music = PrettyMIDI(midi_file=file_name)
        self.Fs = 22050
        self.audio_data = music.synthesize(fs=self.Fs)

    # def set_file(self, file_name, path):
    #     self.file_name = file_name 
    #     self.path = path
    #     self.playing = False

    #     music = PrettyMIDI(midi_file=file_name)
    #     self.Fs = 22050
    #     self.audio_data = music.synthesize(fs=self.Fs)

    def play(self):
        if not self.playing:
            sd.play(self.audio_data, self.Fs)
            self.playing = True
        else: 
            sd.stop()
            self.playing = False

#inputMidi = InputMidi("/Users/manon/Downloads/EPFL/MA4/Computers & Music/COM418-2022-CMProject/MIDI_Files/KCP_Major_1.mid","/Users/manon/Downloads/EPFL/MA4/Computers & Music/COM418-2022-CMProject/MIDI_Files")
inputMidi = None

dpg.create_context()

def callback(sender, app_data, user_data):
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
    

def play_midi(sender, app_data, user_data):
    if inputMidi is not None:
        inputMidi.play()

def random_midi(sender, app_data, user_data):
    random_file = random.choice(midifiles)

    dpg.set_value("Text", "Playing: " + random_file)

    random_file = midi_path + "/" + random_file

    global inputMidi
    inputMidi = InputMidi(random_file, midi_path)



with dpg.file_dialog(directory_selector=False, show=False, callback=callback, id="file_dialog_id", height=300):
    dpg.add_file_extension(".mid")
    dpg.add_file_extension("", color=(150, 255, 150, 255))
    # dpg.add_file_extension("Source files (*.cpp *.h *.hpp){.cpp,.h,.hpp}", color=(0, 255, 255, 255))
    # dpg.add_file_extension(".h", color=(255, 0, 255, 255), custom_text="[header]")
    # dpg.add_file_extension(".py", color=(0, 255, 0, 255), custom_text="[Python]")

with dpg.window(label="Midi Player", width=800, height=300):
    dpg.add_button(label="File Selector", callback=lambda: dpg.show_item("file_dialog_id"))
    dpg.add_button(label="Random", callback=random_midi)
    dpg.add_text(label="Text", default_value="No file selected", tag="Text")
    dpg.add_button(label="Play", callback=play_midi)

# with dpg.window(label="Menu Box", width=800, height=300):
#     list_choices = ['one', 'two', 'three', 'four']

#     dpg.add_listbox(name = "Choose", items = list_choices)
    # dpg.set_main_window_size(500,500)
    # dpg.set_core_window


dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
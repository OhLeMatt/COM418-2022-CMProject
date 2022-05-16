import dearpygui.dearpygui as dpg
import mido
from pretty_midi import PrettyMIDI
import sounddevice as sd


class InputMidi: 

    def __init__(self, file_name, path):
        self.file_name = file_name 
        self.path = path

        music = PrettyMIDI(midi_file=file_name)
        self.Fs = 22050
        self.audio_data = music.synthesize(fs=self.Fs)

    def play(self):
        sd.play(self.audio_data, self.Fs)


dpg.create_context()

def callback(sender, app_data, user_data):
    #file_name = app_data['file_name']

    path = app_data['current_path']  # path to sound font file
    midi_file = app_data['file_path_name']
    #m = mido.MidiFile(filename=file_name)
    print("Sender: ", sender)
    print("App Data: ", app_data)
    print("Filename: ", midi_file)

    # music = PrettyMIDI(midi_file=midi_file)
    # Fs = 22050
    # audio_data = music.synthesize(fs=Fs)

    inputMidi = InputMidi(midi_file, path)

    dpg.set_value("Text", "Playing: " + app_data['file_name'])
    

def play_midi(sender, app_data, user_data):




with dpg.file_dialog(directory_selector=False, show=False, callback=callback, id="file_dialog_id", height=300):
    dpg.add_file_extension(".mid")
    dpg.add_file_extension("", color=(150, 255, 150, 255))
    dpg.add_file_extension("Source files (*.cpp *.h *.hpp){.cpp,.h,.hpp}", color=(0, 255, 255, 255))
    dpg.add_file_extension(".h", color=(255, 0, 255, 255), custom_text="[header]")
    dpg.add_file_extension(".py", color=(0, 255, 0, 255), custom_text="[Python]")

with dpg.window(label="Tutorial", width=800, height=600):
    dpg.add_button(label="File Selector", callback=lambda: dpg.show_item("file_dialog_id"))
    dpg.add_text(label="Text", default_value="Hello", tag="Text")
    dpg.add_button(label="Play", callback=lambda: dpg.show_item("file_dialog_id"))

dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
# COM418-2022-CMProject - Improvisation Helper Tool

In the context of the Computers & Music (COM-418) course at EPFL, we implemented an Improvisation Helper Tool. We analyse midi files to extract corresponding scales and suggest chords or notes to play along. 

We offer the following functionalities:
* Midi file selection 
* Midi player 
* Midi visualiser
* Personalisable scale suggestions
* Parametrisable chord & note suggestions

## Run Instructions
First you need to install all of the requirements using the following command:
```
pip install -r requirements.txt
```

Then you can launch the GUI :
```
python3 ./improvisation_guidance_tool.py 
```

## Midi Player
To begin the user must select a midi file. This can either be done using the `File Selector` button or the `Random` button which selects a midi file at random from the `MIDI_Files` folder. 

The midi player allows user to play, pause or stop the midi. The user can also control the volume directly from the interface. 

## Midi Visualiser

The selected midi file will be displayed with notes along the x-axis. The y-axis can be displayed either in ticks, bartime or time (in seconds). The visualiser is colour-coded according to notes (independently of the octave). 

![colour code](images/colour_code.png)

The user can also select which of the 12 midi file channels to display.

You can see an example of the visualisation for a midi of Eleanor Rigby by the Beatles below. 

![colour code](images/midiviz_beatles.png)

## Scale Suggestion

### Parameters
The scale suggestion can be personalised under the following parameters:
* Normalize accuracy: TODO explain this
* Weighted by Beat Importance: idem
* Computation window (2 modes)
    * Bars: under this mode the suggestion will be computed over the displayed grey area on the visualiser. The user can choose the size of this window in bars. 
    * Entire window: under this mode the suggestion will be computed over the entire midi file. 
* Accuracy threshold: this threshold determines the accuracy with which the user would like the scales to be suggested (i.e. to filter out bad suggestions).
* Amount of notes: the user can select how many notes they would like the scale suggestions to have. 

### Result
The resulting suggestions are displayed under a table which shows the scale name, the accuracy of the suggestion, the amount of notes in the scale and alternate names for the scale if any. 

### Methodology

# References 
The midi files were collected from the following websites: 
* www.bitmidi.com
* www.midiworld.com
* www.feelyoursound.com
* www.mutopiaproject.org
* www.hooktheory.com

The GUI is based on the DearPyGUI library, for which we used the following ressources:
* https://dearpygui.readthedocs.io
* https://github.com/hoffstadt/DearPyGui/blob/master/DearPyGui/dearpygui/demo.py
* https://github.com/hoffstadt/DearPyGui/wiki/Dear-PyGui-Showcase#dearbagplayer

The scale and chord suggestions gained a lot from the following ressources:
* https://ianring.com/musictheory/scales/
* http://allthescales.org/index.php
* https://www.sciencedirect.com/science/article/abs/pii/S0020025518307163?via%3Dihub#fig0001

And finally the following ressources came in handy for playing around with midi files (notably the Mido and PrettyMidi libraries):
* https://mido.readthedocs.io
* https://www.twilio.com/blog/working-with-midi-data-in-python-using-mido
* https://craffel.github.io/pretty-midi/
* https://notebook.community/craffel/pretty-midi/Tutorial

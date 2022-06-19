import dearpygui.dearpygui as dpg

import music_tools.midi_utils as mu
import gui.context as gc

# VISU SETTINGS

CELL_INACTIVE_COLOR = [50, 50, 50]
TEXT_COLOR = [255, 255, 255, 200]

CHROMA_CELL_X = 70
CHROMA_CELL_Y = 120
CHROMA_TEXT_SIZE = 17
CHROMA_WIDTH = 930
CHROMA_HEIGHT = 130
CHROMA_KEY_THICKNESS = 3.0
CHROMA_ROUNDING = 5

PIANO_WHITE_KEY_X = 60
PIANO_WHITE_KEY_Y = 240
PIANO_BLACK_KEY_X = 40
PIANO_BLACK_KEY_Y = 150
PIANO_WHITE_KEYS = [0, 2, 4, 5, 7, 9, 11]        
PIANO_BLACK_KEYS = [1, 3, 6, 8, 10]
PIANO_TEXT_SIZE = 14
PIANO_WIDTH = 460
PIANO_HEIGHT = 250
PIANO_KEY_THICKNESS = 3.0
PIANO_ROUNDING = 4

GUITAR_CELL_X = 15
GUITAR_CELL_Y = 20
GUITAR_THICKNESS = 1.0

def draw_chroma_display(notes_name=[], 
                     alt_notes_name=[], 
                     spacing_factor=0.1, 
                     text_pos_factor=0.5,
                     x_factor=1.0,
                     y_factor=1.0,
                     prefix="",
                     **kwargs):
    
    with dpg.drawlist(width=int(CHROMA_WIDTH*x_factor), 
                      height=int(CHROMA_HEIGHT*y_factor), 
                      tag=prefix+"chroma_drawlist",
                      **kwargs):
        rec_width = CHROMA_CELL_X*x_factor
        rec_height = CHROMA_CELL_Y*y_factor
        text_x_pos = (CHROMA_CELL_X/2 - 10)*x_factor
        text_y_pos = (CHROMA_CELL_Y * text_pos_factor - CHROMA_TEXT_SIZE)*y_factor
        alt_text_x_pos = (CHROMA_CELL_X/2 - 10)*x_factor
        alt_text_y_pos = CHROMA_CELL_Y * text_pos_factor * y_factor
        x_spacing = CHROMA_CELL_X * (1 + spacing_factor) * x_factor
        
        thickness = CHROMA_KEY_THICKNESS * min(x_factor, y_factor)
        rounding = CHROMA_ROUNDING * min(x_factor, y_factor)
        
        draw_x = thickness * 1.1
        draw_y = thickness * 1.1
        for chroma in mu.CHROMA_IDS:
            dpg.draw_rectangle([draw_x, draw_y], 
                               [draw_x + rec_width, draw_y + rec_height], 
                               thickness=thickness, rounding=rounding, fill=CELL_INACTIVE_COLOR,
                               tag=prefix+"chroma_rect_"+str(chroma))
            if(len(notes_name) > 0):
                dpg.draw_text([draw_x + text_x_pos, draw_y + text_y_pos], 
                            notes_name[chroma], 
                            size=CHROMA_TEXT_SIZE*y_factor, color=TEXT_COLOR, 
                            tag=prefix+"chroma_text_"+str(chroma))
            
            if(len(alt_notes_name) > 0):
                dpg.draw_text([draw_x + alt_text_x_pos, draw_y + alt_text_y_pos], 
                              alt_notes_name[chroma], 
                              size=CHROMA_TEXT_SIZE*y_factor, color=TEXT_COLOR, 
                              tag=prefix+"chroma_alt_text_"+str(chroma))
            draw_x += x_spacing
        

def update_chroma_display(selected_chromas, prefix=""):
    for chroma in mu.CHROMA_IDS:    
        if chroma in selected_chromas:
            dpg.configure_item(prefix+"chroma_rect_"+str(chroma), fill=gc.get_note_colour(chroma, 0.8))
        else:
            dpg.configure_item(prefix+"chroma_rect_"+str(chroma), fill=CELL_INACTIVE_COLOR)

def draw_piano_display(notes_name=[], 
                     alt_notes_name=[], 
                     spacing_factor=0.1, 
                     text_pos_factor=0.85,
                     x_factor=0.9,
                     y_factor=0.8,
                     prefix="",
                     **kwargs):
    
    with dpg.drawlist(width=int(PIANO_WIDTH*x_factor), 
                      height=int(PIANO_HEIGHT*y_factor), 
                      tag=prefix+"piano_drawlist",
                      **kwargs):
        
        x_spacing = PIANO_WHITE_KEY_X * (1 + spacing_factor) * x_factor
        key_width = PIANO_WHITE_KEY_X * x_factor
        key_height = PIANO_WHITE_KEY_Y * y_factor
        text_x_pos = (PIANO_WHITE_KEY_X/2 - 10) * x_factor
        text_y_pos = (PIANO_WHITE_KEY_Y*text_pos_factor) * y_factor
        alt_text_x_pos = (PIANO_WHITE_KEY_X/2 - 14) * x_factor
        alt_text_y_pos = (PIANO_WHITE_KEY_Y*text_pos_factor - PIANO_TEXT_SIZE) * y_factor
        
        thickness = PIANO_KEY_THICKNESS * min(x_factor, y_factor)
        rounding = PIANO_ROUNDING * min(x_factor, y_factor)
        
        white_draw_x = thickness * 1.1
        black_draw_x = (PIANO_WHITE_KEY_X * (1 + spacing_factor/2) - PIANO_BLACK_KEY_X/2)*x_factor
        draw_y = thickness * 1.1
        
        for i, key_chroma in enumerate(PIANO_WHITE_KEYS):
            dpg.draw_rectangle([white_draw_x, draw_y], 
                               [white_draw_x + key_width, draw_y + key_height], 
                               thickness=thickness, rounding=rounding, fill=CELL_INACTIVE_COLOR,
                               tag=prefix+"piano_rect_"+str(key_chroma))
            if(len(notes_name) > 0):
                dpg.draw_text([white_draw_x + text_x_pos, draw_y + text_y_pos], 
                            notes_name[key_chroma], 
                            size=PIANO_TEXT_SIZE*y_factor, color=TEXT_COLOR, 
                            tag=prefix+"piano_text_"+str(key_chroma))
            if(len(alt_notes_name) > 0):
                dpg.draw_text([white_draw_x + alt_text_x_pos, draw_y + alt_text_y_pos], 
                              alt_notes_name[key_chroma], 
                              size=PIANO_TEXT_SIZE*y_factor, color=TEXT_COLOR, 
                              tag=prefix+"piano_alt_text_"+str(key_chroma))
            white_draw_x += x_spacing
        
        key_width = PIANO_BLACK_KEY_X*x_factor
        key_height = PIANO_BLACK_KEY_Y*y_factor
        text_x_pos = (PIANO_BLACK_KEY_X/2 - 10)*x_factor
        text_y_pos = (PIANO_BLACK_KEY_Y*text_pos_factor)*y_factor
        alt_text_x_pos = (PIANO_BLACK_KEY_X/2 - 14)*x_factor
        alt_text_y_pos = (PIANO_BLACK_KEY_Y*text_pos_factor - PIANO_TEXT_SIZE) * y_factor
        
        for i, key_chroma in enumerate(PIANO_BLACK_KEYS):
            dpg.draw_rectangle([black_draw_x, draw_y], 
                               [black_draw_x + key_width, draw_y + key_height], 
                               thickness=thickness, rounding=rounding, fill=CELL_INACTIVE_COLOR, 
                               tag=prefix+"piano_rect_"+str(key_chroma))
            if(len(notes_name) > 0):
                dpg.draw_text([black_draw_x + text_x_pos, draw_y + text_y_pos], 
                            notes_name[key_chroma], 
                            size=PIANO_TEXT_SIZE*y_factor, color=TEXT_COLOR, 
                            tag=prefix+"piano_text_"+str(key_chroma))

            if(len(alt_notes_name) > 0):
                dpg.draw_text([black_draw_x + alt_text_x_pos, draw_y + alt_text_y_pos], 
                              alt_notes_name[key_chroma], 
                              size=PIANO_TEXT_SIZE*y_factor, color=TEXT_COLOR, 
                              tag=prefix+"piano_alt_text_"+str(key_chroma))

            black_draw_x += x_spacing
            if i == 1:
                black_draw_x += x_spacing

def update_piano_display(selected_chromas, prefix=""):
    for chroma in mu.CHROMA_IDS:
        if chroma in selected_chromas:
            dpg.configure_item(prefix+"piano_rect_"+str(chroma), fill=gc.get_note_colour(chroma, 0.8))
        else:
            dpg.configure_item(prefix+"piano_rect_"+str(chroma), fill=CELL_INACTIVE_COLOR)

def draw_empty_guitar(notes_name, alt_notes_name=[], x_offset=0, y_offset=0, prefix=""):
    notes=[0, 2] #to remove
    en_chroma_scale = gc.EN_NOTES_DISPLAY #to remove
    fr_chroma_scale = gc.FR_NOTES_DISPLAY #to remove
    
    A_indices = [(1, 2), (1, 3), (1, 4)]
    B_indices = [(1, 1), (1, 5), (3, 2), (3, 3), (3, 4)]
    C_indices = [(0, 4), (1, 2), (2, 1)]
    D_indices = [(1, 3), (1, 5), (2, 4)]
    E_indices = [(0, 3), (1, 1), (1, 2)]
    F_indices = [(0, 0), (0, 4), (0, 5), (1, 3), (2, 1), (2, 2)]
    G_indices = [(1, 1), (2, 0), (2, 5)]
    with dpg.drawlist(width=1000, height=130):
        draw_x = 4
        draw_y = 4
        square_nb = 5
        # Handle multiple lines of chords
        for index in notes:
            note = en_chroma_scale[index]
            table = []
            if note == 'A':
                table = A_indices
            elif note == 'B':
                table = B_indices
            elif note == 'C':
                table = C_indices
            elif note == 'D':
                table = D_indices
            elif note == 'E':
                table = E_indices
            elif note == 'F':
                table = F_indices
            elif note == 'G':
                table = G_indices
            draw_chord(draw_x, draw_y, table)
            draw_x = draw_x + square_nb*GUITAR_CELL_X + 20

def draw_chord(draw_x, draw_y, indices):
    cur_draw_x = draw_x
    cur_draw_y = draw_y
    for i in range(5):
        for j in range(5):
            dpg.draw_rectangle([cur_draw_x, cur_draw_y], 
                               [cur_draw_x + GUITAR_CELL_X, GUITAR_CELL_Y + cur_draw_y], 
                               thickness=GUITAR_THICKNESS)
            cur_draw_x += GUITAR_CELL_X
        cur_draw_x = draw_x
        cur_draw_y += GUITAR_CELL_Y
    cur_draw_y = draw_y
    for y, x in indices:
        dpg.draw_circle(center=[cur_draw_x + x * GUITAR_CELL_X, cur_draw_y + (y + 0.5) * GUITAR_CELL_Y], 
                        radius=5, 
                        fill=[255, 255, 255])
        
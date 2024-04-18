import numpy as np
import pygame
from wsr import WSR, Dirs, Axis
from misc import *
from gui_style import Colors, Style
import pickle
import os

######## CONFIG ########

window_size = (1280, 720)
# its better for it to be higher than your monitor refresh rate because vsync is not working properly with resizable window in pygame and there would be stuttering
fps_limit = 240

# inclusive range of keys on the left side of the screen in octaves
#rendered_octaves = (1, 6)
rendered_octaves = (0, 6)

pitch_file = "test2_pitch_curve.pkl"

########################

cwd = os.path.dirname(os.path.realpath(__file__))

# load pitch curve
try:
    with open(os.path.join(cwd, "extracted_pitch", pitch_file), "rb") as f:
        pitch_curve, confidence_curve, audio_len, bpm, sample_rate = pickle.load(f)
except FileNotFoundError:
    print(f"Could not find {pitch_file} inside extracted_pitch folder!")
    exit()



print("========================")
print(f"pitch curve len: {len(pitch_curve)}")
print(f"original audio len: {audio_len}")
print(f"bpm: {bpm}")
print(f"sample rate: {sample_rate}")
print("========================")

# duration of original audio in bars
#bars_duration = audio_len / sample_rate * bpm / 240
#print(f"bars duration: {bars_duration}")
step_duration = audio_len / sample_rate * bpm / 15
print(f"step duration: {step_duration}")
print("========================")


# DEBUG create pitch curve with lenght of original pitch curve with values 16.35
#pitch_curve = np.full_like(pitch_curve, 65.41)

pitch_curve = -12 * np.log2(pitch_curve / 440) - 57.5



pygame.init()
window = pygame.display.set_mode(window_size, pygame.RESIZABLE)
clock = pygame.time.Clock()

wsr = WSR(
    window,
    init_view_pos=(0, window_size[1]),
    init_view_zoom=(25, 50),
    debug=False
)


# Z index
# 3 - black keys
# 2 - white keys
# 1 - reference curve
# 0 - grid lines
# -1 - black keys grid





## create keys
# create one big white rectangle for all white keys
#wsr.add_rect(
#    Colors.white_notes,
#    (0, rendered_octaves[0] * 12),
#    (Style.white_note_width, -(rendered_octaves[1] - rendered_octaves[0] + 1) * 12),
#    z_index=1,
#    stick=Dirs.left,
#    screen_space_lock_axis=Axis.x
#)

# convert inclusive range to exclusive at the end
rendered_octaves = (rendered_octaves[0], rendered_octaves[1] + 1)

# white keys
wsr.add_rect_corners(
    Colors.white_notes,
    (0, -rendered_octaves[1] * 12),
    (Style.white_note_width, rendered_octaves[0] * 12),
    z_index=2,
    stick=Dirs.left,
    screen_space_lock_axis=Axis.x
)


#for i in range(rendered_octaves[0] * 12, (rendered_octaves[1] + 1)  * 12):
#
#    if is_note_black(i):
#        temp_color = Colors.black_notes
#        temp_height = 1
#    else:
#        temp_color = Colors.white_notes
#        temp_height = 2
#
#    wsr.add_rect((0, 0, 0), np.array([i, 0]), np.array([1, 1]), z_index=-1)
#    wsr.add_rect((255, 255, 255), np.array([i, 0]), np.array([1, 2]), z_index=-1)

# temp value. will be calculated automatically based on track length
#track_width = 100

rendered_notes = (rendered_octaves[0] * 12, rendered_octaves[1] * 12)

# add notes, grid, grid lines
for i in range(rendered_notes[0], rendered_notes[1] + 1):
    if is_note_black(i):
        # black keys
        wsr.add_rect(
            Colors.black_notes,
            (0, -i),
            (Style.black_note_width, -1),
            z_index=3,
            stick=Dirs.left,
            screen_space_lock_axis=Axis.x
        )

        # black keys grid
        wsr.add_rect(
            Colors.grid_black_notes,
            (0, -i),
            (step_duration, -1),
            z_index=-1
        )

        #print((Style.white_note_width, -i))

    # grid lines
    wsr.add_line_delta(
        Colors.grid_lines,
        (0, -i),
        (step_duration, 0),
        z_index=0
    )


# add bar, beat, step lines
for i in range(0, int(step_duration) + 1):
    # bar line
    if i % 16 == 0:
        wsr.add_line(
            Colors.bar_line,            
            (i, -rendered_notes[0]),
            (i, -rendered_notes[1]),
            z_index=0,
            thick=2
        )   

    # beat line
    elif i % 4 == 0:
        wsr.add_line(
            Colors.beat_line,
            (i, -rendered_notes[0]),
            (i, -rendered_notes[1]),
            z_index=0
        )

    # step line
    else:
        wsr.add_line(
            Colors.step_line,
            (i, -rendered_notes[0]),
            (i, -rendered_notes[1]),
            z_index=0
        )


# reference curve
wsr.add_curve(
    Colors.reference_curve,
    pitch_curve,
    width = step_duration,
    y_color_coeff = confidence_curve,
    color_secondary = Colors.reference_curve_sec,
    thick=3,
    z_index=1
)




while True:
    scroll_rel = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        if event.type == pygame.MOUSEWHEEL:
            scroll_rel = event.y


    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()

    mouse_pos = np.array(pygame.mouse.get_pos(), dtype=np.float32)
    mouse_rel = np.array(pygame.mouse.get_rel(), dtype=np.float32)


    # y zoom
    if keys[pygame.K_LCTRL] and mouse_buttons[1]:
        wsr.zoom_view(1 - mouse_rel[1] / 100, mouse_pos, Axis.y)
    
    # 2D movement
    elif mouse_buttons[1]:
        wsr.move_view_screen_space(mouse_rel)

    elif keys[pygame.K_LCTRL] and scroll_rel:
        wsr.zoom_view(1 + scroll_rel / 5, mouse_pos, axis=Axis.x)


    window.fill(Colors.background)

    wsr.render()

    pygame.display.update()
    clock.tick(fps_limit)
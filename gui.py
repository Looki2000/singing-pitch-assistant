import numpy as np
import pygame
from wsr import WSR, Dirs, Axis
from misc import *
from gui_style import Colors, Style
import pickle
import os
import threading
import time
from pynput.keyboard import Key, Listener
import pyaudio
import librosa


######## CONFIG ########

window_size = (1280, 720)
# its better for it to be higher than your monitor refresh rate because vsync is not working properly with resizable window in pygame and there would be stuttering
fps_limit = 90

# inclusive range of keys on the left side of the screen in octaves
#rendered_octaves = (1, 6)
rendered_octaves = (2, 5)

pitch_file = "test_pitch_curve.pkl"

coeff_tresh = 0.5

rec_sample_rate = 48000
rec_buffer_size = 1024 * 2
max_detect_deviations = 10

pitch_file_hop_length = int(rec_sample_rate / 200.)


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


init_zoom = (25, 50)

wsr = WSR(
    window,
    init_view_pos=(0, window_size[1] + rendered_octaves[0] * 12 * init_zoom[1]),
    init_view_zoom=init_zoom,
    debug=False
)


# Z index
# 11 - black keys
# 10 - white keys
# 5 - play head
# 3 - detected line
# 2 - detected curve
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
#wsr.add_rect_corners(
#    Colors.white_notes,
#    (0, -rendered_octaves[1] * 12),
#    (Style.white_note_width, rendered_octaves[0] * 12),
#    z_index=2,
#    stick=Dirs.left,
#    screen_space_lock_axis=Axis.x
#)

wsr.add_rect_corners(
    Colors.white_notes,
    (0, -rendered_octaves[1] * 12),
    (Style.white_note_width, -rendered_octaves[0] * 12),
    z_index=10,
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
            z_index=11,
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
    coeff_tresh = coeff_tresh,
    #color_secondary = Colors.reference_curve_sec,
    thick=3,
    z_index=1
)


# play head
init_play_head_pos = 0
play_head_pos = init_play_head_pos
play_head = wsr.add_line(
    Colors.play_head,
    (init_play_head_pos, -rendered_notes[0]),
    (init_play_head_pos, -rendered_notes[1]),
    thick=3,
    z_index=5
)



## detected curve
#detected_curve_obj = wsr.add_curve(
#    Colors.detected_curve,
#    np.zeros_like(pitch_curve),
#    width = step_duration,
#    thick=3,
#    z_index=2
#)
# detected curve
detected_curve_obj = wsr.add_curve(
    Colors.detected_curve,
    np.zeros_like(pitch_curve),
    width = step_duration,
    y_color_coeff = np.ones_like(pitch_curve),
    coeff_tresh = 0.5,
    thick=3,
    z_index=2
)

# detected line
detected_line_obj = wsr.add_line(
    Colors.detected_line,
    (0, 0),
    (step_duration, 0),
    thick=3,
    z_index=3
)



def set_play_head(pos):
    play_head[1][1][0] = pos
    play_head[1][2][0] = pos


def choices_menu(choices):
    while True:
        # "=" multiplied by len of longest choice
        separator = (len(max(choices, key=len)) + 3) * "="
        print("\n" + separator)
        for i, choice in enumerate(choices):
            print(f"{i + 1}. {choice}")
        print(separator)

        choice = input(" > ")

        bad = False

        try:
            choice = int(choice)
        except ValueError:
            bad = True

        if choice < 1 or choice > len(choices) or bad:
            print(f"\nInput must be a number between 1 and {len(choices)}!")
            continue

        return choice - 1

def num_input(prompt, min_val=None, max_val=None, is_float=False):
    while True:
        num = input("\n" + prompt)

        bad = False

        try:
            num = float(num) if is_float else int(num)
        except ValueError:
            bad = True

        if min_val is not None and num < min_val:
            bad = True
        elif max_val is not None and num > max_val:
            bad = True

        if bad:
            print(f"\nInput must be a number between {min_val} and {max_val}!")
            continue

        return num


bars_to_record = 4

def cli():
    global init_play_head_pos, bars_to_record

    while True:

        choices = (
            f"Set initial play head position ({init_play_head_pos + 1})",
            f"Set amount of bars to record ({bars_to_record})",
        )

        choice = choices_menu(choices)

        if choice == 0:
            init_play_head_pos = num_input(" position in bars > ", min_val=1, is_float=True) - 1
            play_head_pos = init_play_head_pos
            set_play_head(init_play_head_pos * 16)
        elif choice == 1:
            bars_to_record = num_input(" amount of bars > ", min_val=1)


cli_thread = threading.Thread(target=cli, daemon=True)
cli_thread.start()


# calculate curve scale that will allow to convert bars to curve index
curve_scale = len(pitch_curve) / step_duration * 16


recording = False

space_pressed = False
def space_press(key):
    global space_pressed
    if key == Key.space:
        space_pressed = True

listener = Listener(on_press=space_press)
listener.start()



# init pyaudio
p = pyaudio.PyAudio()

# open stream
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=rec_sample_rate,
    input=True,
    frames_per_buffer=rec_buffer_size
)


fmin = librosa.note_to_hz("C1")
fmax = librosa.note_to_hz("C7")
def recording_thread_func():
    global pitch_detect_values
    
    while True:
        if not_recording_detect == False and not recording:
            time.sleep(0.01)
            continue

        #print("recording")
        data = stream.read(rec_buffer_size)

        # convert to numpy array
        data = np.frombuffer(data, dtype=np.int16)

        # convert to float
        data = data.astype(np.float32) / 32768
        
        # if recording add to recorded_audio
        if recording:
            recorded_audio.extend(data.tolist())
        
        #print("detecting pitch")
        # low quality pitch detection
        f0 = librosa.yin(
            data,
            frame_length=rec_buffer_size,
            sr=rec_sample_rate,
            fmin=fmin,
            fmax=fmax
        )

        # cut the first value off
        f0 = f0[1:]
        
        #f0_before = f0.copy()
        #
        ### remove outliers
        #mean = np.mean(f0)
        #standard_deviation = np.std(f0)
        #distance_from_mean = abs(f0 - mean)
        #not_outlier = distance_from_mean < max_detect_deviations * standard_deviation
        #f0 = f0[not_outlier]
        #
        #print(f0_before, f0)

        pitch_detect_values = pitch_detect_values + f0.tolist()


not_recording_detect = True

pitch_detect_values = []

rec_thread = threading.Thread(target=recording_thread_func, daemon=True)
rec_thread.start()


def refine_and_set_pitch_curve():
    audio = np.array(recorded_audio, dtype=np.float32)
    
    offset = init_play_head_pos * curve_scale
    
    #print(audio.shape)
    
    #print(f"audio len seconds: {len(audio) / rec_sample_rate}")
    
    scale = 8
    
    # high quality pitch detection on recorded_audio
    f0, voiced_flag, voiced_probs = librosa.pyin(
        audio,
        hop_length=pitch_file_hop_length*scale,
        sr=rec_sample_rate,
        fmin=fmin,
        fmax=fmax,
    )
    
    #print(len(f0))
    #print(len(detected_curve_obj[1][1]))
    
    no_nan_mask = ~np.isnan(f0)
    final_f0 = np.zeros_like(f0)
    final_f0[no_nan_mask] = -12 * np.log2(f0[no_nan_mask] / 440) - 57.5
    
    # interpolate by scale
    final_f0 = np.repeat(final_f0, scale)
    
    
    no_nan_mask = np.repeat(no_nan_mask, scale)
    final_no_nan_mask = np.zeros_like(detected_curve_obj[1][3])
    final_no_nan_mask[int(offset):int(offset + len(no_nan_mask))] = no_nan_mask
    
    
    
    
    detected_curve_obj[1][1][int(offset):int(offset + len(final_f0))] = final_f0
    detected_curve_obj[1][3] = final_no_nan_mask


last_detected_pitch = 1


refresh_needed = False

while True:
    scroll_rel = 0


    if recording:
        # move play head based on bpm
        play_head_pos = (time.perf_counter() - rec_start) / 240 * bpm + init_play_head_pos


    if len(pitch_detect_values) == 0:
        detected_pitch = last_detected_pitch
        #print("No pitch detected!")
    else:
        detected_pitch = np.mean(pitch_detect_values)
        pitch_detect_values = []
        #print(f"Detected pitch: {detected_pitch}")

        last_detected_pitch = detected_pitch

    detected_pitch = -12 * np.log2(detected_pitch / 440) - 57.5


    if recording:
        #print("recording")
        detected_curve_obj[1][1][int(old_play_head_pos * curve_scale):int(play_head_pos * curve_scale)] = detected_pitch


        set_play_head(play_head_pos * 16)

        if play_head_pos >= bars_to_record + init_play_head_pos:
            #print("recording done")
            recording = False
            space_pressed = False
            play_head_pos = init_play_head_pos
            set_play_head(init_play_head_pos * 16)
            
            # refine pitch
            refine_thread = threading.Thread(target=refine_and_set_pitch_curve, daemon=True)
            refine_thread.start()
            
            # unhide detected line
            detected_line_obj[5] = False

        refresh_needed = True

    elif not_recording_detect:
        # set line y position to detected pitch
        detected_line_obj[1][1][1] = detected_pitch
        detected_line_obj[1][2][1] = detected_pitch

        refresh_needed = True


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        if event.type == pygame.MOUSEWHEEL:
            scroll_rel = event.y

        elif event.type == pygame.KEYDOWN:
            # switch not_recording_detect
            if event.key == pygame.K_p:
                not_recording_detect = not not_recording_detect

        ## space key
        #elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and not recording:
        #    recording = True
        #    detected_curve_obj[1][1] = np.zeros_like(pitch_curve)
        #    rec_start = time.perf_counter()
    if space_pressed and not recording:
        recording = True
        recorded_audio = []

        # hide detected line
        detected_line_obj[5] = True

        detected_curve_obj[1][1] = np.zeros_like(pitch_curve)
        detected_curve_obj[1][3] = np.ones_like(pitch_curve)
        rec_start = time.perf_counter()

        refresh_needed = True


    if recording:
        old_play_head_pos = play_head_pos



    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()

    mouse_pos = np.array(pygame.mouse.get_pos(), dtype=np.float32)
    mouse_rel = np.array(pygame.mouse.get_rel(), dtype=np.float32)


    # y zoom
    if keys[pygame.K_LCTRL] and mouse_buttons[1]:
        wsr.zoom_view(1 - mouse_rel[1] / 100, mouse_pos, Axis.y)

        refresh_needed = True
    
    # 2D movement
    elif mouse_buttons[1]:
        wsr.move_view_screen_space(mouse_rel)

        refresh_needed = True

    elif keys[pygame.K_LCTRL] and scroll_rel:
        wsr.zoom_view(1 + scroll_rel / 5, mouse_pos, axis=Axis.x)

        refresh_needed = True


    if refresh_needed:
        window.fill(Colors.background)

        wsr.render()

        pygame.display.update()

        refresh_needed = False

        #print("refreshed")

    clock.tick(fps_limit)
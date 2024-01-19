import time
from multiprocessing import shared_memory

import PySimpleGUI as sg
import numpy
import soundfile as sf
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame

import algorithms

# ----------------------
# CONSTANTS
# ----------------------
VOLUME = 20                # Volume to use when playing the music (in %)
FILE_NAME = 'takeastepback.mp3'    # Path to the file used
SLEEP_TIME = 2.0            # Head start given to processing threads (in seconds)
THREAD_COUNT = 1            # of threads to use for processing
FULLSCREEN = True          # Whether the window should be fullscreen or not
ALGO_NUM = 2                # ID of the algorithm to use (1 through 1)
# ----------------------


FLASH_SCREEN = False

if __name__ == '__main__':
    pygame.mixer.init()
    pygame.mixer.music.load(FILE_NAME)
    pygame.mixer.music.set_volume(VOLUME)

    data: numpy.ndarray
    data, samplerate = sf.read(FILE_NAME, always_2d=True)

    # [0,...,0] n/1024 times, where n is number of sample pairs
    shared_buf_result = shared_memory.SharedMemory(create=True, size=data.shape[0] // 1024)
    algorithms.start_algorithm(data, samplerate, shared_buf_result, ALGO_NUM, THREAD_COUNT)

    # time.sleep(SLEEP_TIME)

    layout = [[sg.Frame('', [[]], background_color='#000000', key='fr0', size=(500, 500), pad=(0, 0), border_width=0)]]

    window = sg.Window(title="Boombox", layout=layout, no_titlebar=True, return_keyboard_events=True,
                       margins=(0, 0)).Finalize()
    window.bind("<Escape>", "-ESCAPE-")
    if FULLSCREEN:
        window.maximize()
    window.TKroot['cursor'] = 'none'  # hide cursor
    window.bring_to_front()  # re-focus on window

    # Window now in fullscreen, get size and adjust frame size accordingly
    window_size = window.size
    window['fr0'].Widget.config(width=window_size[0], height=window_size[1])

    pygame.mixer.music.play(-1)
    time_per_val = (1024/samplerate) * 1000  # in ms

    while True:

        try:

            # TODO set ms timeout based on sample rate from soundfile (1 refresh per sample?)
            event, vals = window.read(timeout=10)
            if event in (sg.WIN_CLOSED, "-ESCAPE-"):
                window.close()
                break

            idx = int(pygame.mixer.music.get_pos() // time_per_val)

            if shared_buf_result.buf[idx] == 1:
                window['fr0'].Widget.config(background='#ffffff')
            else:
                window['fr0'].Widget.config(background='#000000')

        except:
            pygame.mixer.music.play(-1)
            idx = int(pygame.mixer.music.get_pos() // time_per_val)
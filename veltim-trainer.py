#! /usr/bin/python3

# This program is (C) 2021 by folkert@vanheusden.com.
# License: GPL v3.0

import pygame
import pygame.midi
import random
import sys
import threading
import time

from enum import Enum
from os.path import expanduser

pygame.init()

pygame.fastevent.init()

pygame.midi.init()
midi_in = pygame.midi.Input(pygame.midi.get_default_input_id())

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
RED   = (255,  40,  40)
GREEN = ( 40, 255,  40)
BLUE  = ( 40,  40, 255)

line_width = 2

bar_size = 4

screen_info = pygame.display.Info()
size = [screen_info.current_w, screen_info.current_h]

screen = pygame.display.set_mode(size)  # FIXME, pygame.FULLSCREEN)

qx = size[0] // 4
qy = size[1] // 4
dx = size[0] // 2 // bar_size
dy = size[1] // 2 // 5

pygame.display.set_caption('Tap-trainer')

count_ok = count_fail = 0

font_small = pygame.font.Font(pygame.font.get_default_font(), 16)
font_big = pygame.font.Font(pygame.font.get_default_font(), dy)

def draw_screen(velocities, intervals):
    screen.fill(BLACK)

    text_surface = font_small.render('vel-trainer, (C) 2021 by folkert@vanheusden.com', True, WHITE)
    screen.blit(text_surface, dest=(0, 0))

    info = "press 'q' to exit"

    mul = size[0] / 100.0

    pygame.draw.line(screen, RED, [0, 50 + 127], [size[0], 50 + 127], 1)
    pygame.draw.line(screen, GREEN, [0, 50], [size[0], 50], 1)

    pygame.draw.line(screen, GREEN, [0, 400], [size[0], 400], 1)

    for i in range(0, 100):
        if i < 99:
            next_v = velocities[i + 1]
            next_i = intervals[i + 1]

        else:
            next_v = velocities[i]
            next_i = intervals[i]

        pygame.draw.line(screen, WHITE, [i * mul, 50 + 127 - velocities[i]], [(i + 1) * mul, 50 + 127 - next_v], line_width)

        if intervals[i] < 2.0 and next_i < 2.0:
            pygame.draw.line(screen, WHITE, [i * mul, 400 - intervals[i] * 100], [(i + 1) * mul, 400 - next_i * 100], line_width)
 
    pygame.display.flip()

def midi_poller():
    global midi_in

    while True:
        # really need blocking functions here
        while not midi_in.poll():
            time.sleep(0.001)

        midi_events = midi_in.read(100)

        midi_evs = pygame.midi.midis2events(midi_events, midi_in.device_id)

        for m_e in midi_evs:
            pygame.fastevent.post(m_e)

th = threading.Thread(target=midi_poller)
th.start()

pos = 0

prev_ts = None

velocities = [ 0 ] * 100
interval = [ 0 ] * 100

draw_screen(velocities, interval)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit(0)

        if event.type == pygame.midi.MIDIIN:
            cmd = event.status & 0xf0
            channel = event.status & 0x0f
            note = event.data1
            velocity = event.data2

            if cmd == 0x90 and channel != 9 and velocity > 0:  # note-on, no percussion
                now = time.time()

                while len(velocities) >= 100:
                    del velocities[0]
                    del interval[0]

                velocities.append(velocity)

                if prev_ts == None:
                    prev_ts = now

                interval.append(now - prev_ts)
                prev_ts = now

                draw_screen(velocities, interval)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                sys.exit(0)

pygame.quit()

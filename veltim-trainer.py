#! /usr/bin/python3

# This program is (C) 2021 by folkert@vanheusden.com.
# License: GPL v3.0

import pygame
import pygame.midi
import threading
import time

# configurable parameters
line_width = 2

max_interval = 2.0

n_points = 100
###

pygame.init()

pygame.fastevent.init()

pygame.midi.init()
midi_in = pygame.midi.Input(pygame.midi.get_default_input_id())

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
RED   = (255,  40,  40)
GREEN = ( 40, 255,  40)
BLUE  = ( 40,  40, 255)

screen_info = pygame.display.Info()
size = [screen_info.current_w, screen_info.current_h]

screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

pygame.display.set_caption('veltim-trainer')

font_small = pygame.font.Font(pygame.font.get_default_font(), 16)

def draw_screen(velocities, intervals):
    screen.fill(BLACK)

    text_surface = font_small.render('veltim-trainer, (C) 2021 by folkert@vanheusden.com', True, WHITE)
    screen.blit(text_surface, dest=(0, 0))

    info = "press 'q' to exit"

    mul = size[0] / n_points

    pygame.draw.line(screen, RED, [0, 50 + 127], [size[0], 50 + 127], 1)
    pygame.draw.line(screen, GREEN, [0, 50], [size[0], 50], 1)

    pygame.draw.line(screen, GREEN, [0, 400], [size[0], 400], 1)

    median_v = []
    median_i = []
    for i in range(0, n_points):
        if not velocities[i] is None:
            median_v.append(velocities[i])
            median_i.append(intervals[i])

    if len(median_v) > 0:
        median_v = sorted(median_v)
        median_i = sorted(median_i)

        m_v = median_v[len(median_v) // 2]
        m_i = median_i[len(median_i) // 2]

        pygame.draw.line(screen, BLUE, [0, 50 + 127 - m_v], [size[0], 50 + 127 - m_v], 1)

        if m_i < max_interval:
            pygame.draw.line(screen, BLUE, [0, 400 - m_i * 100], [size[0], 400 - m_i * 100], 1)

    for i in range(0, n_points):
        val_v = velocities[i] if not velocities[i] is None else 127
        val_i = intervals[i] if not intervals[i] is None else max_interval

        if i < 99:
            next_v = velocities[i + 1]
            next_i = intervals[i + 1]

        else:
            next_v = velocities[i]
            next_i = intervals[i]

        next_v = next_v if not next_v is None else 127
        next_i = next_i if not next_i is None else max_interval

        pygame.draw.line(screen, WHITE, [i * mul, 50 + 127 - val_v], [(i + 1) * mul, 50 + 127 - next_v], line_width)

        if val_i < max_interval and next_i < max_interval:
            pygame.draw.line(screen, WHITE, [i * mul, 400 - val_i * 100], [(i + 1) * mul, 400 - next_i * 100], line_width)

        elif not intervals[i] is None:
            pygame.draw.line(screen, BLUE, [(i + 1) * mul, 50 + 127], [(i + 1) * mul, 50], 1)

    text_surface = font_small.render('velocity', True, WHITE)
    screen.blit(text_surface, dest=(0, 50 + 127 + 8))

    text_surface = font_small.render('interval', True, WHITE)
    screen.blit(text_surface, dest=(0, 408))

    pygame.display.flip()

running = True

def midi_poller():
    global midi_in
    global running

    while running:
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

velocities = [ None ] * n_points
interval = [ None ] * n_points

draw_screen(velocities, interval)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

        if event.type == pygame.midi.MIDIIN:
            cmd = event.status & 0xf0
            channel = event.status & 0x0f
            note = event.data1
            velocity = event.data2

            if cmd == 0x90 and channel != 9 and velocity > 0:  # note-on, no percussion
                now = time.time()

                while len(velocities) >= n_points:
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
                running = False
                break

pygame.quit()

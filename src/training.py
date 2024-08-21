import datetime
import sys
from random import random
from threading import Thread
from time import sleep
import traceback

import tensorflow as tf
from agent import DQNAgent
from environment import Environment
from mouse_manager import MouseManager
from osu.manager import OsuManager
import helper
from scheduler import LinearSchedule


def main(osu_manager: OsuManager, mouse_manager: MouseManager):
    MAP_COUNT = 20
    
    WIDTH = osu_manager.Window.width
    HEIGHT = osu_manager.Window.height
    INITIAL_SCREEN = (WIDTH, HEIGHT)
    DOWNSCALE_MULTIPLIER = 5
    STAR_RATING = 2
    
    
    _, _, _, img = osu_manager.Window.GrabPlayground(DOWNSCALE_MULTIPLIER)
    DOWNSCALED_HEIGHT, DOWNSCALED_WIDTH, DOWNSCALED_DEPTH = img.shape
    SCREEN_INPUT_SHAPE = (DOWNSCALED_HEIGHT, DOWNSCALED_WIDTH, DOWNSCALED_DEPTH)
    
    env = Environment(mouse_manager, osu_manager, INITIAL_SCREEN, DOWNSCALE_MULTIPLIER, SCREEN_INPUT_SHAPE)
    
    BATCH_SIZE = 32
    MAX_MEMORY_SIZE = 100000
    ACTION_SHAPE = 4
    CONTROL_SHAPE = DOWNSCALED_HEIGHT * DOWNSCALED_WIDTH * ACTION_SHAPE
    MIN_EXPERIENCE = 24000
    TARGET_UPDATE = 30000
    GAMMA = 0.999
    LEARNING_RATE = 5e-4
    
    agent = DQNAgent(BATCH_SIZE, MAX_MEMORY_SIZE, SCREEN_INPUT_SHAPE, ACTION_SHAPE,\
                     CONTROL_SHAPE, MIN_EXPERIENCE, GAMMA, LEARNING_RATE)
    SCHEDULE_TIMESTAMP = 4000000
    INITIAL_P = 1.0
    FINAL_P = 0.05
    scheduler = LinearSchedule(SCHEDULE_TIMESTAMP, INITIAL_P, FINAL_P)
    
    helper.move_to_songs()
    sleep(0.5)
    
    controls_state, state = env.reset()
    agent.dqn.model([tf.expand_dims(state, axis=0), tf.expand_dims(controls_state, axis=0)])
    
    i = 0
    for mc in range(MAP_COUNT):
        helper.find_maps(STAR_RATING)
        sleep(1)
        helper.reset_mods()
        sleep(0.5)
        helper.enable_mods()
        sleep(0.5)
        helper.launch_random_beatmap()
        
        controls_state, state = env.reset()
        learning_thread = None
        while osu_manager.Memory.GetInGameState().name == "PLAYING":
            i += 1
            action = None
            if i > MIN_EXPERIENCE:
                sample = random()
                if sample > scheduler.value(i):
                    action = agent.select_action(state, controls_state)
                else:
                    action = agent.random_action(DOWNSCALED_WIDTH, DOWNSCALED_HEIGHT)
            else:
                action = agent.random_action(DOWNSCALED_WIDTH, DOWNSCALED_HEIGHT)
                    
            new_state, new_controls_state, reward = env.step(action)
            agent.replay_buffer.push(state, action, reward, new_state, controls_state, new_controls_state)    
        
            if learning_thread is not None:
                learning_thread.join()
            learning_thread = Thread(target=agent.learn)
            learning_thread.start()
            
            state = new_state
            controls_state = new_controls_state

        if i % TARGET_UPDATE == 0:
            agent.dqn_target.optimizer.set_weights(agent.dqn.optimizer.get_weights())
            agent.dqn_target.model.set_weights(agent.dqn.model.get_weights())
            
        if mc % 10 == 0 and mc > 0:
            agent.save()
        
        helper.return_to_beatmaps()
    agent.save()

if __name__ == "__main__":
    osu_manager = None
    env = None
    
    try:
        osu_manager = OsuManager()
        mouse_manager = MouseManager()
        main(osu_manager, mouse_manager)
        
    except Exception:
        print(traceback.format_exc)    
        
    finally:
        del osu_manager
        del env
        sys.exit(0)
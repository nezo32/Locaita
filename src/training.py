from time import sleep
from agent import DQNAgent
from environment import Environment
from mouse_manager import MouseManager
from osu.manager import OsuManager
import helper

MAP_COUNT = 2

def main(osu_manager: OsuManager, mouse_manager: MouseManager):
    WIDTH = osu_manager.Window.width
    HEIGHT = osu_manager.Window.height
    INITIAL_SCREEN = (WIDTH, HEIGHT)
    DOWNSCALE_MULTIPLIER = 5
    STACK_SIZE = 4
    STAR_RATING = 2
    
    
    _, _, _, img = osu_manager.Window.GrabPlayground(DOWNSCALE_MULTIPLIER)
    h, w, d = img.shape
    SCREEN_INPUT_SHAPE = (h, w, d)
    
    env = Environment(mouse_manager, osu_manager, INITIAL_SCREEN, DOWNSCALE_MULTIPLIER, SCREEN_INPUT_SHAPE, STACK_SIZE)
    
    BATCH_SIZE = 32
    MAX_MEMORY_SIZE = 100000
    CONTROL_SHAPE = h * w * 4
    MIN_EXPERIENCE = 24000
    GAMMA = 0.999
    LEARNING_RATE = 5e-4
    LOAD_MODEL = False
    
    agent = DQNAgent(BATCH_SIZE, MAX_MEMORY_SIZE, SCREEN_INPUT_SHAPE, \
                     CONTROL_SHAPE, MIN_EXPERIENCE, GAMMA, LEARNING_RATE, LOAD_MODEL)
    
    helper.move_to_songs()
    sleep(0.5)
    for i in range(MAP_COUNT):
        helper.find_maps(STAR_RATING)
        helper.reset_mods()
        helper.enable_mods()
        helper.launch_random_beatmap()
        
        controls_state, state = env.reset()
        while osu_manager.Memory.GetInGameState().name == "PLAYING":
            action = agent.random_action(w, h)
            control = env.perform_action(action)
        
        sleep(3)    
        helper.return_to_beatmaps()
        
    

if __name__ == "__main__":
    osu_manager = None
    env = None
    try:
        osu_manager = OsuManager()
        mouse_manager = MouseManager()
        main(osu_manager, mouse_manager)
    finally:
        del osu_manager
        del env
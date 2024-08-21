import numpy as np
import pyautogui
import tensorflow as tf
from mouse_manager import MouseManager
from osu.manager import OsuManager

class Environment():
    def __init__(self, mouse_manager: MouseManager, osu_manager: OsuManager,\
        initial_screen: tuple[int, int], downscale_multiplier: int, screen_input_shape: tuple[int, int, int]
        ):
        self.mouse_manager = mouse_manager
        self.osu_manager = osu_manager
        
        self.initial_screen = initial_screen
        self.downscale_multiplier = downscale_multiplier
        self.screen_input_shape = screen_input_shape
        
        self.previous_accuracy = 100.0
        self.previous_score = 0
    
    
    def reset(self):
        x, y = pyautogui.center((0, 0, 1920, 1080))
        self.mouse_manager.MouseMove(x, y, 0)
        self.mouse_manager.Reset()
        self.previous_accuracy = 100.0
        
        _, _, _, state = self.osu_manager.Window.GrabPlayground(self.downscale_multiplier)
        
        return tf.convert_to_tensor([0.5, 0.5, 0.0, 0.0]), tf.convert_to_tensor(state)
    
    def step(self, action):
        new_controls_state = self.perform_action(action)
        
        hits = self.osu_manager.Memory.GetHitsData()
        
        reward = self.calculate_reward(hits['accuracy'], hits['score'])
        
        self.previous_accuracy = hits['accuracy']
        self.previous_score = hits['score']
        
        _, _, _, state = self.osu_manager.Window.GrabPlayground(self.downscale_multiplier)

        return tf.convert_to_tensor(state), new_controls_state, reward
    
    def perform_action(self, action):
        height, width, _ = self.screen_input_shape
        
        click, xy = divmod(action.numpy()[0], height * width)
        y, x = divmod(xy, width)
        
        dx = x * self.downscale_multiplier + 311
        dy = y * self.downscale_multiplier + 32
        
        self.mouse_manager.MouseClick(click)
        self.mouse_manager.MouseMove(dx, dy)
        
        left, right = self.mouse_manager.GetButtonsState()
        height, width = self.initial_screen
        
        return tf.convert_to_tensor([left, right, dx / width, dy / height])
    
    def calculate_reward(self, accuracy: float, score: int):
        # TODO: RETHINK REWARD FUNCTION
        """ reward = np.clip(-np.exp(self.previous_accuracy - accuracy) + 1.5, -0.7, 0.7)
        
        combo_coefficient = 1.5
        if current_combo - max_combo < 0:
            combo_coefficient = np.log10(np.clip(1 / -(current_combo - max_combo), 0.02, 0.999))
        reward += 0.2 * combo_coefficient
        
        reward = np.clip(reward, -1, 1, dtype=np.float32)
          
        return tf.convert_to_tensor([reward]) """
        
        # I'm so bad so just copypasted this shit
        
        if accuracy > self.previous_accuracy:    # ToDo: CLip it in [-1, 1] as well as TD-error in the optimization func, not here
            bonus = 3
        elif accuracy < self.previous_accuracy:
            bonus = -0.3
        else:
            bonus = 0.1
        
        score_coef = 0.1 * np.clip(np.log10(np.maximum(score - self.previous_score, 1.0) + bonus), -1, 1)
        return tf.convert_to_tensor([score_coef])
            
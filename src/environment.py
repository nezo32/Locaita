import math
import numpy as np
import tensorflow as tf
from mouse_manager import MouseManager
from osu.manager import OsuManager

class Environment():
    def __init__(self, mouse_manager: MouseManager, osu_manager: OsuManager,\
        initial_screen: tuple[int, int], downscale_multiplier: int, screen_input_shape: tuple[int, int, int],
        stack_size: int,
        ):
        self.mouse_manager = mouse_manager
        self.osu_manager = osu_manager
        
        self.initial_screen = initial_screen
        self.downscale_multiplier = downscale_multiplier
        self.screen_input_shape = screen_input_shape
        self.stack_size = stack_size
        
        self.history = None
        
        self.previous_accuracy = 100.0
    
    
    def reset(self):
        self.mouse_manager.Reset()
        self.previous_accuracy = 100.0
        
        _, _, _, state = self.osu_manager.Window.GrabPlayground(self.downscale_multiplier)
        self.history = tf.concat([state for _ in range(self.stack_size - 1)], axis=0)
        _, _, _, state = self.osu_manager.Window.GrabPlayground(self.downscale_multiplier)
        self.history = tf.concat((self.history, state), axis=0)
        
        return tf.convert_to_tensor([[0.5, 0.5, 0.0, 0.0]]), tf.expand_dims(self.history, axis=0)
    
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
    
    def calculate_reward(self, accuracy: float, current_combo: int, max_combo: int):
        reward = 0
        if accuracy > self.previous_accuracy:
            reward = 0.3
        elif accuracy < self.previous_accuracy:
            reward = -0.3
        elif math.isclose(accuracy, self.previous_accuracy) and accuracy > 1:
            reward = 0.1
        elif math.isclose(accuracy, self.previous_accuracy) and accuracy < 1:
            reward = -0.3
        else:
            reward = -0.1
            
        combo_coefficient = 1.5
        if current_combo - max_combo < 0:
            combo_coefficient = np.log10(np.clip(1 / -(current_combo - max_combo), 0.02, 0.999))
        reward += 0.2 * combo_coefficient
        
        tensor = tf.convert_to_tensor([reward])    
        return tf.clip_by_value(tensor, -1, 1)
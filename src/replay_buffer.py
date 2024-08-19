import random
from collections import deque
import tensorflow as tf


class ReplayBuffer():
    def __init__(self, batch_size: int, max_memory_size: int):
        self.batch_size = batch_size
        self.__memory = deque(maxlen=max_memory_size)
    
    def len(self):
        return len(self.__memory)
    
    def push(self, state, action, reward, next_state, controls_state, next_controls_state):
        s = tf.convert_to_tensor([state])
        a = tf.convert_to_tensor([action])
        r = tf.convert_to_tensor([reward])
        n_s = tf.convert_to_tensor([next_state])
        c = tf.convert_to_tensor([controls_state])
        n_c = tf.convert_to_tensor([next_controls_state])
        self.__memory.append((s, a, r, n_s, c, n_c))
    
    def batch(self):
        return random.sample(self.__memory, self.batch_size)
    
    def clear(self):
        self.__memory.clear()
        
    def __del__(self):
        self.clear()
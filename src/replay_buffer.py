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
        self.__memory.append((state, action, reward, next_state, controls_state, next_controls_state))
    
    def batch(self):
        batch = random.sample(self.__memory, self.batch_size)
        s = tf.stack([a[0] for a in batch])
        a = tf.stack([a[1] for a in batch])
        r = tf.stack([a[2] for a in batch])
        s1 = tf.stack([a[3] for a in batch])
        c_s = tf.stack([a[4] for a in batch])
        c_s1 = tf.stack([a[5] for a in batch])
        return s, a, r, s1, c_s, c_s1
    
    def clear(self):
        self.__memory.clear()
        
    def __del__(self):
        self.clear()
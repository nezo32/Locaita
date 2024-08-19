from tensorflow import keras
import tensorflow as tf
import numpy as np

class DQN():
    def __init__(self, screen_input_shape: tuple[int, int, int], control_shape: int, learning_rate: float, load_model: bool):
        self.screen_input_shape = screen_input_shape
        self.control_shape = control_shape
        
        if load_model:
            self.load()
        else:
            self.model = self.__build()
            self.model.optimizer = keras.optimizers.Adam(learning_rate)

        keras.utils.plot_model(self.model, to_file='./architecture/dqn.png', show_shapes=True, show_layer_names=True)

    def __build(self):
        screen_input = keras.layers.Input(self.screen_input_shape)
        control_input = keras.layers.Input(self.control_shape)
        
        conv = keras.layers.LeakyReLU()(keras.layers.Conv2D(32, kernel_size=8, strides=4)(screen_input))
        conv = keras.layers.LeakyReLU()(keras.layers.Conv2D(32, kernel_size=4, strides=2)(conv))
        conv = keras.layers.LeakyReLU()(keras.layers.Conv2D(64, kernel_size=3)(conv))
        flatten = keras.layers.Flatten()(conv)
        
        fcScreen = keras.layers.LeakyReLU()(keras.layers.Dense(1024)(flatten))
        fcScreen = keras.layers.LeakyReLU()(keras.layers.Dense(1024)(fcScreen))
        
        fcControl = keras.layers.LeakyReLU()(keras.layers.Dense(64)(control_input))
        fcControl = keras.layers.LeakyReLU()(keras.layers.Dense(64)(fcControl))
        
        concat = keras.layers.Concatenate()([fcScreen, fcControl])
        output = keras.layers.Activation("tanh")(keras.layers.Dense(self.control_shape)(concat))
        
        return keras.Model(inputs=[screen_input, control_input], outputs=output)
    
    def save(self):
        self.model.save("models/index.keras")
    
    def load(self):
        loaded_model = keras.models.load_model('models/index.keras')
        if loaded_model is not None:
            self.model = loaded_model
        else:
            raise Exception("Failed to load model")
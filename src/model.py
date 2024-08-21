from tensorflow import keras
import tensorflow as tf
import numpy as np

class DQN():
    def __init__(self, screen_input_shape: tuple[int, int, int], action_input_shape: int, control_shape: int, learning_rate: float):
        self.screen_input_shape = screen_input_shape
        self.control_shape = control_shape
        self.action_input_shape = action_input_shape
        
        self.model = self.__build()
        self.optimizer = keras.optimizers.Adam(learning_rate)

        keras.utils.plot_model(self.model, to_file='./architecture/dqn.png', show_shapes=True, show_layer_names=True)

    def __build(self):
        screen_input = keras.layers.Input(self.screen_input_shape)
        control_input = keras.layers.Input(self.action_input_shape)
        
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
        self.model.save("models/index.h5")
        a_weights = self.optimizer.get_weights()
        np.save(f"./models/optimizer.npy", np.asarray([a_weights], dtype="object"),
                allow_pickle=True)
    
    def load(self):
        loaded_model = keras.models.load_model('models/index.h5')
        if loaded_model is not None:
            self.model = loaded_model
        else:
            raise Exception("Failed to load model")
        opt_weights = np.load(f"./models/optimizer.npy", allow_pickle=True)
        grad_vars = self.model.trainable_weights
        zero_grads = [tf.zeros_like(w) for w in grad_vars]
        self.optimizer.apply_gradients(zip(zero_grads, grad_vars))
        self.optimizer.set_weights(opt_weights[0])
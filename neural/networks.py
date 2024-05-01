import tensorflow as tf
from tensorflow_probability.python.layers import DistributionLambda
from tensorflow_probability.python.distributions import Normal
from tensorflow.python.keras import Model
from tensorflow.python.keras.layers import Input, Conv2D, MaxPool2D, Flatten, Dense, LeakyReLU, Concatenate, Activation
from keras.utils import plot_model


class ActorNetwork:
    def __init__(self, image_shape, outputs_count):
        self.image_shape = image_shape
        self.outputs_count = outputs_count
        self.network = self.__build()
        plot_model(self.network, to_file='./architecture/actorExtractor.png', show_shapes=True, show_layer_names=True)
    
    def __build(self):
        image_input = Input(self.image_shape)
        mouse_position_input = Input((2, ))
        mouse_press_input = Input((1, ))
        
        # Image processing
        conv_layer = Conv2D(8, (3, 3), padding="same")(image_input)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Conv2D(16, (3, 3), padding="same")(conv_layer)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Conv2D(16, (3, 3), padding="same")(conv_layer)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Conv2D(32, (3, 3), padding="same")(conv_layer)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Conv2D(32, (3, 3), padding="same")(conv_layer)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Flatten()(conv_layer)
        
        # Concat
        concat_input = Concatenate()([conv_layer, mouse_position_input, mouse_press_input])
        
        # FC
        fc = Dense(128)(concat_input)
        fc = LeakyReLU()(fc)
        fc = Dense(128)(fc)
        fc = LeakyReLU()(fc)
        mu = Dense(self.outputs_count, activation="tanh")(fc)
        sigma = Dense(self.outputs_count, activation="softplus")(fc)
        
        return Model(inputs=[image_input, mouse_position_input, mouse_press_input], outputs=[mu, sigma])
        
class CriticNetwork:
    def __init__(self, image_shape):
        self.image_shape = image_shape
        self.network = self.__build()
        plot_model(self.network, to_file='./architecture/criticExtractor.png', show_shapes=True, show_layer_names=True)
    
    def __build(self):
        # state
        image_input = Input(self.image_shape)
        mouse_position_input = Input((2, ))
        mouse_press_input = Input((1, ))
        
        # Image processing
        conv_layer = Conv2D(8, (3, 3), padding="same")(image_input)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Conv2D(16, (3, 3), padding="same")(conv_layer)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Conv2D(16, (3, 3), padding="same")(conv_layer)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Conv2D(32, (3, 3), padding="same")(conv_layer)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Conv2D(32, (3, 3), padding="same")(conv_layer)
        conv_layer = LeakyReLU()(conv_layer)
        conv_layer = MaxPool2D((2, 2), 2)(conv_layer)
        conv_layer = Flatten()(conv_layer)
        
        # Concat
        concat_input = Concatenate()([conv_layer, mouse_position_input, mouse_press_input])
        
        # FC
        fc = Dense(128)(concat_input)
        fc = LeakyReLU()(fc)
        fc = Dense(128)(fc)
        fc = LeakyReLU()(fc)
        output = Dense(1)(fc)
        
        return Model(inputs=[image_input, mouse_position_input, mouse_press_input], outputs=output) 

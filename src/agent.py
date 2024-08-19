import tensorflow as tf
from model import DQN
from replay_buffer import ReplayBuffer


class DQNAgent():
    def __init__(self, batch_size: int, max_memory_size: int, \
                 screen_input_shape: tuple[int, int, int], control_shape: int, min_experience: int, \
                 gamma: float, 
                 #epsilon: float, epsilon_min: float, epsilon_decrement: float,
                 learning_rate: float, #gradient_clipping_norm: float,\
                 load_model: bool, 
                ):
        self.batch_size = batch_size
        self.replay_buffer = ReplayBuffer(batch_size, max_memory_size)
        
        self.screen_input_shape = screen_input_shape
        self.control_shape = control_shape
        self.min_experience = min_experience
        
        self.dqn = DQN(screen_input_shape, control_shape, learning_rate, load_model)
        self.dqn_target = DQN(screen_input_shape, control_shape, learning_rate, load_model)
        
        self.learning_rate = learning_rate
        self.gamma = gamma
        """ self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decrement = epsilon_decrement """
        """ self.gradient_clipping_norm = gradient_clipping_norm """
        
        self.tensorboard = tf.summary.create_file_writer("./tensorboard/", name="main") # type: ignore
        self.step = 0    
    
    def loss(self, y_true, y_pred):
        return tf.keras.losses.MSE(y_true, y_pred)
    
    def select_action(self, state, controls_state):
        action = self.dqn.model.predict([state, controls_state])
        _, action = tf.math.reduce_max(action, axis=1)
        return action
    
    def random_action(self, x_discrete, y_discrete, click_dim=4):
        x = tf.concat([tf.clip_by_value(0.25 * tf.random.normal([4]) + 0.5, 0.0, 0.999), tf.random.uniform(shape=[1])], axis=0)
        action = tf.convert_to_tensor([int(x[0] * x_discrete) + x_discrete * int(
            x[1] * y_discrete) + x_discrete * y_discrete * int(x[2] * click_dim)])
        return action

    
    def learn(self):
        if self.replay_buffer.len() < self.min_experience:
            return
        with tf.GradientTape() as tape:
            s1, a1, r1, s2, c_s1, c_s2 = self.replay_buffer.batch()
            q = self.dqn.model(s1, c_s1)
            state_action_values = tf.stack([q[i, a1[i]] for i in range(self.batch_size)])
            next_state_values = tf.math.reduce_max(self.dqn_target.model(s2, c_s2), axis=1)[0]
            expected_state_action_values = r1 + self.gamma * next_state_values
            loss = tf.clip_by_value(self.loss(state_action_values, expected_state_action_values), 0, 1.0)
            grads = tape.gradient(loss, self.dqn.model.trainable_variables)
            t_grads = tape.gradient(loss, self.dqn_target.model.trainable_variables)
            self.dqn.model.optimizer.apply_gradients(zip(grads, self.dqn.model.trainable_variables))
            self.dqn_target.model.optimizer.apply_gradients(zip(t_grads, self.dqn_target.model.trainable_variables))
        with self.tensorboard.as_default():
            tf.summary.scalar("loss", tf.reduce_mean(loss), self.step)
            tf.summary.histogram("loss", loss, self.step)
            
            tf.summary.scalar("rewards", tf.reduce_mean(r1), self.step)
        self.step += 1
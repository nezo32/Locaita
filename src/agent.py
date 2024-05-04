import time
import numpy as np
import tensorflow as tf
import tensorflow_probability as tfp
import tensorflow.python.keras as keras
from buffer import ReplayBuffer
from networks import ActorNetwork, CriticNetwork

class Agent:
    def __init__(self, image_shape, memory, gamma=0.99,
                 actor_lr = 3e-3, critic_lr = 3e-3, sigma=0.3,
                 gae_lambda=0.95, policy_clip=0.2, actions_count=3,
                 n_epochs=10, chkpt_dir='./models/'):
        
        self.gamma = gamma
        self.sigma = sigma
        self.policy_clip = policy_clip
        self.n_epochs = n_epochs
        self.gae_lambda = gae_lambda
        self.chkpt_dir = chkpt_dir
        self.actions_count = actions_count
        self.image_shape = image_shape

        self.actor = ActorNetwork(image_shape, actions_count)
        self.critic = CriticNetwork(image_shape)
        
        self.actorOptimizer = tf.keras.optimizers.Adam(actor_lr)
        self.criticOptimizer = tf.keras.optimizers.Adam(critic_lr)
        
        self.tensorboard = tf.summary.create_file_writer("./tensorboard/", name="main")
        self.step = 0
        self.memory: ReplayBuffer = memory

    def sample_action(self, image, mousePosition, mousePress):
        image = np.array([image])
        mousePosition = np.array([mousePosition])
        mousePress = np.array([mousePress])
        
        mu = self.actor.network.predict([image, mousePosition, mousePress])
        dist = tfp.distributions.Normal(loc=mu, scale=self.sigma, allow_nan_stats=False)
        
        actions = dist.sample().numpy()[0]
        log_prob = dist.log_prob(actions).numpy()[0]
        value = self.critic.network.predict([image, mousePosition, mousePress])[0]
        
        return actions, log_prob, value

    def save_models(self):
        print('\n... saving models ...')
        self.actor.network.save_weights(self.chkpt_dir + 'actor')
        self.critic.network.save_weights(self.chkpt_dir + 'critic')
        print("... saved ...\n")

    def load_models(self):
        print('\n... loading models ...')
        self.actor.network.load_weights(self.chkpt_dir + 'actor')
        self.critic.network.load_weights(self.chkpt_dir + 'critic')
        print('... loaded ...\n')
    
    def learn(self):
        print('\n... start training ...')
        start = int(time.time())
        
        ep = self.memory.length() // self.memory.batch_size
        n = self.n_epochs if ep < self.n_epochs else ep
        for _ in range(n):
            imageStates_arr, mousePositionStates_arr, mousePressStates_arr, actions_arr, probs_arr, values_arr, rewards_arr, batches = self.memory.generate_batches()

            values = values_arr
            advantage = np.zeros(len(rewards_arr), dtype=np.float32)

            for t in range(len(rewards_arr)-1):
                discount = 1
                a_t = 0
                for k in range(t, len(rewards_arr)-1):
                    a_t += discount*(rewards_arr[k] + self.gamma*values[k+1] - values[k])
                    discount *= self.gamma*self.gae_lambda
                advantage[t] = a_t

            for batch in batches:
                with tf.GradientTape() as tapeActor, tf.GradientTape() as tapeCritic:
                    images = tf.convert_to_tensor(imageStates_arr[batch])
                    mousePositions = tf.convert_to_tensor(mousePositionStates_arr[batch])
                    mousePresses = tf.convert_to_tensor(mousePressStates_arr[batch])
                    
                    old_probs = tf.convert_to_tensor(probs_arr[batch])
                    actions = tf.convert_to_tensor(actions_arr[batch])

                    mu = self.actor.network([images, mousePositions, mousePresses])
                    dist = tfp.distributions.Normal(loc=mu, scale=self.sigma)
                    new_probs = dist.log_prob(actions)

                    critic_value = self.critic.network([images, mousePositions, mousePresses])
                    critic_value = tf.squeeze(critic_value, 1)

                    prob_ratio = tf.exp(new_probs - old_probs)
                    
                    weighted_probs = tf.expand_dims(advantage[batch], axis=1) * prob_ratio
                    clipped_probs = tf.clip_by_value(prob_ratio, 1-self.policy_clip, 1+self.policy_clip)
                    weighted_clipped_probs = clipped_probs * tf.expand_dims(advantage[batch], axis=1)
                    actor_loss = -tf.reduce_sum(tf.minimum(weighted_probs, weighted_clipped_probs))

                    returns = advantage[batch] + values[batch]
                    
                    critic_loss = tf.reduce_sum(tf.square(critic_value - returns))
                    
                    actor_grads = tapeActor.gradient(actor_loss, self.actor.network.trainable_variables)
                    critic_grads = tapeCritic.gradient(critic_loss, self.critic.network.trainable_variables)

                    self.actorOptimizer.apply_gradients(zip(actor_grads, self.actor.network.trainable_variables))
                    self.criticOptimizer.apply_gradients(zip(critic_grads, self.critic.network.trainable_variables))
                    
                
                with self.tensorboard.as_default():
                    tf.summary.scalar("loss/actor", tf.reduce_mean(actor_loss), self.step)
                    tf.summary.scalar("loss/critic", tf.reduce_mean(critic_loss), self.step)
                    tf.summary.histogram("loss/actor_loss", actor_loss, self.step)
                    tf.summary.histogram("loss/critic_loss", critic_loss, self.step)
                    
                    tf.summary.histogram('probs/old', old_probs, self.step)
                    tf.summary.histogram('probs/new', new_probs, self.step)
                    tf.summary.histogram('probs/ratio', prob_ratio, self.step)
                    

                    tf.summary.histogram("advantage", advantage[batch], self.step)
                    tf.summary.histogram("values", values[batch], self.step)
                    tf.summary.histogram("returns", returns, self.step)
                    
                    tf.summary.scalar("rewards", tf.reduce_mean(rewards_arr[batch]), self.step)
                self.step += 1

        print('... ended ...\n')

        d = divmod(int(time.time()) - start, 86400)
        h = divmod(d[1], 3600)
        m = divmod(h[1], 60)
        s = m[1]

        print('\nElapsed time %d days, %d hours, %d minutes, %d seconds\n' % (d[0],h[0],m[0],s))

        self.memory.clear_memory()
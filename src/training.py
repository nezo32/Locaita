import datetime
import os
import sys
import traceback
from dqn import DQNAgent
from environment import OsuEnv
from utils.mouse_manager import MouseManager
from osu.manager import OsuManager
from utils.scheduler import LinearSchedule


def main(osu_manager: OsuManager, mouse_manager: MouseManager):
    MAP_COUNT = 20
    STAR_RATING = 2

    WIDTH = osu_manager.Window.width
    HEIGHT = osu_manager.Window.height
    DISCRETE_FACTOR = 10

    _, _, _, img = osu_manager.Window.GrabPlayground(DISCRETE_FACTOR)
    DISCRETE_HEIGHT, DISCRETE_WIDTH, DISCRETE_DEPTH = img.shape

    BATCH_SIZE = 32
    MAX_MEMORY_SIZE = 1000000
    MIN_EXPERIENCE = 25000
    TARGET_UPDATE = 30000
    GAMMA = 0.999
    LEARNING_RATE = 5e-4

    SCHEDULE_TIMESTAMP = 4000000
    INITIAL_P = 1.0
    FINAL_P = 0.05

    INFERENCE = False

    date = datetime.datetime.now().strftime("%d-%m-%Y")
    version = 0
    def get_version(): return f"{version:06d}"
    while os.path.exists(f"./weights/dqn-{date}-%s.pt" % get_version()):
        version += 1

    # Pass to agent to load model and/or memory
    MODEL_PATH = f'./weights/dqn-{date}-{get_version()}.pt'
    MODEL_PATH_LAST = f'./weights/dqn-{date}-last.pt'
    MEMORY_PATH = f'./memory/replay_buffer-{date}-{get_version()}.pck'
    MEMORY_PATH_LAST = f'./memory/replay_buffer-{date}-last.pck'

    env = OsuEnv(mouse_manager, osu_manager, star_rating=STAR_RATING,
                 width=WIDTH, height=HEIGHT, depth=DISCRETE_DEPTH,
                 discrete_width=DISCRETE_WIDTH, discrete_height=DISCRETE_HEIGHT, discrete_factor=DISCRETE_FACTOR)
    agent = DQNAgent(batch_size=BATCH_SIZE, max_memory_size=MAX_MEMORY_SIZE, min_experience=MIN_EXPERIENCE,
                     learning_rate=LEARNING_RATE, gamma=GAMMA,
                     screen_input_shape=(env.observation_space.shape),
                     action_input_shape=env.action_space.n, control_shape=4
                     )
    scheduler = LinearSchedule(SCHEDULE_TIMESTAMP, INITIAL_P, FINAL_P)

    while True:
        inGameState = osu_manager.Memory.GetInGameState()
        hits = osu_manager.Memory.GetHitsData()
        # print(f"STATE {str(inGameState)} HITS {str(hits)}")


if __name__ == "__main__":
    osu_manager = None
    env = None

    try:
        with OsuManager() as osu_manager:
            mouse_manager = MouseManager()
            main(osu_manager, mouse_manager)

    except Exception:
        print(traceback.format_exc())

    finally:
        del env
        sys.exit(0)

    """steps = 0
     for mc in range(MAP_COUNT):
        controls_state, state = env.reset()
        learning_thread = None
        while osu_manager.Memory.GetInGameState().name == "PLAYING" or osu_manager.Memory.GetInGameState().name == "UNKNOWN":
            steps += 1
            with torch.no_grad():
                if INFERENCE:
                    action = agent.select_action(state, controls_state)
                else:
                    if steps > MIN_EXPERIENCE:
                        sample = random()
                        if sample > scheduler.value(steps):
                            action = agent.select_action(state, controls_state)
                        else:
                            action = agent.random_action(
                                DISCRETE_WIDTH, DISCRETE_HEIGHT)
                    else:
                        action = agent.random_action(
                            DISCRETE_WIDTH, DISCRETE_HEIGHT)
                if done:
                    new_state = None
                else:
                    th = Thread(target=network.memory.push,
                                args=(state, action, reward, new_state, controls_state, new_controls_state))
                    th.start()
                new_state, new_controls_state, reward, done = env.step(
                    action, steps)
                agent.replay_buffer.push(
                    state, action, reward, new_state, controls_state, new_controls_state)

            if learning_thread is not None:
                learning_thread.join()
            learning_thread = Thread(target=agent.optimize)
            learning_thread.start()

            state = new_state
            controls_state = new_controls_state

            if done:
                break

        gc.collect()

        if steps % TARGET_UPDATE == 0:
            agent.target_network.load_state_dict(agent.network.state_dict())

        if mc % 10 == 0 and mc > 0:
            agent.save(MODEL_PATH, MEMORY_PATH)
            agent.save(MODEL_PATH_LAST, MEMORY_PATH_LAST)

        helper.return_to_beatmaps()

    agent.save(MODEL_PATH, MEMORY_PATH)
    agent.save(MODEL_PATH_LAST, MEMORY_PATH_LAST) """

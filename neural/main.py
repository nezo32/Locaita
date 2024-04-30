import cv2
import win32con
import threading
import asyncio
import time
import osu
import numpy as np
from win32 import win32api
from agent import Agent
from env import Environment
from buffer import ReplayBuffer
from constants import MARGIN_LEFT, MARGIN_TOP, PLAYGROUND_WIDTH, PLAYGROUND_HEIGHT, THREAD_CLOSE_EVENT, REWARD_PRICE, ACTIONS_COUNT
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--load-models', default=False, action=argparse.BooleanOptionalAction)
args = parser.parse_args()

TRAIN_FLAG = False
END_FLAG = False
TERMINATE_FLAG = False
CLEAR_FLAG = False

def keyThread():
    global TRAIN_FLAG, END_FLAG, TERMINATE_FLAG, CLEAR_FLAG
    while True:
        if win32api.GetAsyncKeyState(win32con.VK_RCONTROL) < 0: 
            if END_FLAG:
                END_FLAG = False
            else:
                END_FLAG = True
            time.sleep(0.7)
            
        if win32api.GetAsyncKeyState(win32con.VK_NUMPAD5) < 0:
            TERMINATE_FLAG = True
        
        if win32api.GetAsyncKeyState(win32con.VK_NUMPAD0) < 0:
            if CLEAR_FLAG:
                CLEAR_FLAG = False
            else:
                CLEAR_FLAG = True
            time.sleep(0.7)
            
        if win32api.GetAsyncKeyState(win32con.VK_RSHIFT) < 0:
            if TRAIN_FLAG:
                TRAIN_FLAG = False
            else:
                TRAIN_FLAG = True
            time.sleep(0.7)
        if THREAD_CLOSE_EVENT.is_set():
            break


def calculateReward(hits, currentHits):
    hitsArray = np.asarray(hits, dtype=np.int32)
    currentArray = np.asarray(currentHits, dtype=np.int32)
    diff = currentArray - hitsArray
    return np.sum(diff * REWARD_PRICE)
    
async def main():
    global TRAIN_FLAG, END_FLAG, ACTIONS_COUNT, args
    
    memory = ReplayBuffer(64)
    agent = Agent(ACTIONS_COUNT, (202, 260, 1), memory)
    
    if (args.load_models):
        agent.load_models()
        
    osuClient = await osu.OsuClient()
    
    def save_data():
        print('\n... saving data ...')
            
        print('... saving training data ...')
        memory.save()
        print('... saved...\n')
            
        agent.save_models()
    
    keyHandler = threading.Thread(target=keyThread)
    keyHandler.start()
    
    print('\nRCTRL save data without exiting')
    print('RSHIFT start training loop (need to be in map)')
    print('NUMPAD5 save data and exit the program\n')
    
    hitsCounter = (0, 0, 0, 0, 0)
    print('\n... starting main loop ...')
    while True:
        image, _ = Environment.grabScreen((MARGIN_LEFT, MARGIN_TOP, PLAYGROUND_WIDTH, PLAYGROUND_HEIGHT))
        mousePosition = Environment.grabMousePosition()
        mousePress = Environment.getMousePressState()
        osuState = await osu.GetState(osuClient)
        inGameState = osuState["menu"]["state"]
        
        if (TRAIN_FLAG and inGameState == 2):
            hits = osuState["gameplay"]["hits"]
            currentHits = (hits["300"], hits["100"], hits["50"], hits["sliderBreaks"], hits["0"])

            actions, log_prob, value = agent.sample_action(image, mousePosition, mousePress)
            Environment.step(actions)
            reward = calculateReward(hitsCounter, currentHits)
            print(reward)
            memory.store_memory(image, mousePosition, mousePress, actions, log_prob, value, reward)

            hitsCounter = tuple(currentHits)

        if inGameState != 2:
            hitsCounter = (0, 0, 0, 0, 0)
        
        if END_FLAG:
            save_data()
            memory.clear_memory()
            END_FLAG = False
            
        if CLEAR_FLAG:
            print("\n... clearing replay buffer ...")
            memory.clear_memory()
            print("... cleared ...\n")
            
        
        if TERMINATE_FLAG:
            save_data()
            memory.clear_memory()
            break
            
        

if __name__=='__main__':
    try:
        asyncio.run(main())
    finally:
        print("Exiting program. Clearing threads...\n")
        cv2.destroyAllWindows()
        THREAD_CLOSE_EVENT.set()
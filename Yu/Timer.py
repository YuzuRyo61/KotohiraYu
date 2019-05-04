# -*- coding: utf-8 -*-

import threading
from time import sleep

class Timer:
    def __init__(self, time):
        self.time = time
        self.time_int = time
        self.working = False
    
    def _timer(self):
        while True:
            sleep(1)
            self.time -= 1
            if self.time <= 0:
                self.time = 0
                self.working = False
                print("[TIMER] TIME UP!")
                return
    
    def start(self):
        if self.working == False:
            self.working = True
            print(f"[TIMER] TIMER START! : {self.time}")
            threading.Thread(target=self._timer).start()
        else:
            print("[TIMER] ALREADY WORKING!")
    
    def check(self):
        if self.time < 0:
            return 0
        else:
            return self.time
    
    def reset(self, time=None):
        if time == None:
            self.time = self.time_int
        else:
            self.time = time
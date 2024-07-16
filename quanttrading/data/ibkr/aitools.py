
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from setting import Aiconfig
import logging
import threading
import requests
import os


class Message_Area():
    messagearea = ""
    def __init__(self) -> None:
        pass

def display_message(message:str, st:ScrolledText=None):
    """
    Display message to a scrolledText if given. otherwise, output to the sys.stdout
    """
    if str and st and isinstance(st, ScrolledText):
        st.pack()
        st.insert(tk.END, message+"\n")
        st.see(tk.END)

# display_message("x lines now ...")


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

# check if the give name is an valid asset ticker online. if name is empty. check the asset itself.
def asset_is_valid(name=""):
    if name != "":
        
        try:
            res = requests.get(Aiconfig.get('VALIDATION_ADDRESS') + name)
            if Aiconfig.get('DEBUG'):
                print("----Response in is_valid funcion is ---------", res)
                print("Status code is ",res.status_code,
                        "ticker name is ", name, 
                        "validation address is ", Aiconfig.get('VALIDATION_ADDRESS'), 
                        name)

            if res.status_code == 200:
                return True
        except Exception as ex:
            return False
    return False

import queue
def test():
    q = queue.Queue()

    def worker():
        while True:
            item = q.get()
            print(f'Working on {item}')
            print(f'Finished {item}')
            q.task_done()

    # Turn-on the worker thread.
    threading.Thread(target=worker, daemon=True).start()

    # Send thirty task requests to the worker.
    for item in range(30):
        q.put(item)

    # Block until all tasks are done.
    q.join()
    print('All work completed')
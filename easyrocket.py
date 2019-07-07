#!/usr/bin/env python3

import argparse
import atexit
import json
import os
import signal
import subprocess
import sys
import tkinter as tk

from threading import Thread

PIDFILE = "/tmp/easyrocket"

class Frame(tk.Frame):
    def __init__(self, config, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.labels = []

        self.bind("<KeyRelease>", self.keydown)
        self.focus_set()

        self.set_config(config)


    def destroy_options(self):
        for label in self.labels:
            label.destroy()

    def set_config(self, config):
        self.config = config
        self.destroy_options()

        for opt in config.get_options():
            label = tk.Label(self, text=opt.text)
            label.pack()
            self.labels.append(label)


    def keydown(self, e):
        if self.config.keydown(e.keysym):
            self.master.destroy()


class ThreadedApp(Thread):
    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        self.root = tk.Tk()
        self.frame = Frame(config=self.config, master=self.root)

        # Configure
        self.root.configure(background="white")

        self.root.eval("tk::PlaceWindow %s center" % self.root.winfo_pathname(self.root.winfo_id()))

        self.root.mainloop()


class App():
    def __init__(self, config):
        self.config = config

    def start(self):
        self.root = tk.Tk()
        self.frame = Frame(config=self.config, master=self.root)
        self.root.configure(background="white")

        self.root.eval("tk::PlaceWindow %s center" % self.root.winfo_pathname(self.root.winfo_id()))
        self.root.mainloop()


class Config:
    def __init__(self, config_file):
        with open(config_file) as f:
            config = json.load(f)
        self.options = [Option(x) for x in config]

    def keydown(self, key):
        """
        Key handler

        Returning True will exit the program
        """

        # Exit on Escape
        if key == "Escape":
            return True

        for option in self.options:
            if option.key == key:
                print("handling")
                self.handle_option(option)
                print("handle done")
                return True

        # not found, ignore or not depending on config
        return False

    def handle_option(self, option):
        if option.stdout:
            print(option.stdout)
        if option.command:
            subprocess.Popen(option.command, shell=True)


    def get_options(self):
        return self.options


class Option:
    def __init__(self, obj):
        self.key = None
        self.text = ""
        self.stdout = ""
        self.command = ""

        if "key" in obj:
            self.key = obj["key"]
        if "text" in obj:
            self.text = obj["text"]
        if "stdout" in obj:
            self.stdout = obj["stdout"]
        if "command" in obj:
            self.command = obj["command"]


def run_daemon(options):
    with open(PIDFILE, "w") as f:
        f.write(str(os.getpid()))

    app = ThreadedApp(options, show=False)
    app.start()

    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        app.toggle_show()

    signal.signal(signal.SIGUSR1, signal_handler)
    while True:
        signal.pause()


def run_normal(config):
    app = App(config)
    app.start()


def find_pid():
    try:
        with open(PIDFILE) as f:
            pid = int(f.read())

        # verify pid is correct?

        return pid
    except:
        return None

def rm_pidfile():
    if os.path.exists(PIDFILE):
        os.remove(PIDFILE)

def trigger(pid):
    os.kill(pid, signal.SIGUSR1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", "-d", action="store_true",
            help="Run daemon")
    parser.add_argument("--run", "-r", action="store_true",
            help="Run dialog")

    parser.add_argument("config", metavar="CONFIG",
            help="Config file")

    args = parser.parse_args()

    config = Config(args.config)

    if args.daemon:
        atexit.register(rm_pidfile)
        run_daemon(options)

    elif args.run:
        print("triggering daemon")
        trigger(pid)
    else:
        run_normal(config)


if __name__ == "__main__":
    main()

from utils import log

class SignalHandler():
    def __init__(self, instance):
        self.instance = instance

    def pause_handler(self, _, __):
        log('Syncronization being paused by user')
        self.instance.pause()

    def stop_handler(self, _, __):
        log('Exiting jds by user request')
        self.instance.stop()
        exit(0)
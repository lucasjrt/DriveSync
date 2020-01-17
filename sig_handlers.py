from utils import log

class SignalHandler():
    def __init__(self, instance):
        self.instance = instance

    def pause_handler(self, _, __):
        log('Syncronization paused')
        self.instance.pause()

    def resume_handler(self, _, __):
        log('Synchronization resumed')
        self.instance.resume()

    def stop_handler(self, _, __):
        log('Exiting JDS')
        self.instance.stop()
        exit(0)
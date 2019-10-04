from utils import log

class SignalHandler():
    def __init__(self, instance):
        self.instance = instance


    def stop_handler(self, _, __):
        log('Stop signal received')
        self.instance.disable_observer()
        exit(0)

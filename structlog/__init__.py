class processors:
    class TimeStamper:
        def __init__(self, fmt=None):
            pass
        def __call__(self, logger, method_name, event_dict):
            return event_dict

    @staticmethod
    def add_log_level(logger, method_name, event_dict):
        return event_dict

    class StackInfoRenderer:
        def __call__(self, logger, method_name, event_dict):
            return event_dict

    @staticmethod
    def format_exc_info(logger, method_name, event_dict):
        return event_dict

    class JSONRenderer:
        def __call__(self, logger, method_name, event_dict):
            return event_dict

def configure(*args, **kwargs):
    pass

class _Logger:
    def info(self, *args, **kwargs):
        pass

def make_filtering_bound_logger(level):
    return _Logger

get_logger = lambda name=None: _Logger()

def retry(*args, **kwargs):
    def decorator(fn):
        return fn
    return decorator

def stop_after_attempt(n):
    return None

def wait_exponential_jitter(*args, **kwargs):
    return None

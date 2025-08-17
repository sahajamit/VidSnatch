"""
Utility functions for the YouTube Downloader.
"""

import time
from functools import wraps

def retry(tries=3, delay=5, backoff=2):
    """
    A retry decorator with exponential backoff.

    Args:
        tries (int): The maximum number of attempts.
        delay (int): The initial delay between attempts in seconds.
        backoff (int): The factor by which the delay should increase after each attempt.
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    print(f"Retrying in {mdelay} seconds... ({str(e)})")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry
    return deco_retry

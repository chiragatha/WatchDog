import os
import sys
import time


class Dataset_watcher(object):
    running = True
    refresh_delay_secs = 1

    # Constructor
    def __init__(self, watch_data, call_func_on_change=None, *args, **kwargs):
        self._cached_stamp = 0
        self.filename = watch_data
        self.call_func_on_change = call_func_on_change
        self.args = args
        self.kwargs = kwargs

    # Look for changes
    def look(self):
        stamp = os.stat(self.filename).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            # File has changed, so do something...
            self.flag= True
            print(self.flag)
            if self.call_func_on_change is not None:
                self.call_func_on_change(*self.args, **self.kwargs)
        return self.flag

    # Keep watching in a loop
    def watch(self):
        while self.running:
            try:
                # Look for changes
                time.sleep(self.refresh_delay_secs)
                self.look()
            except KeyboardInterrupt:
                print('\nDone')
                break
            except FileNotFoundError:
                # Action on file not found
                pass
            except:
                print('Unhandled error: %s' % sys.exc_info()[0])

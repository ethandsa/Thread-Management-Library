import threading


class ThreadSafeQueue(list):
    def __init__(self):
        self._thread_lock = threading.Lock()
        super(ThreadSafeQueue, self).__init__()

    def __len__(self):
        with self._thread_lock:
            return super(ThreadSafeQueue, self).__len__()

    def append(self, obj):
        with self._thread_lock:
            super(ThreadSafeQueue, self).append(obj)

    def pop(self, index=0):
        with self._thread_lock:
            try:
                return super(ThreadSafeQueue, self).pop(index)
            except IndexError:
                return None

    def clear(self):
        with self._thread_lock:
            super(ThreadSafeQueue, self).clear()


class ThreadSafeInt:
    def __init__(self):
        self._thread_lock = threading.Lock()
        self._value = 0

    def increment(self, by):
        with self._thread_lock:
            self._value = self._value + by
            return self._value

    def increment_if_less_than(self, max_value):
        with self._thread_lock:
            if self._value < max_value:
                self._value += 1
                return True
            return False

    def equals(self, compare_with):
        with self._thread_lock:
            return compare_with == self._value

    def value(self):
        with self._thread_lock:
            return self._value

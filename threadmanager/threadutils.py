import time

from threadmanager.thread_events import ThreadEventsController


_event_controller = ThreadEventsController.get_instance()


def event_aware_sleep(duration, event=None):
    event = _event_controller.get_event() if not event else event
    if not event:
        time.sleep(duration)
    elif event.wait(duration):
        return False
    return True


def wait_for_condition(expression, timeout, sleep_interval=0.1, event=None):
    """Since there is a sleep time in between checks, user has to make sure to avoid race conditions."""
    event = _event_controller.get_event() if not event else event
    if not event:
        raise Exception("No event to set when condition is met")
    end_time = time.time() + timeout
    while end_time > time.time():
        if expression():  # TODO  add exception handling
            event.set()
            return True
        event_aware_sleep(sleep_interval, event)
    return False

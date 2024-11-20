import time
from abc import ABC

from ThreadEvents import ThreadEventsController


class ThreadUtils(ABC):
    """
    Abstract base class (ABC) providing utility methods for managing thread synchronization using events.
    This class serves as a base for both parent and child thread utility classes.

    Attributes:
        _event_controller (ThreadEventsController): Singleton instance to manage thread events.
        _event (threading.Event): The event object associated with the thread or thread group.
    """

    _event_controller = ThreadEventsController.get_instance()

    def __init__(self, event):
        """
        Initializes the ThreadUtils instance with a specific event object.

        Args:
            event (threading.Event): The event associated with the thread or thread group.
        """
        self._event = event

    def event_aware_sleep(self, duration):
        """
        Sleeps for the specified duration unless the event is set during this time.

        Args:
            duration (float): The duration (in seconds) to sleep.

        Returns:
            bool: False if the event was set during the sleep duration, True otherwise.
        """
        if not self._event:
            time.sleep(duration)
        elif self._event.wait(duration):
            # Avoiding busy waiting; the thread is removed from the CPU's active thread queue by the OS
            return False
        return True

    def set_event(self):
        """
        Sets the event associated with this instance, signaling other threads waiting on this event.
        """
        self._event.set()

    def wait_for_condition(self, expression, timeout, sleep_interval=0.1):
        """
        Waits for a specific condition to become True or for the timeout to expire.

        Args:
            expression (callable): A function that evaluates to True or False.
            timeout (float): The maximum time (in seconds) to wait for the condition.
            sleep_interval (float): The interval (in seconds) between checks for the condition.

        Returns:
            bool: True if the condition was met within the timeout, False otherwise.

        Note:
            The user must ensure the condition evaluation avoids race conditions.
        """
        end_time = time.time() + timeout
        while end_time > time.time():
            if expression():  # TODO: Add exception handling for expression evaluation
                self.set_event()
                return True
            self.event_aware_sleep(sleep_interval)
        return False

    @classmethod
    def set_all_events(cls):
        """
        Sets the event for all active thread groups managed by the event controller.

        Note:
            Use this method cautiously as it affects all thread groups.
        """
        cls._event_controller.set_all_events()


class ParentThreadUtils(ThreadUtils):
    """
    Utility class for managing events in parent threads.
    This class requires explicit passing of an event object during initialization.
    """

    def __init__(self, thread_group_object):
        """
        Initializes a ParentThreadUtils instance by fetching the event associated with the given thread group.

        Args:
            thread_group_object (ThreadGroup.ThreadGroup): The thread group object whose event is to be managed.

        Raises:
            Exception: If the thread group is invalid or its UUID is not registered with the event controller.
        """
        event = self._event_controller.get_event(thread_group_object.tg_uuid)
        super().__init__(event)



class ChildThreadUtils(ThreadUtils):
    """
    Utility class for managing events in child threads.
    Automatically fetches the event object based on the parent thread group ID using the event controller.
    Intended for use in threads created as part of a thread group.
    """

    def __init__(self):
        """
        Initializes the ChildThreadUtils instance by fetching the event object for the current thread group.
        """
        event = self._event_controller.get_event()
        super().__init__(event)

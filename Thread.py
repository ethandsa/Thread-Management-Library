import threading


class Thread(threading.Thread):
    """
    Custom thread class extending Python's built-in threading.Thread.
    Adds support for associating threads with a parent thread and a thread group (tg_uuid).

    Attributes:
        parent_thread_ident (int): Identifier of the thread that spawned this thread.
        tg_uuid (UUID): Unique identifier for the thread group this thread belongs to.
    """

    def __init__(self, target=None, name=None, args=(), kwargs=None, tg_uuid=None):
        """
        Initializes the custom Thread instance.

        Args:
            target (callable, optional): The function to be executed by the thread.
            name (str, optional): Name of the thread.
            args (tuple, optional): Positional arguments to pass to the target function.
            kwargs (dict, optional): Keyword arguments to pass to the target function.
            tg_uuid (UUID, optional): Unique identifier for the thread group this thread belongs to.

        Attributes Set:
            parent_thread_ident (int): The identifier of the parent thread (the thread that created this thread).
            tg_uuid (UUID): The thread group UUID associated with this thread.
        """
        super().__init__(target=target, name=name, args=args, kwargs=kwargs)
        self.parent_thread_ident = threading.current_thread().ident
        self.tg_uuid = tg_uuid

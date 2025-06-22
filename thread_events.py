import threading
import uuid

from thread_group import Thread

_thread_lock = threading.RLock()  # Module level re-entrant lock


class ThreadEventTreeNode:
    """
    Represents a node in a tree structure used to manage thread group events.
    Each node corresponds to a thread group and maintains its event, children, and parent nodes.

    Attributes:
        tg_uuid (UUID): Unique identifier for the thread group.
        event (threading.Event): Event associated with the thread group for synchronization.
        children (list): List of child nodes (sub-thread groups).
        parent (ThreadEventTreeNode): Parent node in the thread group tree.
    """

    def __init__(self, tg_uuid):
        """
        Initializes a ThreadEventTreeNode instance.

        Args:
            tg_uuid (UUID): Unique identifier for the thread group.
        """
        self.tg_uuid = tg_uuid
        self.event = threading.Event()
        self.children = []
        self.parent = None

    def add_child(self, child):
        """
        Adds a child node to the current node.

        Args:
            child (ThreadEventTreeNode): Child node to add.
        """
        with _thread_lock:
            child.parent = self
            self.children.append(child)

    def get_child_nodes(self):
        """
        Retrieves the immediate child nodes of the current node.

        Returns:
            list: List of immediate child nodes.
        """
        with _thread_lock:
            return self.children

    def get_all_child_nodes(self):
        """
        Retrieves all descendant nodes of the current node in the tree.

        Returns:
            list: List of all descendant nodes.
        """
        with _thread_lock:
            all_child_nodes = []
            nodes = [self]
            while nodes:
                curr_node = nodes.pop(0)
                for child in curr_node.children:
                    all_child_nodes.append(child)
                    nodes.append(child)
            return all_child_nodes

    def remove_child_node(self, child):
        """
        Removes a specific child node from the current node.

        Args:
            child (ThreadEventTreeNode): Child node to remove.
        """
        with _thread_lock:
            if child in self.children:
                self.children.remove(child)
                child.parent = None


class ThreadEventsController:
    """
    Singleton controller class to manage thread group events.
    Provides functionalities for mapping, notifying, and managing events across thread groups.

    Attributes:
        _instance (ThreadEventsController): Singleton instance of the controller.
    """

    _instance = None

    def __new__(cls):
        """
        Ensures a single instance of the controller is created (Singleton pattern).
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_instance()
        return cls._instance

    def _initialize_instance(self):
        """
        Initializes the singleton instance with a main thread event tree and UUID mappings.
        """
        self._main_thread_uuid = uuid.uuid4()
        self._main_thread_event_tree = ThreadEventTreeNode(self._main_thread_uuid)
        self._uuid_to_event_tree_node_map = {self._main_thread_uuid: self._main_thread_event_tree}

    @classmethod
    def get_instance(cls):
        """
        Retrieves the singleton instance of the ThreadEventsController.

        Returns:
            ThreadEventsController: Singleton instance of the controller.
        """
        return cls._instance

    def register_event_for_thread_group(self, tg_uuid):
        """
        Registers a new thread group and creates a corresponding event tree node.

        Args:
            tg_uuid (UUID): Unique identifier for the new thread group.

        Raises:
            Exception: If the thread group is created from a foreign thread.
        """
        current_thread = threading.current_thread()
        new_node = ThreadEventTreeNode(tg_uuid)
        with _thread_lock:
            self._uuid_to_event_tree_node_map[tg_uuid] = new_node
            if not isinstance(current_thread, Thread):
                if current_thread.ident != threading.main_thread().ident:
                    raise Exception("Thread Group is created from a foreign thread")  # TODO: Custom exception
                self._main_thread_event_tree.add_child(new_node)
            else:
                parent_node = self._uuid_to_event_tree_node_map[current_thread.tg_uuid]
                parent_node.add_child(new_node)

    def _get_tg_node(self, tg_uuid):
        """
        Retrieves the parent thread group node of the current thread.

        Returns:
            ThreadEventTreeNode: Parent node for the current thread.

        Raises:
            Exception: If the current thread is not associated with a thread group.
        """
        with _thread_lock:
            return self._uuid_to_event_tree_node_map[tg_uuid]
        raise Exception  # TODO: Custom exception

    def get_event(self, tg_uuid=None):
        """
        Retrieves the event associated with the parent thread group of the current thread.

        Returns:
            threading.Event: Event for the parent thread group.
        """
        if not tg_uuid:
            current_thread = threading.current_thread()
            tg_uuid = current_thread.tg_uuid
        return self._get_tg_node(tg_uuid).event

    def set_events_for_thread_group(self, tg_uuid, set_for_child_thread_groups=True):
        """
        Sets the event for a specific thread group and optionally for its child groups.

        Args:
            tg_uuid (UUID): Unique identifier for the thread group.
            set_for_child_thread_groups (bool): Whether to set events for child groups as well.
        """
        with _thread_lock:
            tg_node = self._uuid_to_event_tree_node_map[tg_uuid]
            nodes = [tg_node] + tg_node.get_all_child_nodes() if set_for_child_thread_groups else [tg_node]
            for _node in nodes:
                _node.event.set()

    def remove_thread_group(self, tg_uuid):
        """
        Removes a thread group and its associated node from the tree.

        Args:
            tg_uuid (UUID): Unique identifier for the thread group.
        """
        with _thread_lock:
            tg_node = self._uuid_to_event_tree_node_map[tg_uuid]
            self._uuid_to_event_tree_node_map.pop(tg_uuid)
            nodes = [tg_node] + tg_node.get_child_nodes()
            for node in nodes:
                node.parent.remove_child_node(node)

    def set_all_events(self):
        """
        Sets the event for all thread groups in the tree.
        """
        with _thread_lock:
            visited_nodes = set()
            all_nodes = list(self._uuid_to_event_tree_node_map.values())
            for node in all_nodes:
                if node not in visited_nodes:
                    node.event.set()
                    visited_nodes.add(node)
                    for child in node.get_all_child_nodes():
                        child.event.set()
                        visited_nodes.add(child)


controller = ThreadEventsController()  # Eager initialization on first module import

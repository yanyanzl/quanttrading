"""
Event-driven framework.
"""

from collections import defaultdict
from queue import Empty, Queue
from threading import Thread
import logging
from time import sleep
from typing import Any, Callable, List

EVENT_TIMER = "eTimer"
logger = logging.getLogger(__name__)

class Event:
    """
    Event object consists of a type string which is used
    by event engine for distributing event, and a data
    object which contains the real data.
    """

    def __init__(self, type: str, data: Any = None) -> None:
        """"""
        self.type: str = type
        self.data: Any = data


# Defines handler function to be used in event engine.
# signifies a function that takes a single parameter of 
# type Event and returns a None
# Callable[[int], str] signifies a function that takes a 
# single parameter of type int and returns a str.
HandlerType: callable = Callable[[Event], None]


class EventEngine:
    """
    Event engine distributes event object based on its type
    to those handlers registered.

    It also generates timer event by every interval seconds,
    which can be used for timing purpose.
    """

    def __init__(self, interval: int = 1) -> None:
        """
        Timer event is generated every 1 second by default, if
        interval not specified.
        could be optimized to async instead of seperate thread.
        """
        self._interval: int = interval
        self._queue: Queue = Queue()
        self._active: bool = False
        self._thread: Thread = Thread(target=self._run)
        self._timer: Thread = Thread(target=self._run_timer)
        self._handlers: defaultdict = defaultdict(list)
        self._general_handlers: List = []

    def _run(self) -> None:
        """
        Get event from queue and then process it.
        """
        logger.info(f"engine _run ...self.active{self._active=} {'££££££' * 10} ")
        while self._active:
            try:
                logger.debug(f"enter get_queue ... {'££££££' * 10} ")
                event: Event = self._queue.get(block=True, timeout=1)
                logger.debug(f"event is {event} _run ... {'££££££' * 10} ")

                self._process(event)
            except Empty:
                logger.debug(f"event is empty _run ... {'££££££' * 20} ")
                pass

    def _process(self, event: Event) -> None:
        """
        First distribute event to those handlers registered listening
        to this type.

        Then distribute event to those general handlers which listens
        to all types.
        """
        logger.debug(f"EventEngine._process:: {'******' * 5} ")
        logger.debug(f"_handlers are {self._handlers} and {event.type=}")
        if event.type in self._handlers:
            [handler(event) for handler in self._handlers[event.type]]
        
        if self._general_handlers:
            [handler(event) for handler in self._general_handlers]
        
        # Indicate that a formerly enqueued task is complete.
        self._queue.task_done()

    def _run_timer(self) -> None:
        """
        Sleep by interval second(s) and then generate a timer event.
        """
        while self._active:
            sleep(self._interval)
            event: Event = Event(EVENT_TIMER)
            self.put(event)

    def start(self) -> None:
        """
        Start event engine to process events and generate timer events.
        """
        logger.info(f"engine started ... {"******" * 20} ")
        self._active = True
        self._thread.start()
        self._timer.start()

    def stop(self) -> None:
        """
        Stop event engine.
        """
        self._active = False
        self._timer.join()
        self._thread.join()

    def put(self, event: Event) -> None:
        """
        Put an event object into event queue.
        """
        self._queue.put(event)

    def register(self, type: str, handler: Callable) -> None:
        """
        Register a new handler function for a specific event type. Every
        function can only be registered once for each event type.
        """
        logger.info(f"registering now ...........................")
        logger.info(f"{handler=}")
        handler_list: list = self._handlers[type]
        if handler not in handler_list:
            handler_list.append(handler)

    def unregister(self, type: str, handler: Callable) -> None:
        """
        Unregister an existing handler function from event engine.
        """
        handler_list: list = self._handlers[type]

        if handler in handler_list:
            handler_list.remove(handler)

        if not handler_list:
            self._handlers.pop(type)

    def register_general(self, handler: Callable) -> None:
        """
        Register a new handler function for all event types.
        only one general handler is required to handle all 
        unhandled data in the queue.
        so the queue will not be blocked. 
        """
        if handler not in self._general_handlers:
            self._general_handlers.append(handler)

    def unregister_general(self, handler: Callable) -> None:
        """
        Unregister an existing general handler function.
        """
        if handler in self._general_handlers:
            self._general_handlers.remove(handler)

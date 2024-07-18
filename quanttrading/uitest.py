"""
test example for the ui
"""
import asyncio
import time
from event.engine import EventEngine

from engine import MainEngine
from ui import MainWindow, create_qapp
from utility import current_task, printD, setUpLogger
import logging
import tracemalloc, os
from profiletools import displayTopMemory, cProfile, displayTopProfile

async def main():
    """
    main entrence of the program
    """
    # =================Testing block for optimization======================
    with cProfile.Profile() as pr:
        tracemalloc.start()
    # =================Testing block for optimization======================

        setUpLogger(logging.INFO)
        logger = logging.getLogger(__name__)
        # logger.warning("this is the warning in uitest...")

        logger.info(f"main function started at {time.strftime('%X')}")

        qapp = create_qapp()
        event_engine = EventEngine()

        main_engine = MainEngine(event_engine)

        try:

            loop = asyncio.get_running_loop()
            deadline = loop.time() + 2
            background_tasks = set()
            logger.info(f"background_tasks started at {time.strftime('%X')}")

            async with asyncio.timeout_at(deadline) as ta:
                async with asyncio.TaskGroup() as tg:
                    task8 = tg.create_task(current_task())
                    background_tasks.add(task8)
                    task8.add_done_callback(background_tasks.discard)

                logger.info(f"Taskgroup finished at {time.strftime('%X')}")

                # Nothing happens if we just call "nested()".
                # A coroutine object is created but not awaited,
                # so it *won't run at all*.
                # current_task()
                # # but if you await. it will run
                # print("here started the await current_task")
                # print(await current_task())

                """
                Save a reference to the result of this function, 
                to avoid a task disappearing mid-execution. 
                The event loop only keeps weak references to tasks. 
                A task that isn’t referenced elsewhere may get garbage collected
                at any time, even before it’s done. For reliable “fire-and-forget”
                background tasks, gather them in a collection:
                """
            # concurrent tasks by gather.
            # Schedule three calls *concurrently*:
            """
            A new alternative to create and run tasks concurrently and 
            wait for their completion is asyncio.TaskGroup. 
            TaskGroup provides stronger safety guarantees than gather 
            for scheduling a nesting of subtasks: if a task (or a subtask,
            a task scheduled by a task) raises an exception, 
            TaskGroup will, while gather will not, 
            cancel the remaining scheduled tasks).
            """
            # L = await asyncio.gather(
            #     factorial("A", 2),
            #     factorial("B", 3),
            #     factorial("C", 4),
            # )
            # print(L)

        except TimeoutError:
            logger.warning("the operation timed out, handled it here")
        except asyncio.CancelledError:
            logger.warning("the task was canceled.")
        finally:
            logger.warning("here is the clean up part of the program")

        # main_engine.add_gateway(CtpGateway)
        main_window = MainWindow(main_engine, event_engine)

        main_window.showMaximized()
        logger.info(f"main function finished 1 at {time.strftime('%X')}")
    
        # ================Testing block for optimization=======================
        fp = os.path.dirname(os.path.abspath(__file__)) + "/log/restats"
        pr.dump_stats(fp)
        snapshot: tracemalloc.Snapshot = tracemalloc.take_snapshot()
        displayTopMemory(snapshot,limit=10)
        
        displayTopProfile(fp)
        tracemalloc.stop()
        # =================Testing block for optimization======================

    qapp.exec()
    logger.info(f"main function finished 2 at {time.strftime('%X')}")


if __name__ == "__main__":
    asyncio.run(main())
    # main()

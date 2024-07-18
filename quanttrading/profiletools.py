


# ====================================================
import cProfile, pstats, io, os
from pstats import SortKey

# trace the memory allocation profile
import tracemalloc
# This is intended to read lines from modules imported
#  -- hence if a filename is not found, it will look 
# down the module search path for a file by that name.
import linecache
# ====================================================

# ====================================================
# Pympler integrates three previously separate projects
#  into a single, comprehensive profiling tool.
#  Asizeof provides basic size information for one or 
# several Python objects, muppy is used for on-line 
# monitoring of a Python application and the class tracker
#  provides off-line analysis of the lifetime of selected 
# Python objects. A web profiling frontend exposes process
#  statistics, garbage visualisation and class tracker statistics.
import pympler

# This is a python module for monitoring memory consumption
#  of a process as well as line-by-line analysis of memory
#  consumption for python programs. It is a pure python
#  module which depends on the psutil module.
import memory_profiler
# ====================================================

# ====================================================
# example 1  of the tracemalloc builtin python module.
# tracemalloc.start()

# ... run you application

# snapshot: tracemalloc.Snapshot = tracemalloc.take_snapshot()
# display_top(snapshot)

# example 2 compare.
# tracemalloc.start()
# # ... start your application ...

# snapshot1 = tracemalloc.take_snapshot()
# # ... call the function leaking memory ...
# snapshot2 = tracemalloc.take_snapshot()

# top_stats = snapshot2.compare_to(snapshot1, 'lineno')
# display_top(snapshot)
# ====================================================


    # import pstats
    # from pstats import SortKey
def displayTopProfile(fileName:str, topNum:int=10) -> None:
    """
    based on the stats file . display top profile
    """
    p = pstats.Stats(fileName)
    p.sort_stats(SortKey.TIME).print_stats(topNum)
    # p.sort_stats(SortKey.CALLS).print_stats(10)
    # # p.sort_stats(SortKey.CALLS).print_stats(10)
    # p.sort_stats(SortKey.FILENAME).print_stats('__init__')
    # p.print_callers(.5, 'init')



def displayTopMemory(snapshot:tracemalloc.Snapshot, key_type='lineno', limit=3):
    """
    Code to display the 10 lines allocating the most memory with a 
    pretty output, ignoring <frozen importlib._bootstrap> and <unknown> files:
    """
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        print("#%s: %s:%s: %.1f KiB"
              % (index, filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))




def tracedMemoryDiff():
    tracemalloc.start()

    # Example code: compute a sum with a large temporary list
    large_sum = sum(list(range(100000)))

    first_size, first_peak = tracemalloc.get_traced_memory()

    tracemalloc.reset_peak()

    # Example code: compute a sum with a small temporary list
    small_sum = sum(list(range(1000)))

    second_size, second_peak = tracemalloc.get_traced_memory()

    print(f"{first_size=}, {first_peak=}")
    print(f"{second_size=}, {second_peak=}")

def traceMemoryBlock():

    # Store 25 frames
    tracemalloc.start(25)
    import numpy
    random = numpy.random.random(1000)
    # ... run your application ...
    small_sum = sum(list(range(100000)))

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('traceback')

    # pick the biggest memory block
    stats = top_stats[:10]
    for stat in stats:
        print("%s memory blocks: %.1f KiB" % (stat.count, stat.size / 1024))
        for line in stat.traceback.format():
            print(line)

# traceMemoryBlock()
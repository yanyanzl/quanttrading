from typing import Dict, List, Callable, Tuple
from itertools import product
from concurrent.futures import ProcessPoolExecutor
from random import random, choice
from time import perf_counter
from multiprocessing import get_context
from multiprocessing.context import BaseContext
from _collections_abc import dict_keys, dict_values, Iterable

from tqdm import tqdm
from deap import creator, base, tools, algorithms

from constant import _

OUTPUT_FUNC = Callable[[str], None]
EVALUATE_FUNC = Callable[[dict], dict]
KEY_FUNC = Callable[[list], float]


# Create individual class used in genetic algorithm optimization
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)


class OptimizationSetting:
    """
    Setting for runnning optimization.
    """

    def __init__(self) -> None:
        """"""
        self.params: Dict[str, List] = {}
        # self.general_params: dict = {}
        self.target_name: str = ""

    def add_parameter(
        self,
        name: str,
        start: float,
        end: float = None,
        step: float = None
    ) -> Tuple[bool, str]:
        """
        create a list of deffirent values for a paramter based on the 
        parameter's name, start value, end value and steps between this
        two.
        """
        if end is None and step is None:
            self.params[name] = [start]
            return True, _("固定参数添加成功")

        if start >= end:
            return False, _("参数优化起始点必须小于终止点")

        if step <= 0:
            return False, _("参数优化步进必须大于0")

        value: float = start
        value_list: List[float] = []

        while value <= end:
            value_list.append(value)
            value += step

        self.params[name] = value_list

        return True, _("范围参数添加成功，数量{}").format(len(value_list))

    def set_target(self, target_name: str) -> None:
        """"""
        self.target_name = target_name

    def add_general_parameter(self, name:str, values:list) ->None:
        """
        add general parameter to the settings. Those parameters
        are the one has fixed values but not int or float.
        example: Direction, Offset. 
        name: the name of the parameter. str
        values: the values of the parameter, only one value if the
        parameter is fixed for this strategy.
        """
        if name and values:
            self.params[name] = values
            return True, f"gereral parameter added. number {len(values)}"
        else:
            return False, f"invalid general params: name: {name}, values:{values} "
        
    def generate_settings(self) -> List[dict]:
        """
        generate settings by algorithm
        """
        keys: dict_keys = self.params.keys()
        # values are list of list. each key mapped to a list of
        # different values.
        values: dict_values = self.params.values()
        """
        itertools.product(*iterables, repeat=1)
        Cartesian product of input iterables. 
        In mathematics, specifically set theory, the Cartesian product
        of two sets A and B, denoted A × B, is the set of all ordered 
        pairs (a, b) where a is in A and b is in B
        Roughly equivalent to nested for-loops in a generator 
        expression. For example, product(A, B) returns the same as 
        ((x,y) for x in A for y in B).
        """
        products: list = list(product(*values))

        settings: list = []
        for p in products:
            setting: dict = dict(zip(keys, p))
            settings.append(setting)

        return settings


def check_optimization_setting(
    optimization_setting: OptimizationSetting,
    output: OUTPUT_FUNC = print
) -> bool:
    """"""
    if not optimization_setting.generate_settings():
        output(_("优化参数组合为空，请检查"))
        return False

    if not optimization_setting.target_name:
        output(_("优化目标未设置，请检查"))
        return False

    return True


def run_bf_optimization(
    evaluate_func: EVALUATE_FUNC,
    optimization_setting: OptimizationSetting,
    key_func: KEY_FUNC,
    max_workers: int = None,
    output: OUTPUT_FUNC = print
) -> List[Tuple]:
    """
    Run brutal force optimization
    The concurrent.futures module provides a high-level interface for
    asynchronously executing callables. The asynchronous execution can
      be performed with threads, using ThreadPoolExecutor, or separate
        processes, using ProcessPoolExecutor
    """
    settings: List[Dict] = optimization_setting.generate_settings()

    output(_("开始执行穷举算法优化"))
    output(_("参数优化空间：{}").format(len(settings)))

    start: int = perf_counter()

    """
    executes calls asynchronously using a pool of at most max_workers
    processes. If max_workers is None or not given, it will default to
    the number of processors on the machine.On Windows, max_workers 
    must be less than or equal to 61. If it is not then ValueError will
      be raised. If max_workers is None, then the default chosen will
        be at most 61, even if more processors are available. 
        mp_context can be a multiprocessing context or None. It will
          be used to launch the workers. If mp_context is None or not 
          given, the default multiprocessing context is used.

    Depending on the platform, multiprocessing supports three ways to
      start a process. These start methods are:
        a. spawn: The parent process starts a fresh Python interpreter 
        process. The child process will only inherit those resources 
        necessary to run the process object’s run() method. 
        In particular, unnecessary file descriptors and handles from 
        the parent process will not be inherited. Starting a process 
        using this method is rather slow compared to using fork or 
        forkserver. Available on POSIX and Windows platforms. 
        The default on Windows and macOS.

        b. fork
        The parent process uses os.fork() to fork the Python interpreter.
          The child process, when it begins, is effectively identical
            to the parent process. All resources of the parent are 
            inherited by the child process. Note that safely forking
              a multithreaded process is problematic.
        Available on POSIX systems. Currently the default on POSIX except
          macOS.
        
        c. forkserver
        When the program starts and selects the forkserver start method
        , a server process is spawned. From then on, whenever a new 
        process is needed, the parent process connects to the server 
        and requests that it fork a new process. The fork server 
        process is single threaded unless system libraries or preloaded
          imports spawn threads as a side-effect so it is generally 
          safe for it to use os.fork(). No unnecessary resources are 
          inherited.
        Available on POSIX platforms which support passing file 
        descriptors over Unix pipes such as Linux.

    map(fn, *iterables, timeout=None, chunksize=1)
    Similar to map(fn, *iterables) except:
    the iterables are collected immediately rather than lazily;
    fn is executed asynchronously and several calls to fn may be made
      concurrently.

    """
    with ProcessPoolExecutor(
        max_workers,
        mp_context=get_context("spawn")
    ) as executor:
        """
        Instantly make your loops show a progress meter - just wrap
          any iterable with “tqdm(iterable)”, and you’re done!
        """
        it: Iterable = tqdm(
            executor.map(evaluate_func, settings),
            total=len(settings)
        )
        
        results: List[Tuple] = list(it)
        print(f"{results=} and {results[0]=}")
        if results[0]:
            results.sort(reverse=True, key=key_func)
        else:
            results = []

        end: int = perf_counter()
        cost: int = int((end - start))
        output(_("穷举算法优化完成，耗时{}秒").format(cost))

        return results


def run_ga_optimization(
    evaluate_func: EVALUATE_FUNC,
    optimization_setting: OptimizationSetting,
    key_func: KEY_FUNC,
    max_workers: int = None,
    population_size: int = 100,
    ngen_size: int = 30,
    output: OUTPUT_FUNC = print
) -> List[Tuple]:
    """Run genetic algorithm optimization"""
    # Define functions for generate parameter randomly
    buf: List[Dict] = optimization_setting.generate_settings()
    settings: List[Tuple] = [list(d.items()) for d in buf]

    def generate_parameter() -> list:
        """"""
        return choice(settings)

    def mutate_individual(individual: list, indpb: float) -> tuple:
        """"""
        size: int = len(individual)
        paramlist: list = generate_parameter()
        for i in range(size):
            if random() < indpb:
                individual[i] = paramlist[i]
        return individual,

    # Set up multiprocessing Pool and Manager
    ctx: BaseContext = get_context("spawn")
    with ctx.Manager() as manager, ctx.Pool(max_workers) as pool:
        # Create shared dict for result cache
        cache: Dict[Tuple, Tuple] = manager.dict()

        # Set up toolbox
        toolbox: base.Toolbox = base.Toolbox()
        toolbox.register("individual", tools.initIterate, creator.Individual, generate_parameter)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", mutate_individual, indpb=1)
        toolbox.register("select", tools.selNSGA2)
        toolbox.register("map", pool.map)
        toolbox.register(
            "evaluate",
            ga_evaluate,
            cache,
            evaluate_func,
            key_func
        )

        total_size: int = len(settings)
        pop_size: int = population_size                      # number of individuals in each generation
        lambda_: int = pop_size                              # number of children to produce at each generation
        mu: int = int(pop_size * 0.8)                        # number of individuals to select for the next generation

        cxpb: float = 0.95         # probability that an offspring is produced by crossover
        mutpb: float = 1 - cxpb    # probability that an offspring is produced by mutation
        ngen: int = ngen_size    # number of generation

        pop: list = toolbox.population(pop_size)

        # Run ga optimization
        output(_("开始执行遗传算法优化"))
        output(_("参数优化空间：{}").format(total_size))
        output(_("每代族群总数：{}").format(pop_size))
        output(_("优良筛选个数：{}").format(mu))
        output(_("迭代次数：{}").format(ngen))
        output(_("交叉概率：{:.0%}").format(cxpb))
        output(_("突变概率：{:.0%}").format(mutpb))

        start: int = perf_counter()

        algorithms.eaMuPlusLambda(
            pop,
            toolbox,
            mu,
            lambda_,
            cxpb,
            mutpb,
            ngen,
            verbose=True
        )

        end: int = perf_counter()
        cost: int = int((end - start))

        output(_("遗传算法优化完成，耗时{}秒").format(cost))

        results: list = list(cache.values())
        results.sort(reverse=True, key=key_func)
        return results


def ga_evaluate(
    cache: dict,
    evaluate_func: callable,
    key_func: callable,
    parameters: list
) -> float:
    """
    Functions to be run in genetic algorithm optimization.
    """
    tp: tuple = tuple(parameters)
    if tp in cache:
        result: tuple = cache[tp]
    else:
        setting: dict = dict(parameters)
        result: dict = evaluate_func(setting)
        cache[tp] = result

    value: float = key_func(result)
    return (value, )

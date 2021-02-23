"""
Prey, PredatorSpecies, PreyPool, PredatorPool, and Simulation objects
for use in simulating predation, mimicry, etc.
"""
import csv
from numbers import Real
import random
import statistics
import sys
from collections import OrderedDict
from typing import NoReturn, Union, Iterable, Tuple, List
from copy import deepcopy

# TODO: Let predator hunger and prey size influence likelihood of eating per encounter
# TODO: Add escape ability for each prey species, pursuit ability for each predator
# TODO: Allow partial phenotype resemblance
# TODO: Use a generation ratio parameter to refresh prey populations at appropriate intervals
# TODO: optimize using Numba or Cython or something


# Prey object representing a species of prey
class Prey:
    def __init__(self, popu: int = None, phen: str = None, size: float = None, camo: float = None, pal: float = None):
        self._popu = 0 if popu is None else popu
        self._popu_orig = self.popu
        self._phen = 'None' if phen is None else phen
        self._size = 1.0 if size is None else size
        self._camo = 0.0 if camo is None else camo
        self._pal = 1 if pal is None else pal

    def __str__(self) -> str:
        return self.string()
    
    @property
    def phen(self):
        return self._phen
    
    @phen.setter
    def phen(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f'phen expected to be instance of str. Instead got {type(value)}')
        elif not value:
            raise ValueError('phen string cannot be empty')
        self._phen = value
    
    @property
    def camo(self):
        return self._camo
    
    @camo.setter
    def camo(self, value: float):
        if not isinstance(value, Real):
            raise TypeError(f'camo expected to be a float. Instead got {type(value)}')
        elif not 0.0 <= value <= 1.0:
            raise ValueError(f'camo must be between 0.0 and 1.0 inclusive. Instead got {value}')
        self._camo = value
    
    @property
    def pal(self):
        return self._pal
    
    @pal.setter
    def pal(self, value: float):
        if not isinstance(value, Real):
            raise TypeError(f'pal expected to be a float. Instead got {type(value)}')
        elif not 0.0 <= value <= 1.0:
            raise ValueError(f'pal must be between 0.0 and 1.0 inclusive. Instead got {value}')
        self._pal = value
    
    @property
    def size(self):
        return self._size
    
    @size.setter
    def size(self, value: float):
        if not isinstance(value, Real):
            raise TypeError(f'size expected to be a float. Instead got {type(value)}')
        elif value <= 0:
            raise ValueError(f'size must be positive. Instead got {value}')
        self._size = value
    
    @property
    def popu(self):
        return self._popu
    
    @popu.setter
    def popu(self, value: int):
        if not isinstance(value, int):
            raise TypeError(f'popu expected to be an int. Instead got {type(value)}')
        elif value < 0:
            raise ValueError(f'popu must not be negative. Instead got {value}')
        self._popu = value
    
    @property
    def popu_orig(self):
        return self._popu_orig

    def string(self, full: bool = False) -> str:
        fields = ['_popu', '_popu_orig', '_phen', '_size', '_camo', '_pal'] if full \
            else ['_popu', '_phen', '_size', '_camo', '_pal']
        kv_pairs = []
        for field in fields:
            kv_pairs.append(f'{field[1:]}={vars(self)[field]}')
        return '; '.join(kv_pairs)


# PreyPool object representing all of the prey in one ecosystem
class PreyPool:
    def __init__(self):
        self._dict = OrderedDict()  # OrderedDict of name: Prey pairs

    def __str__(self) -> str:
        return '/'.join(self.pretty_list())

    def __iter__(self) -> Iterable[Tuple[str, Prey]]:
        return (pair for pair in self._dict.items())

    def __len__(self) -> int:
        return len(self._dict)

    def __setitem__(self, key, value) -> NoReturn:
        if not isinstance(key, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(key)}')
        elif not isinstance(value, Prey):
            raise TypeError(f'prey_obj must be instance of Prey. Instead got {type(value)}')

        assert key not in self.names, "spec_name already in names. To replace, use .replace(spec_name, prey_obj)"
        self._dict[key] = value
        for name in self.names:
            if name > key:
                self._dict.move_to_end(name)

    def __getitem__(self, item) -> Prey:
        if not isinstance(item, str):
            raise TypeError(f'Species name expected to be str. Instead got {type(item)}')
        elif item not in self.names:
            raise KeyError(f'No species named "{item}"')
        else:
            return self._dict[item]

    def __delitem__(self, key) -> NoReturn:
        if not isinstance(key, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(key)}')
        del self._dict[key]

    @property
    def names(self) -> List[str]:
        return list(self._dict.keys())

    @property
    def objects(self) -> List[Prey]:
        return list(self._dict.values())

    def add(self, spec_name: str, prey_obj: Prey) -> NoReturn:
        self[spec_name] = prey_obj

    def remove(self, spec_name: str) -> NoReturn:
        del self[spec_name]

    def replace(self, spec_name: str, prey_spec: Prey, force: bool = False) -> NoReturn:
        if (not force) or (spec_name in self.names):
            self.remove(spec_name)

        self.add(spec_name, prey_spec)

    def clear(self) -> NoReturn:
        self._dict.clear()

    def _popu_of(self, spec_name: str, surviving_only: bool = True) -> int:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        elif not isinstance(surviving_only, bool):
            raise TypeError(f'surviving_only must be instance of bool. Instead got {type(surviving_only)}')
        elif spec_name not in self.names:
            return 0

        elif surviving_only:
            return self[spec_name].popu
        else:
            return self[spec_name].popu_orig

    def popu(self, spec_name: str = None, surviving_only: bool = True) -> int:
        if spec_name is None:
            return sum([self._popu_of(p, surviving_only=surviving_only) for p in self.names])
        else:
            return self._popu_of(spec_name, surviving_only=surviving_only)

    def select(self, surviving_only: bool = True) -> Union[Tuple[str, Prey], Tuple[None, None]]:
        available_popu = self.popu(surviving_only=surviving_only)
        if not available_popu:
            return None, None
        idx = random.randrange(available_popu)
        for species, prey_obj in self:
            if idx < prey_obj.popu:
                return species, self[species]
            else:
                idx -= prey_obj.popu
        return None, None

    def repopulate(self, popu_target: int = None) -> NoReturn:
        if popu_target is None:
            popu_target = self.popu(surviving_only=False)
        else:
            popu_target = int(popu_target)
        prey_ct_latest = self.popu(surviving_only=True)
        if prey_ct_latest == 0:
            for species in self.objects:
                species.popu = 0
        else:
            for species in self.objects:
                species.popu = round(species.popu / prey_ct_latest * popu_target)

    def pretty_list(self) -> List[str]:
        return [name + ': ' + str(obj) for name, obj in self]


# PredatorSpecies object representing a species of predator
class PredatorSpecies:
    class Pred:
        def __init__(self):
            self.prefs = {}  # (phenotype: [experiences]) pairs, where an experience ranges from 0 to 1
            self.prey_eaten = 0

        def learn_all(self, prey_pool: PreyPool) -> NoReturn:
            for species in prey_pool.objects:
                if species.phen not in self.prefs:
                    self.prefs[species.phen] = []

    def __init__(self, popu, prey_types: PreyPool = None, app: int = None, mem: int = None, insatiable: bool = None):
        self.app = int(sys.maxsize) if app is None else app
        self.mem = int(sys.maxsize) if mem is None else mem
        self.insatiable = True if insatiable is None else insatiable
        rep = self.Pred()
        if prey_types is not None:
            rep.learn_all(prey_types)
        self._lst = [deepcopy(rep) for _ in range(popu)]

    def __getitem__(self, item: int) -> Pred:
        return self._lst[item]

    def __len__(self) -> int:
        return len(self._lst)

    def __str__(self) -> str:
        kv_pairs = [f'popu={self.popu}']
        for field in ['_app', '_mem', '_insatiable']:
            value = vars(self)[field]
            if value >= int(sys.maxsize):
                value = 'max'
            kv_pairs.append(f'{field[1:]}={value}')
        return '; '.join(kv_pairs)

    @property
    def app(self):
        return self._app
    
    @app.setter
    def app(self, value: int):
        if not isinstance(value, int):
            raise TypeError(f'app expected to be an int. Instead got {type(value)}')
        elif value < 0:
            raise ValueError(f'app must not be negative')
        self._app = value

    @property
    def mem(self):
        return self._mem
    
    @mem.setter
    def mem(self, value: int):
        if not isinstance(value, int):
            raise TypeError(f'mem expected to be an int. Instead got {type(value)}')
        elif value < 0:
            raise ValueError(f'mem must not be negative')
        self._mem = value

    @property
    def insatiable(self):
        return self._insatiable
    
    @insatiable.setter
    def insatiable(self, value: bool):
        self._insatiable = bool(value)
    
    @property
    def popu(self):
        return len(self)

    def eat(self, i: int, prey_item: Prey) -> NoReturn:
        pred = self[i]
        if prey_item.phen not in pred.prefs:  # first encounter with phenotype
            pred.prefs[prey_item.phen] = []

        self.update_pref(i, prey_item)
        pred.prey_eaten += prey_item.size

    def encounter(self, i: int, prey_item: Prey) -> bool:  # eat prey or decide not to
        if not self.hungry(i):
            return False

        pursuit_chance = 1  # chance of encounter
        pursuit_chance *= (1 - prey_item.camo)  # *(chance that prey is seen)
        pursuit_chance *= self.get_pref(i, prey_item.phen)  # *(chance that prey is sufficiently appetizing)

        # if not self.insatiable:
        #     size = prey_item.size
        #     if size > self.app - self.prey_eaten:
        #         size = self.app - self.prey_eaten
        #     pursuit_chance *= \
        #         size * ((self.app - self.prey_eaten) / self.app ** 2)  # *(chance that prey is sufficiently filling)

        # print(pursuit_chance)
        if pursuit_chance >= random.random():
            self.eat(i, prey_item)
            return True
        else:  # decide not to eat
            return False

    def update_pref(self, i: int, prey_item: Prey) -> NoReturn:
        pred = self[i]
        phen = prey_item.phen
        pal = prey_item.pal
        pred.prefs[phen].append(pal)  # add on most recent experience
        if len(pred.prefs[phen]) > self.mem:  # remove any experiences too old to remember
            pred.prefs[phen] = pred.prefs[phen][-self.mem:]

    def get_pref(self, i: int, phen: str) -> float:
        pred = self[i]
        if phen not in pred.prefs:
            return 1

        experiences = pred.prefs[phen]
        if not experiences:
            return 1
        elif 0 in pred.prefs[phen]:
            return 0
        else:
            return statistics.geometric_mean(experiences + [experiences[-1]])

    def pref_max(self, i: int) -> float:
        return max([self.get_pref(i, ph) for ph in self[i].prefs])

    def hungry(self, i: int) -> bool:
        return self[i].prey_eaten < self.app

    def reset(self) -> NoReturn:
        for pred in self._lst:
            for phen in pred.prefs:
                pred.prefs[phen] = []
            pred.prey_eaten = 0


# PredatorPool object representing all of the predators in one ecosystem
class PredatorPool:
    def __init__(self):
        self._dict = OrderedDict()  # OrderedDict of name: list<Predator> pairs

    def __str__(self) -> str:
        return '/'.join(self.pretty_list())

    def __iter__(self) -> Iterable[Tuple[str, PredatorSpecies]]:
        return (pair for pair in self._dict.items())

    def __len__(self) -> int:
        return len(self._dict)

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(key)}')
        elif not isinstance(value, PredatorSpecies):
            raise TypeError(f'pred_obj must be instance of PredatorSpecies. Instead got {type(value)}')

        assert key not in self.names, "spec_name already in names. To replace, use .replace(spec_name, pred_obj)"
        self._dict[key] = value
        for name in self.names:
            if name > key:
                self._dict.move_to_end(name)

    def __getitem__(self, item) -> PredatorSpecies:
        if not isinstance(item, str):
            raise TypeError(f'Species name expected to be str. Instead got {type(item)}')
        elif item not in self.names:
            raise ValueError(f'No species named "{item}"')
        else:
            return self._dict[item]

    def __delitem__(self, key) -> NoReturn:
        if not isinstance(key, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(key)}')
        del self._dict[key]
    
    @property
    def names(self) -> List[str]:
        return list(self._dict.keys())

    @property
    def objects(self) -> List[PredatorSpecies]:
        return list(self._dict.values())

    def add(self, spec_name: str, pred_spec: PredatorSpecies) -> NoReturn:
        self[spec_name] = pred_spec

    def remove(self, spec_name: str) -> NoReturn:
        del self[spec_name]

    def replace(self, spec_name: str, pred_spec: PredatorSpecies, force: bool = False) -> NoReturn:
        if not force:
            self.remove(spec_name)
        elif spec_name in self.names:
            self.remove(spec_name)

        self.add(spec_name, pred_spec)

    def clear(self) -> NoReturn:
        self._dict.clear()

    def _popu_of(self, spec_name: str, hungry_only=False) -> int:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        elif not isinstance(hungry_only, bool):
            raise TypeError(f'hungry_only must be instance of bool. Instead got {type(hungry_only)}')
        elif spec_name not in self.names:
            return 0
        elif hungry_only:
            return sum(self[spec_name].hungry(i) for i in range(self[spec_name].popu))
        else:
            return self[spec_name].popu

    def popu(self, spec_name: str = None, hungry_only: bool = False) -> int:
        if spec_name is None:
            return sum(self._popu_of(species, hungry_only=hungry_only) for species in self.names)
        else:
            return self._popu_of(spec_name, hungry_only=hungry_only)

    def select(self, hungry_only: bool = False) -> Union[Tuple[str, int], Tuple[None, None]]:
        available_popu = self.popu(hungry_only=hungry_only)
        if not available_popu:
            return None, None
        idx = random.randrange(available_popu)
        for species_name in self.names:
            if idx < self.popu(species_name, hungry_only=hungry_only):
                if hungry_only:
                    return species_name, [i for i in range(self.popu(species_name))
                                          if self._dict[species_name].hungry(i)][idx]
                else:
                    return species_name, idx
            else:
                idx -= self.popu(species_name, hungry_only=hungry_only)
        return None, None

    def reset(self) -> NoReturn:
        for pred_spec in self.objects:
            pred_spec.reset()

    def pretty_list(self) -> List[str]:
        return [name + ': ' + str(obj) for name, obj in self]


CSV = '.csv'
XML = '.simu.xml'
NONE = 'none'


# run a single-generation trial and return results
def one_gen(prey_in: PreyPool, pred_in: PredatorPool, number_of_encounters: int) \
        -> Tuple[PreyPool, PredatorPool]:
    # Simulation setup
    prey_pool = deepcopy(prey_in)
    pred_pool = deepcopy(pred_in)

    # Simulation execution
    for _ in range(number_of_encounters):
        if prey_pool.popu(surviving_only=True) > 0 and pred_pool.popu(hungry_only=True) > 0:
            prey_selected = prey_pool.select(surviving_only=False)[1]
            pred_spec_selected_name, pred_idx = pred_pool.select(hungry_only=False)
            pred_spec_selected = pred_pool[pred_spec_selected_name]
            if prey_selected is not None and pred_idx is not None:
                if pred_spec_selected.encounter(pred_idx, prey_selected):
                    prey_selected.popu -= 1
        else:  # no prey left or no hungry predators left
            break

    return prey_pool, pred_pool


# return only the last generation of a multi-generation trial
def multi_gen(prey_in: PreyPool, pred_in: PredatorPool, number_of_encounters: int, generations: int = 1,
              repopulate: bool = False) \
        -> Tuple[PreyPool, PredatorPool]:
    prey_pool_current = deepcopy(prey_in)
    pred_pool_current = deepcopy(pred_in)

    for _ in range(generations):
        pred_pool_current = deepcopy(pred_in)
        prey_pool_current.repopulate()

        prey_pool_current, pred_pool_current = one_gen(prey_pool_current, pred_pool_current, number_of_encounters)

    if repopulate:
        prey_pool_current.repopulate()
    return prey_pool_current, pred_pool_current


# return iterable over all the generations of a multi-generation trial
def all_gens(prey_in: PreyPool, pred_in: PredatorPool, number_of_encounters: int, generations: int = 1,
             repopulate: bool = False) \
        -> Iterable[Tuple[PreyPool, PredatorPool, int]]:
    prey_pool_current = deepcopy(prey_in)
    pred_pool_current = deepcopy(pred_in)

    if repopulate:
        yield prey_pool_current, pred_pool_current, 0
    for g in range(1, generations + 1):
        prey_pool_current, pred_pool_current = one_gen(prey_pool_current, pred_pool_current, number_of_encounters)
        if repopulate:
            prey_pool_current.repopulate()
            pred_pool_current = deepcopy(pred_in)
            yield prey_pool_current, pred_pool_current, g
        else:
            yield prey_pool_current, pred_pool_current, g
            prey_pool_current.repopulate()
            pred_pool_current = deepcopy(pred_in)


# Simulation object representing the parameters of one simulation but not its output
class Simulation:
    def __init__(self, title: str = None, prey_pool: PreyPool = PreyPool(),
                 pred_pool: PredatorPool = PredatorPool(), encounters: int = None, generations: int = None,
                 repetitions: int = None, repopulate: bool = False):
        self.title = 'untitled' if title is None else title

        self.prey_pool = PreyPool() if prey_pool is None else prey_pool
        self.pred_pool = PredatorPool() if pred_pool is None else pred_pool
        for pred_spec in self.pred_pool.objects:
            for pred in pred_spec:
                pred.learn_all(self.prey_pool)

        self.encounters = 1 if encounters is None else encounters
        self.generations = 1 if generations is None else generations
        self.repetitions = 1 if repetitions is None else repetitions
        self.repopulate = False if repopulate is None else repopulate

    def __str__(self) -> str:
        return f'<Simulation "{self.title}">'

    @property
    def title(self):
        return self._title
    
    @title.setter
    def title(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f'title expected to be a string. Instead got {type(value)}')
        elif not value:
            raise ValueError(f'title must not be an empty string')
        self._title = value

    @property
    def prey_pool(self):
        return self._prey_pool
    
    @prey_pool.setter
    def prey_pool(self, value: PreyPool):
        if not isinstance(value, PreyPool):
            raise TypeError(f'prey_pool expected to be a PreyPool. Instead got {type(value)}')
        self._prey_pool = value

    @property
    def pred_pool(self):
        return self._pred_pool
    
    @pred_pool.setter
    def pred_pool(self, value: PredatorPool):
        if not isinstance(value, PredatorPool):
            raise TypeError(f'pred_pool expected to be a PredPool. Instead got {type(value)}')
        self._pred_pool = value

    @property
    def encounters(self):
        return self._encounters
    
    @encounters.setter
    def encounters(self, value: int):
        if not isinstance(value, int):
            raise TypeError(f'encounters expected to be an int. Instead got {type(value)}')
        elif value < 0:
            raise ValueError(f'encounters must not be negative')
        self._encounters = value

    @property
    def generations(self):
        return self._generations
    
    @generations.setter
    def generations(self, value: int):
        if not isinstance(value, int):
            raise TypeError(f'generations expected to be an int. Instead got {type(value)}')
        elif value <= 0:
            raise ValueError(f'generations must be positive')
        self._generations = value

    @property
    def repetitions(self):
        return self._repetitions
    
    @repetitions.setter
    def repetitions(self, value: int):
        if not isinstance(value, int):
            raise TypeError(f'repetitions expected to be an int. Instead got {type(value)}')
        elif value <= 0:
            raise ValueError(f'repetitions must be positive')
        self._repetitions = value

    @property
    def repopulate(self):
        return self._repopulate
    
    @repopulate.setter
    def repopulate(self, value: bool):
        self._repopulate = bool(value)

    # run self with no return value
    def run(self, file_destination: str, verbose: bool = False, output: str = CSV, alt_title: str = None) \
            -> NoReturn:
        for _ in self.iter_run(file_destination, verbose, output=output, alt_title=alt_title):
            pass

    # run self, return an iterator over (prey_pool, pred_pool, gen)
    def iter_run(self, file_destination: str, verbose: bool = False, output: str = CSV, alt_title: str = None) \
            -> Iterable[Tuple[PreyPool, PredatorPool, int]]:
        if not file_destination or file_destination[-1] != '/':
            file_destination += '/'
        filename = file_destination + (alt_title if alt_title else self.title)
        if output == CSV:
            return self._run_csv(filename, verbose=verbose)
        elif output == XML:
            import mimsim.xml_tools as xt
            return xt.write_results(self, filename, verbose=verbose)
        elif output == NONE:
            return ((prey_out, pred_out, gen) for trial, gen, prey_out, pred_out in self.run_raw(verbose=verbose))

    # run self without writing to any file
    # return an iterator over (trial, gen, prey_pool, pred_pool)
    def run_raw(self, verbose=False) -> Iterable[Tuple[int, int, PreyPool, PredatorPool]]:
        if verbose:
            for trial in range(1, self.repetitions + 1):
                for prey_out, pred_out, gen in all_gens(self.prey_pool, self.pred_pool, self.encounters,
                                                        self.generations, repopulate=self.repopulate):
                    yield trial, gen, prey_out, pred_out
        else:
            for trial in range(1, self.repetitions + 1):
                prey_out, pred_out = multi_gen(self.prey_pool, self.pred_pool, self.encounters,
                                               self.generations, repopulate=self.repopulate)
                yield trial, 1, prey_out, pred_out

    def _run_csv(self, filename: str, verbose: bool = False) \
            -> Iterable[Tuple[PreyPool, PredatorPool, int]]:
        prey_names = self.prey_pool.names
        headers = (['trial', 'generation'] * verbose) + [species + ' popu' for species in prey_names]
        with open(filename + '.csv', 'w', newline='') as data:
            writer = csv.DictWriter(data, fieldnames=headers)
            writer.writeheader()
            trial_rows = self.run_raw(verbose=verbose)
            for trial, gen, prey_out, pred_out in trial_rows:
                yield prey_out, pred_out, gen
                this_row = {species + ' popu': prey_out.popu(species) for species in prey_names}
                if verbose:
                    this_row.update({'trial': trial, 'generation': gen})
                writer.writerow(this_row)


# run each Simulation in an Iterable[Simulation] with no return value
def run_all(file_destination: str, simulations: Iterable[Simulation], verbose: bool = False, output: str = CSV) \
        -> NoReturn:
    for sim in simulations:
        sim.run(file_destination, verbose=verbose, output=output)
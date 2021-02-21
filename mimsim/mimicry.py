"""
Prey and Predator classes for use in simulating predation, mimicry, etc.
"""

import bisect
import random
import statistics
import sys
from typing import NoReturn, Union, Iterable, Tuple, List
from copy import copy, deepcopy

# TODO: Let predator hunger and prey size influence likelihood of eating per encounter

# TODO: Use a generation ratio parameter to refresh prey populations at appropriate intervals
#       (will require work on both mimicry_old.py and mimicry_controller_old.py)

# TODO: Add escape ability for each prey species, pursuit ability for each predator

# TODO: Allow partial phenotype resemblance


# Prey object representing a species of prey
class Prey:
    def __init__(self, popu: int = None, phen: str = None, size: float = None, camo: float = None, pal: float = None):
        self.phen = set_with_default(phen, '', 'str')
        self.camo = set_with_default(camo, 0.0, 'float')
        self.pal = set_with_default(pal, 1.0, 'float')
        self.size = set_with_default(size, 1.0, 'float')
        self.popu_orig = set_with_default(popu, 0, 'int')
        self.popu = self.popu_orig

        if not 0 <= self.pal <= 1:
            raise ValueError('Palatability must be between 0 and 1 inclusive')

        if not 0 <= self.pal <= 1:
            raise ValueError('Camo must be between 0 and 1 inclusive')

    def __str__(self) -> str:
        return self.string()

    def string(self, full: bool = False) -> str:
        fields = ['popu', 'popu_orig', 'phen', 'size', 'camo', 'pal'] if full \
            else ['popu', 'phen', 'size', 'camo', 'pal']
        kv_pairs = []
        for field in fields:
            kv_pairs.append(f'{field}={vars(self)[field]}')
        return '; '.join(kv_pairs)


# PreyPool object representing all of the prey in one ecosystem
class PreyPool:
    def __init__(self):
        self._species_names = []  # list of species names only. Always sorted by the end of any method
        self._dict = {}  # dict of name: Prey pairs

    def __str__(self) -> str:
        return '/'.join(self.pretty_list())

    def __iter__(self) -> Iterable[Tuple[str, Prey]]:
        return ((name, self._dict[name]) for name in self.names)

    def __len__(self) -> int:
        return len(self._species_names)
    
    def __getitem__(self, item) -> Prey:
        if not isinstance(item, str):
            raise TypeError(f'Species name expected to be str. Instead got {type(item)}')
        elif item not in self._species_names:
            raise KeyError(f'No species named "{item}"')
        else:
            return self._dict[item]

    @property
    def dict(self) -> dict:
        return copy(self._dict)

    @property
    def names(self) -> List[str]:
        return copy(self._species_names)

    @property
    def objects(self) -> List[Prey]:
        return [self._dict[name] for name in self._species_names]

    def add(self, spec_name: str, prey_obj: Prey) -> bool:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        elif not isinstance(prey_obj, Prey):
            raise TypeError(f'prey_obj must be instance of Prey. Instead got {type(prey_obj)}')

        if spec_name in self._dict:
            return False
        bisect.insort(self._species_names, spec_name)
        self._dict[spec_name] = prey_obj
        return True

    def remove(self, spec_name: str) -> bool:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        if spec_name in self._species_names:
            self._species_names.remove(spec_name)
            del self._dict[spec_name]
            return True
        return False

    def replace(self, spec_name: str, spec_obj: Prey) -> NoReturn:
        self.remove(spec_name)
        self.add(spec_name, spec_obj)

    def clear(self) -> NoReturn:
        self._species_names = []
        self._dict = {}

    def _popu_of(self, spec_name: str, surviving_only: bool = True) -> int:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        elif not isinstance(surviving_only, bool):
            raise TypeError(f'surviving_only must be instance of bool. Instead got {type(surviving_only)}')
        elif spec_name not in self._species_names:
            return 0

        elif surviving_only:
            return self._dict[spec_name].popu
        else:
            return self._dict[spec_name].popu_orig

    def popu(self, spec_name: str = None, surviving_only: bool = True) -> int:
        if spec_name is None:
            if surviving_only:
                return sum([p.popu for p in self._dict.values()])
            else:
                return sum([p.popu_orig for p in self._dict.values()])
        else:
            return self._popu_of(spec_name, surviving_only=surviving_only)

    def repopulate(self, popu_target: int = None) -> NoReturn:
        if popu_target is None:
            popu_target = self.popu(surviving_only=False)
        prey_ct_latest = self.popu(surviving_only=True)
        if prey_ct_latest == 0:
            for species in self._dict.values():
                species.popu = 0
        else:
            for species in self._dict.values():
                species.popu = round(species.popu / prey_ct_latest * popu_target)

    def select(self, surviving_only: bool = True) -> Union[Tuple[str, Prey], Tuple[None, None]]:
        available_popu = self.popu(surviving_only=surviving_only)
        if not available_popu:
            return None, None
        idx = random.randrange(available_popu)
        for species, prey_obj in self:
            if idx < prey_obj.popu:
                return species, self._dict[species]
            else:
                idx -= prey_obj.popu
        return None, None

    def pretty_list(self) -> List[str]:
        return [name + ': ' + str(obj) for name, obj in self]


class PredatorSpecies:
    class Pred:
        def __init__(self):
            self.prefs = {}  # (phenotype: [experiences]) pairs, where an experience ranges from 0 to 1
            self.prey_eaten = 0

        def learn_all(self, prey_pool: PreyPool) -> NoReturn:
            for species in prey_pool.objects():
                if species.phen not in self.prefs:
                    self.prefs[species.phen] = []

    def __init__(self, popu, prey_types: PreyPool = None, app: int = None, mem: int = None, insatiable: bool = None):
        self.popu = set_with_default(popu, 1, 'int')
        self.app = set_with_default(app, int(sys.maxsize), 'int')
        self.mem = set_with_default(mem, int(sys.maxsize), 'int')
        self.insatiable = set_with_default(insatiable, True, 'bool')
        self.rep = self.Pred()
        if prey_types is not None:
            self.rep.learn_all(prey_types)
        self._lst = [deepcopy(self.rep) for _ in range(popu)]

    def __getitem__(self, item: int) -> Pred:
        return self._lst[item]

    def __len__(self) -> int:
        return len(self._lst)

    def __str__(self) -> str:
        kv_pairs = []
        for field in ['popu', 'app', 'mem', 'insatiable']:
            value = vars(self)[field]
            if value >= int(sys.maxsize):
                value = 'max'
            kv_pairs.append(f'{field}={value}')
        return '; '.join(kv_pairs)

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
        self._species_names = []  # list of species names only. Always sorted by the end of any method
        self._dict = {}  # dict of name: list<Predator> pairs

    def __str__(self) -> str:
        return '/'.join(self.pretty_list())

    def __iter__(self) -> Iterable[Tuple[str, PredatorSpecies]]:
        return ((name, self._dict[name]) for name in self.names)

    def __len__(self) -> int:
        return len(self._species_names)

    def __getitem__(self, item) -> PredatorSpecies:
        if not isinstance(item, str):
            raise TypeError(f'Species name expected to be str. Instead got {type(item)}')
        elif item not in self._species_names:
            raise ValueError(f'No species named "{item}"')
        else:
            return self._dict[item]

    @property
    def dict(self) -> dict:
        return copy(self._dict)
    
    @property
    def names(self) -> List[str]:
        return copy(self._species_names)

    @property
    def objects(self) -> List[PredatorSpecies]:
        return [self._dict[name] for name in self._species_names]

    def add(self, spec_name: str, pred_spec: PredatorSpecies) -> bool:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        elif not isinstance(pred_spec, PredatorSpecies):
            raise TypeError(f'prey_obj must be instance of Prey. Instead got {type(pred_spec)}')

        if spec_name in self._dict:
            return False
        bisect.insort(self._species_names, spec_name)
        self._dict[spec_name] = deepcopy(pred_spec)
        return True

    def remove(self, spec_name: str) -> bool:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        if spec_name in self._species_names:
            self._species_names.remove(spec_name)
            del self._dict[spec_name]
            return True
        return False

    def replace(self, spec_name: str, pred_spec: PredatorSpecies) -> NoReturn:
        self.remove(spec_name)
        self.add(spec_name, pred_spec)

    def clear(self) -> NoReturn:
        self._species_names = []
        self._dict = {}

    def _popu_of(self, spec_name: str, hungry_only=False) -> int:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        elif not isinstance(hungry_only, bool):
            raise TypeError(f'hungry_only must be instance of bool. Instead got {type(hungry_only)}')
        elif spec_name not in self._species_names:
            return 0
        elif hungry_only:
            return sum(self._dict[spec_name].hungry(i) for i in range(len(self._dict[spec_name])))
        else:
            return len(self._dict[spec_name])

    def popu(self, spec_name: str = None, hungry_only: bool = False) -> int:
        if spec_name is None:
            return sum(self._popu_of(species, hungry_only=hungry_only) for species in self._species_names)
        else:
            return self._popu_of(spec_name, hungry_only=hungry_only)

    def select(self, hungry_only: bool = False) -> Union[Tuple[str, int], Tuple[None, None]]:
        available_popu = self.popu(hungry_only=hungry_only)
        if not available_popu:
            return None, None
        idx = random.randrange(available_popu)
        for species_name in self.names:
            if idx < self._popu_of(species_name, hungry_only=hungry_only):
                if hungry_only:
                    return species_name, [i for i in range(self._popu_of(species_name))
                                          if self._dict[species_name].hungry(i)][idx]
                else:
                    return species_name, idx
            else:
                idx -= self._popu_of(species_name, hungry_only=hungry_only)
        return None, None

    def pretty_list(self) -> List[str]:
        return [name + ': ' + str(obj) for name, obj in self]

    def reset(self) -> NoReturn:
        for pred_spec in self._dict.values():
            pred_spec.reset()


def set_with_default(param_in, default_val, intended_type='unspecified'):
    cast = {
        'int': lambda x: int(float(x)),
        int: lambda x: int(float(x)),
        'float': float,
        float: float,
        'str': str,
        str: str,
        'bool': bool,
        bool: bool,
        'dict': dict,
        dict: dict,
        'unspecified': lambda x: x
    }
    if param_in is None or (intended_type != 'str' and param_in == ''):
        return default_val
    else:
        try:
            return cast[intended_type](param_in)
        except ValueError:
            raise ValueError(f'Could not cast {type(param_in)} to type "{intended_type}"')
            # print(f'Could not cast "{param_in}" to {intended_type}; Used default value of {default_val}')
            # return default_val

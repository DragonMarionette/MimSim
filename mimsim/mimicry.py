"""
Prey and Predator classes for use in simulating predation, mimicry, etc.
"""

import bisect
import random
import statistics
import sys
from typing import Union
from copy import copy, deepcopy

# TODO: Let predator hunger and prey size influence likelihood of eating per encounter

# TODO: Use a generation ratio parameter to refresh prey populations at appropriate intervals
#       (will require work on both mimicry_old.py and mimicry_controller_old.py)

# TODO: Add escape ability for each prey species, pursuit ability for each predator

# TODO: Allow partial phenotype resemblance


# Prey object represents a species of prey
class Prey:
    def __init__(self, phen: str = None, camo: float = None, pal: float = None, size: float = None, popu: int = None):
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

    def __str__(self):
        return self.string()

    def string(self, full: bool = False):
        fields = ['popu', 'popu_orig', 'phen', 'size', 'camo', 'pal'] if full \
            else ['popu', 'phen', 'size', 'camo', 'pal']
        kv_pairs = []
        for field in fields:
            kv_pairs.append(f'{field}={vars(self)[field]}')
        return '; '.join(kv_pairs)


# PreyPool object represents all of the prey in one ecosystem
class PreyPool:
    def __init__(self):
        self._species_names = []  # list of species names only. Always sorted by the end of any method
        self._dict = {}  # dict of name: Prey pairs

    def __iter__(self):
        return ((name, self._dict[name]) for name in self.names())

    def __len__(self):
        return len(self._species_names)

    def __str__(self):
        return '/'.join(self.pretty_list())

    def dict(self) -> dict:
        return copy(self._dict)

    def list_all(self) -> list[tuple[str, Prey]]:
        return [(name, self._dict[name]) for name in self._species_names]

    def names(self) -> list[str]:
        return copy(self._species_names)

    def species_objects(self) -> list[Prey]:
        return [self._dict[name] for name in self._species_names]

    def species(self, name: str) -> Prey:
        if not isinstance(name, str):
            raise TypeError(f'Species name expected to be str. Instead got {type(name)}')
        elif name not in self._species_names:
            raise ValueError(f'No species named "{name}"')
        else:
            return self._dict[name]

    def append(self, spec_name: str, prey_obj: Prey) -> bool:
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

    def replace(self, spec_name: str, spec_obj: Prey):
        self.remove(spec_name)
        self.append(spec_name, spec_obj)

    def clear(self):
        self._species_names = []
        self._dict = {}

    def _popu_of(self, spec_name: str, surviving_only: bool = True):
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

    def repopulate(self, popu_target: int = None):
        if popu_target is None:
            popu_target = self.popu(surviving_only=False)
        prey_ct_latest = self.popu(surviving_only=True)
        if prey_ct_latest == 0:
            for species in self._dict.values():
                species.popu = 0
        else:
            for species in self._dict.values():
                species.popu = round(species.popu / prey_ct_latest * popu_target)

    def select(self, surviving_only: bool = False) -> Union[tuple[str, Prey], tuple[None, None]]:
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

    def pretty_list(self) -> list[str]:
        return [name + ': ' + str(obj) for name, obj in self]


# Predator object represents an individual predator, which can feed on any Prey
class Predator:
    def __init__(self, prey_types: PreyPool = None, app: int = None, mem: int = None, insatiable: bool = None):
        self.prefs = {}  # (phenotype: [experiences]) pairs, where an experience ranges from 0 to 1
        prey_types = set_with_default(prey_types, PreyPool())
        self.learn_all(prey_types)

        self.app = set_with_default(app, int(sys.maxsize), intended_type='int')
        self.prey_eaten = 0

        self.mem = set_with_default(mem, int(sys.maxsize), intended_type='int')

        self.insatiable = set_with_default(insatiable, False, intended_type='bool')

    def __str__(self):
        kv_pairs = []
        for field in ['app', 'mem', 'insatiable']:
            value = vars(self)[field]
            if value >= int(sys.maxsize):
                value = 'max'
            kv_pairs.append(f'{field}={value}')
        return '; '.join(kv_pairs)

    def eat(self, prey_item: Prey):
        if prey_item.phen not in self.prefs:  # first encounter with phenotype
            self.prefs[prey_item.phen] = []

        self.update_pref(prey_item.phen, prey_item.pal)
        self.prey_eaten += prey_item.size

    def encounter(self, prey_item: Prey) -> bool:  # eat prey or decide not to
        if not self.hungry():
            return False
#  TODO: figure out why pursuit chance is getting lower after the first generation
        pursuit_chance = 1  # chance of encounter
        pursuit_chance *= (1 - prey_item.camo)  # *(chance that prey is seen)
        pursuit_chance *= self.get_pref(prey_item.phen)  # *(chance that prey is sufficiently appetizing)

        # if not self.insatiable:
        #     size = prey_item.size
        #     if size > self.app - self.prey_eaten:
        #         size = self.app - self.prey_eaten
        #     pursuit_chance *= \
        #         size * ((self.app - self.prey_eaten) / self.app ** 2)  # *(chance that prey is sufficiently filling)

        # print(pursuit_chance)
        if pursuit_chance >= random.random():
            self.eat(prey_item)
            return True
        else:  # decide not to eat
            return False

    def update_pref(self, phen: str, pal: float):
        self.prefs[phen].append(pal)  # add on most recent experience
        if len(self.prefs[phen]) > self.mem:  # remove any experiences too old to remember
            self.prefs[phen] = self.prefs[phen][-self.mem:]

    def get_pref(self, phen: str) -> float:
        if phen not in self.prefs:
            return 1

        experiences = self.prefs[phen]
        if not experiences:
            return 1
        elif 0 in self.prefs[phen]:
            return 0
        else:
            return statistics.geometric_mean(experiences + [experiences[-1]])

    def learn_all(self, prey_pool: PreyPool):
        for species in prey_pool.species_objects():
            if species.phen not in self.prefs:
                self.prefs[species.phen] = []

    def pref_max(self) -> float:
        return max([self.get_pref(p) for p in self.prefs])

    def hungry(self) -> bool:
        return self.prey_eaten < self.app

    def reset(self):
        for phen in self.prefs:
            self.prefs[phen] = []
        self.prey_eaten = 0


# PreyPool object represents all of the predators in one ecosystem
class PredatorPool:
    def __init__(self):
        self._species_names = []  # list of species names only. Always sorted by the end of any method
        self._dict = {}  # dict of name: list<Predator> pairs

    def __iter__(self):
        return ((name, self._dict[name]) for name in self.names())

    def __len__(self):
        return len(self._species_names)

    def __str__(self):
        return '/'.join(self.pretty_list())

    def dict(self) -> dict:
        return copy(self._dict)

    def list_all_reps(self) -> list[tuple[str, Predator]]:
        return [(name, deepcopy(self._dict[name][0])) for name in self._species_names]

    def list_all_lists(self) -> list[tuple[str, list[Predator]]]:
        return [(name, self._dict[name]) for name in self._species_names]

    def names(self) -> list[str]:
        return copy(self._species_names)

    def species_reps(self) -> list[Predator]:
        return [deepcopy(self._dict[name][0]) for name in self._species_names]

    def species_rep(self, name: str) -> Predator:
        if not isinstance(name, str):
            raise TypeError(f'Species name expected to be str. Instead got {type(name)}')
        elif name not in self._species_names:
            raise ValueError(f'No species named "{name}"')
        else:
            return deepcopy(self._dict[name][0])

    def species_lists(self) -> list[list[Predator]]:
        return [self._dict[name] for name in self._species_names]

    def species_list(self, name: str) -> list[Predator]:
        if not isinstance(name, str):
            raise TypeError(f'Species name expected to be str. Instead got {type(name)}')
        elif name not in self._species_names:
            raise ValueError(f'No species named "{name}"')
        else:
            return self._dict[name]

    def append(self, spec_name: str, pred_obj: Predator, count: int) -> bool:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        elif not isinstance(pred_obj, Predator):
            raise TypeError(f'prey_obj must be instance of Prey. Instead got {type(pred_obj)}')
        elif not isinstance(count, int):
            raise TypeError(f'count must be instance of int. Instead got {type(count)}')

        if spec_name in self._dict:
            return False
        bisect.insort(self._species_names, spec_name)
        self._dict[spec_name] = [deepcopy(pred_obj) for _ in range(count)]
        return True

    def remove(self, spec_name: str) -> bool:
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        if spec_name in self._species_names:
            self._species_names.remove(spec_name)
            del self._dict[spec_name]
            return True
        return False

    def replace(self, spec_name: str, spec_obj: Predator, count: int):
        self.remove(spec_name)
        self.append(spec_name, spec_obj, count)

    def clear(self):
        self._species_names = []
        self._dict = {}

    def _popu_of(self, spec_name: str, hungry_only=False):
        if not isinstance(spec_name, str):
            raise TypeError(f'spec_name must be instance of string. Instead got {type(spec_name)}')
        elif not isinstance(hungry_only, bool):
            raise TypeError(f'hungry_only must be instance of bool. Instead got {type(hungry_only)}')
        elif spec_name not in self._species_names:
            return 0
        elif hungry_only:
            return sum(pred.hungry() for pred in self._dict[spec_name])
        else:
            return len(self._dict[spec_name])

    def popu(self, spec_name: str = None, hungry_only: bool = False) -> int:
        if spec_name is None:
            return sum(self._popu_of(species, hungry_only=hungry_only) for species in self._species_names)
        else:
            return self._popu_of(spec_name, hungry_only=hungry_only)

    def select(self, hungry_only: bool = False) -> Union[tuple[str, Predator], tuple[None, None]]:
        available_popu = self.popu(hungry_only=hungry_only)
        if not available_popu:
            return None, None
        idx = random.randrange(available_popu)
        for species in self.names():
            if idx < self._popu_of(species, hungry_only=hungry_only):
                if hungry_only:
                    return species, [pred for pred in self._dict[species] if pred.hungry()][idx]
                else:
                    return species, self._dict[species][idx]
            else:
                idx -= self._popu_of(species, hungry_only=hungry_only)
        return None, None

    def pretty_list(self):
        return [name + ': popu=' + str(len(obj)) + '; ' + str(obj[0]) for name, obj in self]

    def reset(self):
        for pred_list in self._dict.values():
            for pred in pred_list:
                pred.reset()


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
            # raise ValueError(f'Could not cast {type(param_in)} to type "{intended_type}"')
            # print(f'Could not cast "{param_in}" to {intended_type}; Used default value of {default_val}')
            return default_val

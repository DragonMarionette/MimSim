# builtin or external imports
import csv
from copy import deepcopy
from typing import Iterable

# imports from this package
import mimsim.mimicry as mim

# TODO: optimize using Numba or Cython or something


# Runs a single-generation trial and returns results
def one_gen(prey_in: mim.PreyPool, pred_in: mim.PredatorPool,
            number_of_encounters: int) -> tuple[mim.PreyPool, mim.PredatorPool]:
    # Simulation setup
    prey_pool = deepcopy(prey_in)
    pred_pool = deepcopy(pred_in)

    # Simulation execution
    for _ in range(number_of_encounters):
        if prey_pool.popu(surviving_only=True) > 0 and pred_pool.popu(hungry_only=True) > 0:
            prey_selected = prey_pool.select(surviving_only=False)[1]
            pred_selected = pred_pool.select(hungry_only=False)[1]
            if prey_selected is not None and pred_selected is not None:
                if pred_selected.encounter(prey_selected):
                    prey_selected.popu -= 1
        else:  # no prey left or no hungry predators left
            break

    return prey_pool, pred_pool


# Returns only the last generation of a multi-generation trial
def multi_gen(prey_in: mim.PreyPool, pred_in: mim.PredatorPool, number_of_encounters: int,
              generations: int = 1, repopulate: bool = False) -> tuple[mim.PreyPool, mim.PredatorPool]:

    prey_pool_current = deepcopy(prey_in)
    pred_pool_current = deepcopy(pred_in)

    for _ in range(generations):
        pred_pool_current = deepcopy(pred_in)
        prey_pool_current.repopulate()

        prey_pool_current, pred_pool_current = one_gen(prey_pool_current, pred_pool_current, number_of_encounters)

    if repopulate:
        prey_pool_current.repopulate()
    return prey_pool_current, pred_pool_current


# Iterable over all the generations of a multi-generation trial
def all_gens(prey_in: mim.PreyPool, pred_in: mim.PredatorPool, number_of_encounters: int, generations: int = 1,
             repopulate: bool = False) -> Iterable[tuple[mim.PreyPool, mim.PredatorPool, int]]:

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


class Simulation:
    def __init__(self, title: str = None, prey_pool: mim.PreyPool = mim.PreyPool(),
                 pred_pool: mim.PredatorPool = mim.PredatorPool(), encounters: int = None, generations: int = None,
                 repetitions: int = None, repopulate: bool = False, cols_extra: dict = None):
        self.title = mim.set_with_default(title, '')
        self.prey_pool = prey_pool
        self.pred_pool = pred_pool
        for pred_list in self.pred_pool.species_lists():
            for pred in pred_list:
                pred.learn_all(self.prey_pool)
        self.encounters = mim.set_with_default(encounters, 1, intended_type='int')
        self.generations = mim.set_with_default(generations, 1, intended_type='int')
        self.repetitions = mim.set_with_default(repetitions, 1, intended_type='int')
        self.repopulate = mim.set_with_default(repopulate, False)
        self.cols_extra = mim.set_with_default(cols_extra, dict())

    def __str__(self):
        return f'<Simulation "{self.title}">'

    def run(self, file_destination: str, verbose: bool = False):
        if not file_destination or file_destination[-1] != '/':
            file_destination += '/'
        prey_names = self.prey_pool.names()
        headers = (['trial', 'generation'] * verbose)\
                  + [species + ' popu' for species in prey_names] + list(self.cols_extra)
        with open(file_destination + self.title + '.csv', 'w', newline='') as data:
            writer = csv.DictWriter(data, fieldnames=headers)
            writer.writeheader()
            for trial in range(1, self.repetitions + 1):
                if verbose:
                    trial_rows = all_gens(self.prey_pool, self.pred_pool, self.encounters,
                                          self.generations, repopulate=self.repopulate)
                else:
                    sole_prey_row, sole_pred_row = multi_gen(self.prey_pool, self.pred_pool, self.encounters,
                                                             self.generations, repopulate=self.repopulate)
                    trial_rows = [(sole_prey_row, sole_pred_row, self.generations + 1)]

                for prey_out, _, gen in trial_rows:
                    this_row = {species + ' popu': prey_out.popu(species) for species in prey_names}
                    this_row.update(self.cols_extra)
                    if verbose:
                        this_row.update({'trial': trial, 'generation': gen})
                    writer.writerow(this_row)

    @staticmethod
    def run_all(file_destination: str, simulations: list, verbose: bool = False, make_xml: bool = True):
        for sim in simulations:
            print(f'Running simulation {sim.title}...')
            sim.run(file_destination, verbose=verbose, make_xml=make_xml)

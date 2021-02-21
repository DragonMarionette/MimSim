# builtin or external imports
import csv
from copy import deepcopy
from typing import NoReturn, Tuple, Iterable

# imports from this package
import mimsim.mimicry as mim

CSV = '.csv'
XML = '.simu.xml'
NONE = 'none'


# TODO: optimize using Numba or Cython or something


# run a single-generation trial and returns results
def one_gen(prey_in: mim.PreyPool, pred_in: mim.PredatorPool, number_of_encounters: int) \
        -> Tuple[mim.PreyPool, mim.PredatorPool]:
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
def multi_gen(prey_in: mim.PreyPool, pred_in: mim.PredatorPool, number_of_encounters: int, generations: int = 1,
              repopulate: bool = False) \
        -> Tuple[mim.PreyPool, mim.PredatorPool]:
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
def all_gens(prey_in: mim.PreyPool, pred_in: mim.PredatorPool, number_of_encounters: int, generations: int = 1,
             repopulate: bool = False) \
        -> Iterable[Tuple[mim.PreyPool, mim.PredatorPool, int]]:
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
    def __init__(self, title: str = None, prey_pool: mim.PreyPool = mim.PreyPool(),
                 pred_pool: mim.PredatorPool = mim.PredatorPool(), encounters: int = None, generations: int = None,
                 repetitions: int = None, repopulate: bool = False):
        self.title = mim.set_with_default(title, '')
        self.prey_pool = prey_pool
        self.pred_pool = pred_pool
        for pred_spec in self.pred_pool.objects:
            for pred in pred_spec:
                pred.learn_all(self.prey_pool)
        self.encounters = mim.set_with_default(encounters, 1, intended_type='int')
        self.generations = mim.set_with_default(generations, 1, intended_type='int')
        self.repetitions = mim.set_with_default(repetitions, 1, intended_type='int')
        self.repopulate = mim.set_with_default(repopulate, False)

    def __str__(self) -> str:
        return f'<Simulation "{self.title}">'

    # run self with no return value
    def run(self, file_destination: str, verbose: bool = False, output: str = CSV, alt_title: str = None) \
            -> NoReturn:
        for _ in self.iter_run(file_destination, verbose, output=output, alt_title=alt_title):
            pass

    # run self, return an iterator over (prey_pool, pred_pool, gen)
    def iter_run(self, file_destination: str, verbose: bool = False, output: str = CSV, alt_title: str = None) \
            -> Iterable[Tuple[mim.PreyPool, mim.PredatorPool, int]]:
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
    def run_raw(self, verbose=False) -> Iterable[Tuple[int, int, mim.PreyPool, mim.PredatorPool]]:
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
            -> Iterable[Tuple[mim.PreyPool, mim.PredatorPool, int]]:
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

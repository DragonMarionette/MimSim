"""
build_xml(Simulation) -> lxml.etree.ElementTree
write_xml(path, sim) -> None
load_sim(file_path, as_dict=False) -> mc.Simulation
"""

# builtin or external imports
from copy import deepcopy

import lxml.etree as et

# imports from this package
import mimsim.mimicry as mim


# Functions for writing a Simulation to XML

def _build_meta(data, title, encounters, generations, repetitions, repopulate, cols_extra):
    meta = et.SubElement(data, 'meta')
    meta.set('title', title)
    meta.set('encounters', str(encounters))
    meta.set('generations', str(generations))
    meta.set('repetitions', str(repetitions))
    meta.set('repopulate', str(repopulate))

    cols = et.SubElement(meta, 'cols_extra')
    for k, v in cols_extra.items():
        et.SubElement(cols, 'col', {'key': k, 'val': str(v), 'type': str(type(v))})


def _build_prey(data, prey_pool):
    prey = et.SubElement(data, 'prey')
    for prey_name, prey_obj in prey_pool:
        prey_spec = et.SubElement(prey, 'prey_spec')
        prey_spec.set('spec_name', prey_name)
        prey_spec.set('phen', prey_obj.phen)
        prey_spec.set('camo', str(prey_obj.camo))
        prey_spec.set('pal', str(prey_obj.pal))
        prey_spec.set('size', str(prey_obj.size))
        prey_spec.set('popu', str(prey_obj.popu_orig))


def _build_pred(data, pred_pool):
    predators = et.SubElement(data, 'predators')
    for pred_name in pred_pool.names():
        pred_obj = pred_pool.species_rep(pred_name)
        pred_spec = et.SubElement(predators, 'pred_spec')
        pred_spec.set('spec_name', pred_name)
        pred_spec.set('app', str(pred_obj.app))
        pred_spec.set('mem', str(pred_obj.mem))
        pred_spec.set('insatiable', str(pred_obj.insatiable))
        pred_spec.set('popu', str(pred_pool._popu_of(pred_name)))


def build_xml(sim) -> et.ElementTree:
    data = et.Element('data')
    _build_meta(data, sim.title, sim.encounters, sim.generations, sim.repetitions, sim.repopulate, sim.cols_extra)
    _build_prey(data, sim.prey_pool)
    _build_pred(data, sim.pred_pool)
    return et.ElementTree(data)


def write_xml(destination_path, sim) -> None:
    if destination_path[-1] != '/':
        destination_path += '/'
    data_tree = build_xml(sim)
    data_tree.write(destination_path + sim.title + '.rsc', pretty_print=True)


# Functions for reading a Simulation from XML

def _load_meta(data):
    attr = deepcopy(data.find('meta').attrib)
    attr['encounters'] = int(attr['encounters'])
    attr['generations'] = int(attr['generations'])
    attr['repetitions'] = int(attr['repetitions'])
    attr['repopulate'] = attr['repopulate'] == 'True'

    attr['cols_extra'] = dict()
    for c in data.find('meta').find('cols_extra').findall('col'):
        attr['cols_extra'][c.get('key')] = _convert_as(c.get('type'), c.get('val'))
    return attr


def _convert_as(val_type, value):
    conversions = {
        "<class 'int'>": int,
        "<class 'float'>": float,
        "<class 'bool'>": bool,
        "<class 'str'>": str
    }
    return conversions[val_type](value)


def _load_prey(data):
    prey_pool = mim.PreyPool()
    for species in data.find('prey').findall('prey_spec'):
        prey_pool.append(
            species.get('spec_name'),
            mim.Prey(phen=species.get('phen'), camo=float(species.get('camo')),
                     pal=float(species.get('pal')),
                     size=float(species.get('size')), popu=int(species.get('popu')))
        )
    return prey_pool


def _load_pred(data, prey_pool=None):
    pred_pool = mim.PredatorPool()
    for species in data.find('predators').findall('pred_spec'):
        pred_pool.append(
            species.attrib['spec_name'],
            mim.Predator(prey_types=prey_pool, app=int(species.get('app')),
                         mem=int(species.get('mem')), insatiable=(species.get('insatiable') == 'True')),
            int(species.get('popu'))
        )

    return pred_pool


def load_sim(file_path: str):
    tree = et.parse(file_path)
    data = tree.getroot()
    meta = _load_meta(data)
    prey_pool = _load_prey(data)
    pred_pool = _load_pred(data, prey_pool=prey_pool)
    import controller as mc
    return mc.Simulation(title=meta['title'], prey_pool=prey_pool, pred_pool=pred_pool,
                         encounters=meta['encounters'], generations=meta['generations'],
                         repetitions=meta['repetitions'],
                         repopulate=meta['repopulate'], cols_extra=meta['cols_extra'])

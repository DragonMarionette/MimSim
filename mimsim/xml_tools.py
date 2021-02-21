"""
Utilities for reading/writing simulations and their results from/to *.simu.xml files

validate_sim(tree) -> bool
load_prey_pool(file_path_in) -> mim.PreyPool
load_pred_pool(file_path_in) -> mim.PredatorPool
load_sim(file_path_in) -> mc.Simulation
write_desc(path, sim) -> None
write_results(sim, filename, verbose=False) -> None
"""

# builtin or external imports
import lxml.etree as et
# imports from this package
from mimsim import controller as mc
from mimsim import mimicry as mim


# return true if tree is a valid simulation, otherwise raise AssertionError
def validate_sim(tree: et.ElementTree, allow_desc: bool = True, allow_output: bool = True) -> bool:
    desc_schema_src = et.parse('../mimsim/rsc/desc_specification.xsd')
    desc_schema = et.XMLSchema(desc_schema_src)
    desc_valid = desc_schema.validate(tree)

    output_schema_src = et.parse('../mimsim/rsc/output_specification.xsd')
    output_schema = et.XMLSchema(output_schema_src)
    output_valid = output_schema.validate(tree)

    if not allow_desc:
        assert not desc_valid, 'File is a valid simulation description file; forbidden by flag desc_ok=False'
    if not allow_output:
        assert not output_valid, 'File is a valid simulation output file; forbidden by flag output_ok=False'
    assert desc_valid or output_valid, "File is not a valid simulation"

    return True


def _prey_from_root(root: et.Element) -> mim.PreyPool:
    prey_pool = mim.PreyPool()
    prey_root = root.find('prey_pool')
    for species in prey_root:
        prey_pool.append(
            species.find('spec_name').text,
            mim.Prey(popu=int(species.find('popu').text), phen=species.find('phen').text,
                     size=float(species.find('size').text), camo=float(species.find('camo').text),
                     pal=float(species.find('pal').text))
        )
    return prey_pool


# return the prey pool described in a given .simu.xml file
def load_prey_pool(file_path_in: str) -> mim.PreyPool:
    sim_tree = et.parse(file_path_in)
    validate_sim(sim_tree)
    root = sim_tree.getroot()
    return _prey_from_root(root)


def _pred_from_root(root: et.Element) -> mim.PredatorPool:
    pred_pool = mim.PredatorPool()
    prey_root = root.find('pred_pool')
    for species in prey_root:
        pred_pool.append(
            species.find('spec_name').text,
            mim.PredatorSpecies(
                app=int(species.find('app').text),
                mem=int(species.find('mem').text),
                insatiable=bool(species.find('insatiable').text in ('true', '1')),
                popu=int(species.find('popu').text)
            )
        )
    return pred_pool


# return the predator pool described in a given .simu.xml file
def load_pred_pool(file_path_in: str) -> mim.PredatorPool:
    sim_tree = et.parse(file_path_in)
    validate_sim(sim_tree)
    root = sim_tree.getroot()
    return _pred_from_root(root)


# return the Simulation described in a given .simu.xml file
def load_sim(file_path_in: str) -> mc.Simulation:
    sim_tree = et.parse(file_path_in)
    validate_sim(sim_tree)
    root = sim_tree.getroot()
    params = {elem.tag: elem.text for elem in root.find('params')}
    prey_pool = _prey_from_root(root)
    pred_pool = _pred_from_root(root)
    return mc.Simulation(
        title=params['title'],
        encounters=int(params['encounters']),
        generations=int(params['generations']),
        repetitions=int(params['repetitions']),
        repopulate=(params['repopulate'] in ('true', '1')),
        prey_pool=prey_pool,
        pred_pool=pred_pool
    )


def _build_desc(sim: mc.Simulation) -> et.ElementTree():
    root = et.Element('simulation')

    params = et.SubElement(root, 'params')
    et.SubElement(params, 'title').text = sim.title
    et.SubElement(params, 'encounters').text = str(sim.encounters)
    et.SubElement(params, 'generations').text = str(sim.generations)
    et.SubElement(params, 'repetitions').text = str(sim.repetitions)
    et.SubElement(params, 'repopulate').text = str(int(sim.repopulate))

    prey_pool = et.SubElement(root, 'prey_pool')
    for prey_name, prey_obj in sim.prey_pool:
        prey_elem = et.SubElement(prey_pool, 'prey_spec')
        et.SubElement(prey_elem, 'spec_name').text = prey_name
        et.SubElement(prey_elem, 'popu').text = str(prey_obj.popu)
        et.SubElement(prey_elem, 'phen').text = prey_obj.phen
        et.SubElement(prey_elem, 'size').text = str(prey_obj.size)
        et.SubElement(prey_elem, 'camo').text = str(prey_obj.camo)
        et.SubElement(prey_elem, 'pal').text = str(prey_obj.pal)

    pred_pool = et.SubElement(root, 'pred_pool')
    for pred_name, pred_obj in sim.pred_pool:
        pred_elem = et.SubElement(pred_pool, 'pred_spec')
        et.SubElement(pred_elem, 'spec_name').text = pred_name
        et.SubElement(pred_elem, 'popu').text = str(pred_obj.popu)
        et.SubElement(pred_elem, 'app').text = str(pred_obj.app)
        et.SubElement(pred_elem, 'mem').text = str(pred_obj.mem)
        et.SubElement(pred_elem, 'insatiable').text = str(int(pred_obj.insatiable))

    return et.ElementTree(root)


# write description of sim to the specified .simu.xml file
def write_desc(sim: mc.Simulation, destination_folder: str, alt_title=None):
    if not destination_folder or destination_folder[-1] != '/':
        destination_folder += '/'
    filename = destination_folder + (sim.title if alt_title is None else alt_title)
    data_tree = _build_desc(sim)
    data_tree.write(filename + '.simu.xml', xml_declaration=True, pretty_print=True)


# write description and results of sim to the specified .simu.xml file, yielding each generation
# not recommended to use; prefer the wrapper sim.iter_run(..., output=controller.XML)
def write_results(sim: mc.Simulation, filename: str, verbose: bool = False):
    sim_tree = _build_desc(sim)
    root = sim_tree.getroot()

    prey_names = sim.prey_pool.names()
    prey_root = root.find('prey_pool')
    prey_result_roots = dict()
    for prey_species_root in prey_root.findall('prey_spec'):
        spec_name = prey_species_root.findtext('spec_name')
        prey_result_roots[spec_name] = et.SubElement(prey_species_root, 'results')

    pred_names = sim.pred_pool.names()
    pred_root = root.find('pred_pool')
    pred_result_roots = dict()
    for pred_species_root in pred_root.findall('pred_spec'):
        spec_name = pred_species_root.findtext('spec_name')
        pred_result_roots[spec_name] = et.SubElement(pred_species_root, 'results')

    prey_trial_nodes = dict()  # These two statements do nothing but avoid a warning
    pred_trial_nodes = dict()

    last_trial = -1
    for trial, gen, prey_out, pred_out in sim.run_raw(verbose=verbose):
        if trial > last_trial:
            last_trial = trial
            prey_trial_nodes = {name: et.SubElement(prey_result_roots[name], 'trial') for name in prey_names}
            for node in prey_trial_nodes.values():
                et.SubElement(node, 'trial_number').text = str(trial)
            pred_trial_nodes = {name: et.SubElement(pred_result_roots[name], 'trial') for name in pred_names}
            for node in pred_trial_nodes.values():
                et.SubElement(node, 'trial_number').text = str(trial)

        for prey_species in prey_names:
            this_gen_node = et.SubElement(prey_trial_nodes[prey_species], 'generation')
            et.SubElement(this_gen_node, 'generation_number').text = str(gen)
            et.SubElement(this_gen_node, 'population').text = str(prey_out.popu(prey_species))

        for pred_species in pred_names:
            this_gen_node = et.SubElement(pred_trial_nodes[pred_species], 'generation')
            et.SubElement(this_gen_node, 'generation_number').text = str(gen)
            et.SubElement(this_gen_node, 'population_hungry').text = str(pred_out.popu(pred_species, hungry_only=True))

        yield prey_out, pred_out, gen

    sim_tree.write(filename + '.simu.xml', xml_declaration=True, pretty_print=True)

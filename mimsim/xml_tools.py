"""
write_xml(path, sim) -> None
load_sim(file_path, as_dict=False) -> mc.Simulation
"""

# builtin or external imports
import lxml.etree as et
# imports from this package
from mimsim import controller as mc
from mimsim import mimicry as mim


def validate_sim(tree: et.ElementTree):
    sim_schema_src = et.parse('../mimsim/rsc/simulation_specification.xsd')
    sim_schema = et.XMLSchema(sim_schema_src)
    sim_schema.assertValid(tree)
    return True


def _prey_from_root(root: et.Element) -> mim.PreyPool:
    prey_pool = mim.PreyPool()
    prey_root = root.find('prey_pool')
    for species in prey_root:
        prey_pool.append(
            species.find('spec_name').text,
            mim.Prey(
                popu=int(species.find('popu').text),
                phen=species.find('phen').text,
                size=float(species.find('size').text),
                camo=float(species.find('camo').text),
                pal=float(species.find('pal').text)
            )
        )
    return prey_pool


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
            mim.Predator(
                app=species.find('app').text,
                mem=int(species.find('mem').text),
                insatiable=bool(species.find('insatiable').text in ('true', '1')),
            ),
            int(species.find('popu').text)
        )
    return pred_pool


def load_pred_pool(file_path_in: str) -> mim.PredatorPool:
    sim_tree = et.parse(file_path_in)
    validate_sim(sim_tree)
    root = sim_tree.getroot()
    return _pred_from_root(root)


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


def _build_xml(sim: mc.Simulation):
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
    for pred_name, pred_obj in sim.pred_pool.list_all_reps():
        pred_elem = et.SubElement(pred_pool, 'pred_spec')
        et.SubElement(pred_elem, 'spec_name').text = pred_name
        et.SubElement(pred_elem, 'popu').text = str(sim.pred_pool.popu(pred_name))
        et.SubElement(pred_elem, 'app').text = str(pred_obj.app)
        et.SubElement(pred_elem, 'mem').text = str(pred_obj.mem)
        et.SubElement(pred_elem, 'insatiable').text = str(int(pred_obj.insatiable))

    return et.ElementTree(root)


def write_xml(destination_path: str, sim: mc.Simulation):  # TODO: add option for different title
    if not destination_path or destination_path[-1] != '/':
        destination_path += '/'
    data_tree = _build_xml(sim)
    data_tree.write(destination_path + sim.title + '.simu.xml', pretty_print=True)

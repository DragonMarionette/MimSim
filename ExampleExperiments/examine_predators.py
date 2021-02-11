from mimsim import controller as mc, xml_tools as xt

sim = xt.load_sim('examine_predators.simu.xml')

prey_out, predators_out = mc.one_gen(sim.prey_pool, sim.pred_pool, sim.encounters)

for prey_name, prey_obj in prey_out:
    print(f'Remaining population of species {prey_name} is {prey_obj.popu}.')

for pred_name, pred_list in predators_out:
    for individual in pred_list:
        print(f'\nIndividual of {pred_name} has following experiences:')
        for phen in individual.prefs:
            print(f'{phen}: {individual.prefs[phen]} giving a preference of {individual.get_pref(phen)}')

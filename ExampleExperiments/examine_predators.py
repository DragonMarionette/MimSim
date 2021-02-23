from mimsim import mimicry as mim, xml_tools as xt

sim = xt.load_sim('examine_predators.simu.xml')

prey_out, predators_out = mim.one_gen(sim.prey_pool, sim.pred_pool, sim.encounters)

for prey_name, prey_obj in prey_out:
    print(f'Remaining population of species {prey_name} is {prey_obj.popu}.')

for pred_name, pred_spec in predators_out:
    for i in range(len(pred_spec)):
        print(f'\nIndividual of {pred_name} ate {pred_spec[i].prey_eaten} prey, leaving it '
              f'{"hungry" if pred_spec.hungry(i) else "full"}. It has following experiences:')
        for phen in pred_spec[i].prefs:
            print(f'{phen}: {pred_spec[i].prefs[phen]} giving a preference of {pred_spec.get_pref(i, phen)}')

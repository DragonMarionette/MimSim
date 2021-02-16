"""
A minimal example of how to use mimsim.
Loads a Simulation from a Simulation XML (extension .simu.xml),
then writes the population of each prey species to simple_example.CSV,
then exports the simulation's parameters to a new Simulation XML.
"""


from mimsim import xml_tools as xt

sim = xt.load_sim('simple_example.simu.xml')
xt.write_desc('../ExampleExperiments/output/simple_example/', sim)
sim.run('../ExampleExperiments/output/simple_example/', verbose=True)

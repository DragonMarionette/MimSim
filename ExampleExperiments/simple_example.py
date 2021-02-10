"""
A minimal example of how to use mimsim.
Loads a Simulation from a properly-formatted XML,
then writes the population of each prey species to simple_example.CSV.
"""


from mimsim import xml_tools as xt

sim = xt.load_sim('simple_example.xml')
sim.run('../ExampleExperiments/output/simple_example/', verbose=True, make_xml=False)

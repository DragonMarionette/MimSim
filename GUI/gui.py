"""
GUI for Mimicry Simulator
"""

import sys
import ctypes
import os.path as pth
import platform
import PySimpleGUI as Sg
import webbrowser
from typing import Union, Tuple

import mimsim.controller as mc
import mimsim.mimicry as mim
import mimsim.xml_tools as xt

about_info = {
    'name': 'Mimicry Simulator (Beta)',
    'author': 'Dan Strauss (DragonMarionette)',
    'contributors': ['Emily Louden (deer-prudence)'],  # If you help, add yourself to this list!
    'version': '0.3.1',
    'date': '21 Feb. 2021',
    'license': 'Apache 2.0',
    'repo': 'https://github.com/DragonMarionette/MimSim'
}

# TODO: add option for graph of prey populations over time under certain circumstances (and other analysis tools?)

HEADER_FONT = ('Segoe UI Semilight', 14)
BODY_FONT = ('Segoe UI', 10)
BUTTON_W = 7
PREY_PRED_LISTBOX_SIZE = (56, 5)


def main():
    def make_simulation(for_export=False):  # Return mc.Simulation object initialized with the user's parameters
        if sim_window['-TITLE-'].get() == '':  # input validation checks
            alert('Simulation title cannot be blank. Please enter a title.')
            return False
        elif not valid_nonnegative_int(sim_window['-ENCOUNTERS-'].get()):
            alert('Number of encounters must be a nonnegative integer.')
            return False
        elif not valid_nonnegative_int(sim_window['-GENERATIONS-'].get()):
            alert('Number of generations must be a nonnegative integer.')
            return False
        elif not valid_nonnegative_int(sim_window['-REPETITIONS-'].get()):
            alert('Number of trials must be a nonnegative integer.')
            return False
        elif not prey_pool.popu():
            alert('No prey to simulate. Please add at least one species under the "Prey species" tab.')
            return False
        elif not pred_pool.popu():
            alert('No predators to simulate. Please add at least one species under the "predator species" tab.')
            return False
        elif output_path == '':
            alert('No output directory selected. Please select an output directory before running the simulation.')
            sim_window['-OUTPUT_PATH-'].click()
            return False
        else:
            xml_exists = pth.exists(output_path)
            csv_exists = pth.exists(output_folder + output_title + mc.CSV)
            overwrite_list = []
            if xml_exists:
                overwrite_list.append(output_path)
            if csv_exists and extension == mc.CSV and not for_export:
                overwrite_list.append(output_folder + output_title + mc.CSV)
            if overwrite_list:
                overwrite_alert_string = f"The following file{'s' * (len(overwrite_list) > 1)} will be overwritten:\n" \
                                         + '\n'.join(overwrite_list) + '\n\n OK to proceed?'
                if not Sg.popup_ok_cancel(overwrite_alert_string, title='Confirm') == 'OK':
                    return False
            return mc.Simulation(
                title=sim_window['-TITLE-'].get(),
                prey_pool=prey_pool,
                pred_pool=pred_pool,
                encounters=int(sim_window['-ENCOUNTERS-'].get()),
                generations=int(sim_window['-GENERATIONS-'].get()),
                repetitions=int(sim_window['-REPETITIONS-'].get()),
                repopulate=sim_window['-REPOPULATE-'].get()
            )

    def update_prey_list():  # Make prey listbox match prey_dict
        sim_window['-PREY_LIST-'].update(prey_pool.pretty_list())

    def update_pred_list():  # Make predator listbox match prey_dict
        sim_window['-PRED_LIST-'].update(pred_pool.pretty_list())

    def enable_prey_buttons(boolean):
        disabled = not boolean
        sim_window['-EDIT_PREY-'].update(disabled=disabled)
        sim_window['-DUP_PREY-'].update(disabled=disabled)
        sim_window['-DEL_PREY-'].update(disabled=disabled)

    def enable_pred_buttons(boolean):
        disabled = not boolean
        sim_window['-EDIT_PRED-'].update(disabled=disabled)
        sim_window['-DUP_PRED-'].update(disabled=disabled)
        sim_window['-DEL_PRED-'].update(disabled=disabled)

    prey_pool = mim.PreyPool()  # pool of all prey species user intends for simulation
    pred_pool = mim.PredatorPool()  # pool of all predator species user intends simulation

    Sg.theme('LightGreen2')
    if int(platform.release()) >= 8:  # If possible, make Mimicry Simulator DPI-aware
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

    # PySimpleGui defaults to the smallest resolution available in an ICO for use in the title bar.
    # This hacky workaround chooses a single-res ICO file which is approximately appropriate for user's screen.
    screen_dim = max(ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
    if screen_dim <= 1080:
        viceroy = '../GUI/rsc/Viceroy16.ico'
    elif screen_dim < 3840:
        viceroy = '../GUI/rsc/Viceroy32.ico'
    else:
        viceroy = '../GUI/rsc/Viceroy48.ico'
    Sg.set_global_icon(viceroy)

    layout = make_full_layout()

    sim_window = Sg.Window(title='Mimicry Simulator', layout=layout, finalize=True)
    Sg.set_options(button_element_size=(BUTTON_W, 1), slider_orientation='h', use_ttk_buttons=True, font=BODY_FONT)

    # include ['-ENCOUNTERS-', '-GENERATIONS-', '-REPETITIONS-'] below to extend all to full width
    for field in ['-TITLE-']:
        sim_window[field].expand(expand_x=True, expand_y=False, expand_row=False)

    output_path = ''
    output_folder = ''
    output_title = ''
    extension = mc.CSV

    # Loop to listen and handle events
    while True:
        event, values = sim_window.read()

        # File menu events
        if event == 'Import...':
            xml_in = Sg.popup_get_file('Select local simulation XML',
                                       title='import', file_types=(('Simulation Files', '*.simu.xml'),))
            if xml_in:
                if Sg.popup_ok_cancel('This will overwrite any parameters you\'ve already entered. Proceed?',
                                      title='Confirm') == 'OK':
                    # try:
                    sim_in = xt.load_sim(xml_in)
                    # Meta properties
                    sim_window['-TITLE-'].update(value=sim_in.title)
                    sim_window['-ENCOUNTERS-'].update(value=sim_in.encounters)
                    sim_window['-GENERATIONS-'].update(value=sim_in.generations)
                    sim_window['-REPETITIONS-'].update(value=sim_in.repetitions)
                    sim_window['-REPOPULATE-'].update(value=sim_in.repopulate)

                    # Prey and pred properties
                    prey_pool = sim_in.prey_pool
                    update_prey_list()
                    pred_pool = sim_in.pred_pool
                    update_pred_list()
                    # except xt.et.XMLSyntaxError:
                    #     error(f'The file {xml_in} is not a valid simulation file. Please choose another or enter '
                    #           f'simulation parameters by hand.')
                    # except AssertionError:
                    #     error(f'The file {xml_in} is not a valid simulation file. Please choose another or enter '
                    #           f'simulation parameters by hand.')
                    # except:
                    #     error(f'And unknown error occurred while reading the file {xml_in}.')
        elif event == 'Export...':
            sim = make_simulation(for_export=True)
            if sim:
                try:
                    xt.write_desc(sim, output_path)
                    Sg.popup(f"Success. Simulation parameters exported to "
                             f"{output_path}.",
                             title='Success')
                except:
                    error('An unknown error occurred. Try checking that you have permission to write to the selected '
                          'directory and you are not trying to write to a file that is open in another application.')
        elif event == 'Exit':  # TODO: make this work when the user tries to use native title bar 'X' button
            if Sg.popup_ok_cancel('Are you sure you want to exit? You will lose any unsaved parameters.') == 'OK':
                sim_window.close()
                break
        # Help menu events
        elif event == 'How to use Mimicry Simulator':
            webbrowser.open(about_info['repo'] + '#readme', new=2)
        elif event == 'About':
            about()

        # Prey-related events
        elif event == '-PREY_LIST-':
            # Offer to edit, duplicate, delete prey species only if one is selected
            if not values['-PREY_LIST-']:
                enable_prey_buttons(False)
            else:
                enable_prey_buttons(True)
        elif event == '-NEW_PREY-':
            new_prey_name, new_prey_obj = prey_dialogue()
            while new_prey_name in prey_pool.names:
                alert('Name cannot be shared with another prey species.')
                new_prey_name, new_prey_obj = prey_dialogue(new_prey_name + '_', new_prey_obj)
            if new_prey_obj is not None:
                prey_pool.add(new_prey_name, new_prey_obj)
                update_prey_list()
            sim_window['-PREY_LIST-'].set_value([])
            enable_prey_buttons(False)
        elif event == '-EDIT_PREY-':
            old_prey_name = prey_pool.names[sim_window['-PREY_LIST-'].get_indexes()[0]]  # current selection
            new_prey_name, new_prey_obj = prey_dialogue(old_prey_name, prey_pool[old_prey_name])
            while new_prey_name != old_prey_name and new_prey_name in prey_pool.names:
                alert('Name cannot be shared with another prey species.')
                new_prey_name, new_prey_obj = prey_dialogue(new_prey_name + '_', new_prey_obj)
            if new_prey_obj is not None:
                prey_pool.remove(old_prey_name)
                prey_pool.add(new_prey_name, new_prey_obj)
                update_prey_list()
            sim_window.bring_to_front()
            sim_window['-PREY_LIST-'].set_value([])
            enable_prey_buttons(False)
        elif event == '-DUP_PREY-':
            prey_to_copy_name = prey_pool.names[sim_window['-PREY_LIST-'].get_indexes()[0]]  # current selection
            new_prey_name, new_prey_obj = prey_dialogue(prey_to_copy_name + '_copy', prey_pool[prey_to_copy_name])
            while new_prey_name in prey_pool.names:
                alert('Name cannot be shared with another prey species.')
                new_prey_name, new_prey_obj = prey_dialogue(new_prey_name + '_', new_prey_obj)
            if new_prey_obj is not None:
                prey_pool.add(new_prey_name, new_prey_obj)
                update_prey_list()
            sim_window['-PREY_LIST-'].set_value([])
            enable_prey_buttons(False)
        elif event == '-DEL_PREY-':
            prey_unwanted_name = prey_pool.names[sim_window['-PREY_LIST-'].get_indexes()[0]]  # current selection
            if Sg.popup_ok_cancel(f'Are you sure you want to delete prey species "{prey_unwanted_name}"?',
                                  title='Confirm') == 'OK':
                prey_pool.remove(prey_unwanted_name)
                update_prey_list()
            sim_window['-PREY_LIST-'].set_value([])
            enable_prey_buttons(False)

        # Predator-related events
        elif event == '-PRED_LIST-':
            # Offer to edit, duplicate, delete predator species only if one is selected
            if not values['-PRED_LIST-']:
                enable_pred_buttons(False)
            else:
                enable_pred_buttons(True)
        elif event == '-NEW_PRED-':
            new_pred_name, new_pred_obj = pred_dialogue()
            while new_pred_name in pred_pool.names:
                alert('Name cannot be shared with another predator species.')
                new_pred_name, new_pred_obj = pred_dialogue(new_pred_name + '_', new_pred_obj)
            if new_pred_obj is not None:
                pred_pool.add(new_pred_name, new_pred_obj)
                update_pred_list()
            sim_window['-PRED_LIST-'].set_value([])
            enable_pred_buttons(False)
        elif event == '-EDIT_PRED-':
            old_pred_name = pred_pool.names[sim_window['-PRED_LIST-'].get_indexes()[0]]  # current selection
            new_pred_name, new_pred_obj = pred_dialogue(old_pred_name, pred_pool[old_pred_name])
            while new_pred_name != old_pred_name and new_pred_name in pred_pool.names:
                alert('Name cannot be shared with another predator species.')
                new_pred_name, new_pred_obj = pred_dialogue(new_pred_name + '_', new_pred_obj)
            if new_pred_obj is not None:
                pred_pool.remove(old_pred_name)
                pred_pool.add(new_pred_name, new_pred_obj)
                update_pred_list()
            sim_window.bring_to_front()
            sim_window['-PRED_LIST-'].set_value([])
            enable_pred_buttons(False)
        elif event == '-DUP_PRED-':
            pred_to_copy_name = pred_pool.names[sim_window['-PRED_LIST-'].get_indexes()[0]]  # current selection
            new_pred_name, new_pred_obj = pred_dialogue(pred_to_copy_name + '_copy', pred_pool[pred_to_copy_name])
            while new_pred_name in pred_pool.names:
                alert('Name cannot be shared with another predator species.')
                new_pred_name, new_pred_obj = pred_dialogue(new_pred_name + '_', new_pred_obj)
            if new_pred_obj is not None:
                pred_pool.add(new_pred_name, new_pred_obj)
                update_pred_list()
            sim_window['-PRED_LIST-'].set_value([])
            enable_pred_buttons(False)
        elif event == '-DEL_PRED-':
            pred_unwanted_name = pred_pool.names[sim_window['-PRED_LIST-'].get_indexes()[0]]  # current selection
            if Sg.popup_ok_cancel(f'Are you sure you want to delete predator species "{pred_unwanted_name}"?',
                                  title='Confirm') == 'OK':
                pred_pool.remove(pred_unwanted_name)
                update_pred_list()
            sim_window['-PRED_LIST-'].set_value([])
            enable_pred_buttons(False)

        # Execution-related events
        elif event == '-OUTPUT_PATH-':
            output_path = values['-OUTPUT_PATH-']
            output_folder = '/'.join(output_path.split('/')[:-1]) + '/'
            output_title = output_path.split('/')[-1][:-9]
            sim_window['-FILENAME_READOUT-'].update(value=output_path)
        elif event == mc.XML:
            extension = mc.XML
        elif event == mc.CSV:
            extension = mc.CSV
        elif event == '-RUN-':
            sim = make_simulation(for_export=False)
            if sim:
                verbose = sim_window['-VERBOSE-'].get()
                execution_dialog(output_folder, output_title, sim, verbose, extension=extension)

        elif event == Sg.WIN_CLOSED:
            break


def make_full_layout():
    return [
        [Sg.Menu([['File', ['Import...', 'Export...', 'Exit']], ['Help', ['How to use Mimicry Simulator', 'About']]])],
        [Sg.Text('Simulation Parameters', font=HEADER_FONT)],
        [Sg.TabGroup(layout=[[make_meta_tab(), make_prey_tab(), make_pred_tab()]])],
        [Sg.Text()],  # A line of space. using Sg.Text here instead of Sg.Sizer because Sizer height depends on DPI
        [Sg.Text('Execution', font=HEADER_FONT)],
        [Sg.Text('Output type:')],
        [Sg.Radio('CSV + descriptive *.simu.xml', 'output_selection', key=mc.CSV, enable_events=True, default=True)],
        [Sg.Radio('Full results in *.simu.xml', 'output_selection', key=mc.XML, enable_events=True, default=False)],
        [Sg.HorizontalSeparator()],
        [Sg.Checkbox(key='-VERBOSE-', text='Include all generations in output',
                     tooltip='Output a row for each  generation of each trial; if turned off, only the last '
                             'generation of each trial is used')],
        [Sg.Text('Output destination:',
                 tooltip='Where to save CSV and/or XML output'),
         Sg.Text(key='-FILENAME_READOUT-', text='No output location selected', auto_size_text=False,
                 tooltip='Where to save CSV and XML output'), ],
        [Sg.FileSaveAs(key='-OUTPUT_PATH-', button_text='Change', size=(BUTTON_W, 1), enable_events=True,
                       tooltip='Change output directory', file_types=(('Simulation Files', '*.simu.xml'),)), ],
        [Sg.HorizontalSeparator()],
        [Sg.Button(key='-RUN-', button_text='Run', size=(2 * BUTTON_W, 1),
                   tooltip='Run the simulation')]
    ]


def make_meta_tab():
    text_size = (20, None)
    field_size = (8, 1)
    layout = [
        [Sg.Text(text='Simulation title:', size=text_size, justification='r',
                 tooltip='Name for the simulation'),
         Sg.Input(key='-TITLE-', size=field_size,
                  tooltip='Name for the simulation')],
        [Sg.Text(text='Number of trials:', size=text_size, justification='r',
                 tooltip='Number of independent trials to simulate'),
         Sg.Input(key='-REPETITIONS-', size=field_size,
                  tooltip='Number of independent trials to simulate')],
        [Sg.Text(text='Number of encounters:', size=text_size, justification='r',
                 tooltip='Number of predator-prey encounters to simulate per generation.\n'
                         'Advised to keep this below 10000 for multi-generation simulations'),
         Sg.Input(key='-ENCOUNTERS-', size=(19, 1),
                  tooltip='Number of predator-prey encounters to simulate per generation.\n'
                          'Advised to keep this below 10000 for multi-generation simulations')],
        [Sg.Text(text='Number of generations:', size=text_size, justification='r',
                 tooltip='Number of generations to simulate'),
         Sg.Input(key='-GENERATIONS-', size=field_size,
                  tooltip='Number of generations to simulate')],
        [Sg.Checkbox(key='-REPOPULATE-', text='Repopulate before recording data',
                     tooltip='Output populations at the start of the next '
                             'generation rather than the end of the previous one')]
    ]

    return Sg.Tab('General parameters', layout=layout)


def make_prey_tab():
    layout = [
        [Sg.Listbox([], key='-PREY_LIST-', size=PREY_PRED_LISTBOX_SIZE,
                    select_mode=Sg.LISTBOX_SELECT_MODE_SINGLE, enable_events=True)],
        [Sg.Button(key='-NEW_PREY-', button_text='Add species...', size=(2 * BUTTON_W, 1))],
        [Sg.Button(key='-EDIT_PREY-', button_text='Edit...', size=(BUTTON_W, 1),
                   disabled=True, disabled_button_color=('#cccccc', '#a7bba8')),
         Sg.Button(key='-DUP_PREY-', button_text='Duplicate...', size=(2 * BUTTON_W, 1),
                   disabled=True, disabled_button_color=('#cccccc', '#a7bba8')),
         Sg.Button(key='-DEL_PREY-', button_text='Delete', size=(BUTTON_W, 1),
                   disabled=True, disabled_button_color=('#cccccc', '#a7bba8'))]
    ]

    return Sg.Tab('Prey species', layout)


def make_pred_tab():
    layout = [
        [Sg.Listbox([], key='-PRED_LIST-', size=PREY_PRED_LISTBOX_SIZE,
                    select_mode=Sg.LISTBOX_SELECT_MODE_SINGLE, enable_events=True)],
        [Sg.Button(key='-NEW_PRED-', button_text='Add species...', size=(2 * BUTTON_W, 1))],
        [Sg.Button(key='-EDIT_PRED-', button_text='Edit...', size=(BUTTON_W, 1),
                   disabled=True, disabled_button_color=('#cccccc', '#a7bba8')),
         Sg.Button(key='-DUP_PRED-', button_text='Duplicate...', size=(2 * BUTTON_W, 1),
                   disabled=True, disabled_button_color=('#cccccc', '#a7bba8')),
         Sg.Button(key='-DEL_PRED-', button_text='Delete', size=(BUTTON_W, 1),
                   disabled=True, disabled_button_color=('#cccccc', '#a7bba8'))]
    ]

    return Sg.Tab('Predator species', layout)


def prey_dialogue(prey_in_name=None, prey_in=None) -> Union[Tuple[str, mim.Prey], Tuple[None, None]]:
    edit = prey_in is not None
    text_size = (12, 1)
    field_size = (25, 1)
    layout = [
        [Sg.Text(text='Species name:', size=text_size,
                 tooltip='Name for the prey species'),
         Sg.Input(key='spec_name', default_text=prey_in_name if edit else '', size=field_size,
                  tooltip='Name for the prey species')],
        [Sg.Text(text='Population:', size=text_size,
                 tooltip='Number of individuals of this species in the first generation'),
         Sg.Input(key='popu', default_text=prey_in.popu if edit else '', size=field_size,
                  tooltip='Number of individuals of this species in the first generation')],
        [Sg.Text(text='Phenotype:', size=text_size,
                 tooltip='String that must match between species mimicking each other'),
         Sg.Input(key='phen', default_text=prey_in.phen if edit else '', size=field_size,
                  tooltip='String that must match between species mimicking each other')],
        [Sg.Text(text='Size:', size=text_size,
                 tooltip='How filling an individual of the species is'),
         Sg.Input(key='size', default_text=prey_in.size if edit else '', size=field_size,
                  tooltip='How filling an individual of the species is')],
        # Sliders
        [Sg.Text(text='Camouflage:', size=text_size,
                 tooltip='Camouflage ability of the species, from 0 (impossible '
                         'for predator to see) to 1 (guaranteed visible)'),
         Sg.Text('{:.2f}'.format(prey_in.camo if edit else 0), key='-CAMO_TEXT-',
                 justification='c', size=(4, 1), background_color='#FDFFF7', relief=Sg.RELIEF_SUNKEN)],
        [Sg.Slider(key='camo', range=(0, 1), resolution=0.05, tick_interval=1, size=(24, 18),
                   default_value=prey_in.camo if edit else 0, disable_number_display=True, enable_events=True,
                   tooltip='Camouflage ability of the species, from 0 '
                           '(impossible for predator to see) to 1 (guaranteed visible)')],
        [Sg.Text(text='Palatability:', size=text_size,
                 tooltip='How edible the species is, from 0 (very unpalatable) to 1 (totally palatable)'),
         Sg.Text('{:.2f}'.format(prey_in.pal if edit else 1), key='-PAL_TEXT-',
                 justification='c', size=(4, 1), background_color='#FDFFF7', relief=Sg.RELIEF_SUNKEN)],
        [Sg.Slider(key='pal', range=(0, 1), resolution=0.05, tick_interval=1, size=(24, 18),
                   default_value=prey_in.pal if edit else 1, disable_number_display=True, enable_events=True,
                   tooltip='How edible the species is, from 0 (very unpalatable) to 1 (totally palatable)')],
        [Sg.Text()],
        [Sg.Button(button_text='Use this prey species', key='-ADD_PREY-', size=(3 * BUTTON_W, 1),
                   tooltip='Add prey species with the above parameters'),
         Sg.Button(button_text='Cancel', key='-CANCEL_PREY-', size=(BUTTON_W, 1),
                   tooltip='Discard these edits')]
    ]

    prey_window = Sg.Window(title='Edit Prey Species', layout=layout, use_ttk_buttons=True,
                            text_justification='r', font=BODY_FONT, modal=True, finalize=True)
    prey_window['camo'].expand(expand_x=True)
    prey_window['pal'].expand(expand_x=True)

    while True:
        event, values = prey_window.read()
        if event == '-ADD_PREY-':
            if prey_window['spec_name'].get() == '':
                alert('Prey name cannot be empty. Please enter a valid name.')
            elif not valid_nonnegative_int(prey_window['popu'].get()):
                alert('Prey population must be a positive integer.')
            elif not valid_positive_float(prey_window['size'].get()):
                alert('Prey size must be a positive number.')
            else:  # Valid prey creation/edit
                prey_window.close()
                return (prey_window['spec_name'].get(),
                        mim.Prey(popu=prey_window['popu'].get(), phen=prey_window['phen'].get(),
                                 size=prey_window['size'].get(), camo=values['camo'], pal=values['pal']))
        elif event == 'camo':
            prey_window['-CAMO_TEXT-'].update(value='{:.2f}'.format(values['camo']))
        elif event == 'pal':
            prey_window['-PAL_TEXT-'].update(value='{:.2f}'.format(values['pal']))
        elif event == '-CANCEL_PREY-' or event == Sg.WINDOW_CLOSED:
            prey_window.close()
            return None, None


def pred_dialogue(pred_in_name=None, pred_obj_in=None) -> Union[Tuple[str, mim.PredatorSpecies], Tuple[None, None]]:
    edit = pred_obj_in is not None
    text_size = (12, None)
    field_size = (25, None)
    layout = [
        [Sg.Text(text='Species name:', size=text_size,
                 tooltip='Name for the predator species'),
         Sg.Input(key='spec_name', default_text=pred_in_name if edit else '', size=field_size,
                  tooltip='Name for the predator species')],
        [Sg.Text(text='Population:', size=text_size,
                 tooltip='Number of individuals of this species'),
         Sg.Input(key='popu', default_text=pred_obj_in.popu if edit else '', size=field_size,
                  tooltip='Number of individuals of this species in the first generation')],
        [Sg.Text(text='Appetite:', size=text_size,
                 tooltip='Maximum amount of prey to eat before ceasing to pursue further prey items.'
                         'Leave blank for maximum possible appetite.'),
         Sg.Input(key='app', default_text=pred_obj_in.app if edit else '', size=field_size,
                  tooltip='Maximum amount of prey to eat before ceasing to pursue further prey items.'
                          'Leave blank for maximum possible appetite.')],
        [Sg.Text(text='Memory:', size=text_size,
                 tooltip='How many past experiences with a given phenotype contribute to the '
                         'predator\'s preferences. Leave blank for maximum possible memory.'),
         Sg.Input(key='mem', default_text=pred_obj_in.mem if edit else '', size=field_size,
                  tooltip='How many past experiences with a given phenotype contribute to the predator\'s '
                          'preferences. Leave blank for maximum possible memory.')],
        [Sg.Checkbox(text='Insatiable', key='insatiable', default=pred_obj_in.insatiable if edit else True,
                     tooltip='When checked, predator remains equally likely to pursue a given prey item regardless '
                             'how much appetite it has left. Predator will still stop eating once totally full.'), ],
        [Sg.Button(button_text='Use this predator species', key='-ADD_PRED-', size=(4 * BUTTON_W, 1),
                   tooltip='Add predator species with the above parameters'),
         Sg.Button(button_text='Cancel', key='-CANCEL_PRED-', size=(BUTTON_W, 1),
                   tooltip='Discard these edits')]
    ]

    pred_window = Sg.Window(title='Edit Predator Species', layout=layout, use_ttk_buttons=True,
                            text_justification='r', font=BODY_FONT, modal=True, finalize=True)

    while True:
        event, values = pred_window.read()
        if event == '-CANCEL_PRED-' or event == Sg.WINDOW_CLOSED:
            pred_window.close()
            return None, None
        elif event == '-ADD_PRED-':
            if pred_window['spec_name'].get() == '':
                alert('Predator name cannot be empty. Please enter a valid name.')
            elif not valid_nonnegative_int(pred_window['popu'].get()):
                alert('Population must be a positive integer.')
            else:  # Valid predator creation/edit
                app_valid = valid_nonnegative_int(pred_window['app'].get())
                mem_valid = valid_nonnegative_int(pred_window['mem'].get())
                app = pred_window['app'].get() if app_valid else int(sys.maxsize)
                mem = pred_window['mem'].get() if app_valid else int(sys.maxsize)
                if not (app_valid and mem_valid):
                    alert(f"{'Appetite' if mem_valid else 'Memory' if app_valid else 'Appetite and memory both'} "
                          f"defaulted to the maximum possible value.")

                pred_window.close()
                return (pred_window['spec_name'].get(),
                        mim.PredatorSpecies(app=app, mem=mem,
                                            insatiable=pred_window['insatiable'].get(),
                                            popu=int(pred_window['popu'].get())
                                            )
                        )


def execution_dialog(folder, title, sim, verbose, extension):
    as_csv = extension == mc.CSV
    progress_text = Sg.Text('Running simulation... 0% complete', justification='c')
    progress_bar = Sg.ProgressBar(100, orientation='h', size=(60, 48))
    # cancel_button = Sg.Button('Cancel', key='-CANCEL_EXEC-', size=(BUTTON_W, 1))
    layout = [
        [progress_text],
        [Sg.Text()],
        [progress_bar],
        [Sg.Text()],
        # [cancel_button]
    ]
    exec_window = Sg.Window('Running', layout, element_justification='c', modal=True, finalize=True,
                            disable_close=True)
    total_rows = sim.repetitions * ((sim.generations + int(sim.repopulate)) if verbose else 1)
    row_count = 0
    try:
        for _ in sim.iter_run(folder, alt_title=title, verbose=verbose, output=mc.CSV if as_csv else mc.XML):
            row_count += 1
            progress = int(100 * row_count / total_rows)
            progress_bar.update(progress)
            progress_text.update(f'Running simulation... {progress}% complete')
        if as_csv:
            xt.write_desc(sim, folder, alt_title=title)
        Sg.popup(f"Success. Simulation saved to {folder + title + extension}.",
                 title='Success')
    except:
        error('An unknown error occurred. Try checking that you have permission to write to the selected directory '
              'and you are not trying to write to a file that is open in another application.')
    finally:
        exec_window.close()


def about():
    layout = [
        [Sg.Text(about_info['name'], font=HEADER_FONT)],
        [Sg.Text(f"Version: {about_info['version']}")],
        [Sg.Text(f"Released on: {about_info['date']}")],
        [Sg.Text(f"Original author: {about_info['author']}")],
        [Sg.Text(f"Other contributors: {', '.join(about_info['contributors'])}")],
        [Sg.Text(f"Released under the {about_info['license']} License")],
        [Sg.Text()],
        [Sg.Image(filename='../GUI/rsc/Viceroy256.png', key='-VICEROY-', enable_events=True)],
        [Sg.Text()],
        [Sg.Button('Source on Github', key='-SOURCE-', size=(3 * BUTTON_W, 1)),
         Sg.Sizer(h_pixels=48),
         Sg.Button(about_info['license'], key='-LICENSE-', size=(2 * BUTTON_W, 1))]

    ]
    about_win = Sg.Window(title='Edit Predator Species', layout=layout,
                          font=BODY_FONT, modal=True, finalize=True, element_justification='c')
    while True:
        event, values = about_win.read()
        if event == '-SOURCE-':
            webbrowser.open(about_info['repo'])
        elif event == '-LICENSE-':
            webbrowser.open('https://www.apache.org/licenses/LICENSE-2.0')
        elif event == '-VICEROY-':
            webbrowser.open('https://en.wikipedia.org/wiki/Viceroy_(butterfly)')
        elif event == Sg.WINDOW_CLOSED:
            break


def valid_nonnegative_int(value):
    try:
        return int(value) >= 0
    except ValueError:
        return False


def valid_positive_float(value):
    try:
        return float(value) > 0
    except ValueError:
        return False


def error(text):
    return Sg.popup(text, title='Error')


def alert(text):
    return Sg.popup(text, title='Alert')


if __name__ == '__main__':
    main()

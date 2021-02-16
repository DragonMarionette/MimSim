# MimSim

Python package and GUI for simulating Batesian and Müllerian mimicry, among other things

## Using MimSim

The easiest way to get started is to intall and run `gui.py`. Proper documentation on the `mimsim` package will come when it's ready for release on PyPI.

### Dependencies

* [PySimpleGui](https://pypi.org/project/PySimpleGUI/) and tkinter (only needed for `gui.py`)
* [lxml](https://lxml.de/)

tkinter is installed alongside most distributions of Python. The other dependencies can abe installed as follows:
```
pip install PySimpleGUI
pip install lxml
```

### Installation

Currently, mimsim is not available for install any way other than manually dropping `mimsim` into your project. Since we're under alpha development, features and function names are changing too often to effectivey offer backwards compatibility. A `pip` installable version is in the works.

To test your installation, try running one of the sample projects under the [Example Experiments](ExampleExperiments)!

## Built With

* [Python 3.9](https://www.python.org/downloads/release/python-391/)
* [PySimpleGui (tkinter version)](https://pypi.org/project/PySimpleGUI/) - Platform for graphical user interface

## Contributing

Currently, there is no protocol for contribution. But if you have an idea, fork this repo!

## Versioning

...is currently not much of a thing. This project is in alpha and may never leave it, so versions start from 0.1.0. Bugfixes increment the sub-subversion (e.g. 0.1.1), while new or updated features mark a new subversion (e.g. 0.2.0).

## Author

* **Dan Strauss** - *Concept and initial work* - [DragonMarionette](https://github.com/Dragonmarionette)

### Other Contributors
* **Anoush Khan** - *Bughunting and being a rubber duck* - [doubleaykay](https://github.com/doubleaykay)
* **Emily Louden** - *Work towards an executable version* - [deer-prudence](https://github.com/deer-prudence)

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details

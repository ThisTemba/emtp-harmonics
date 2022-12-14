# EMTP Harmonic Table Reader

Usage:

1. Download `main.py`
2. Ensure you have the python packages `numpy`, `lxml`, and `matplotlib` installed
3. Run as follows: `python main.py [path to input html file]`

It is easiest is if the html file is in the same directory as `main.py`. This way, the path is just the filename of the html file.

## Requirements

You will need to install

## harmonic_table_reader.py

This program reads the HTML output of the EMTP simulation
EMTP file specified in the command line (no input check in program)
The HTML file is huge, and this program takes about 3 minutes to run
Program assumes only one node voltage table per solution frequency
Output: txt file of dictionary with key=solution frequency,
and value: list of pairs matching EMTP final node to voltage
e.g. { 60 Hz: [(TPSS1_a, 10 V), (TPSS1_b, 11V), ...]}
This program uses BeautifulSoup to parse and search htmls.
U. Monaghan Sept 2020

## Updates:

- 5-13-2022 - Changed the buses we are analyzing
- 5-16-2022 - Cut out the THD calc function, so program only exports the bus votages into a csv
- 5-18-2022 - Added THD and IHD calculations, and added histogram plotting [by Temba Mateke]

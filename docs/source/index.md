% Super-auto-comb documentation master file, created by
% sphinx-quickstart on Thu Sep  5 10:54:15 2024.
% You can adapt this file completely to your liking, but it should at least
% contain the root `toctree` directive.

# Super-auto-comb documentation

This is the documentation for Super-auto-comb.


Super-auto-comb is a python script for processing optical comb data useful for Time\&Frequency science in the optical domain.
Super-auto-combs outputs data in the ROCIT format, useful for comparison using optical fibre links, developed for the [EMPIR project ROCIT](http://empir.npl.co.uk/rocit/) and for the [European Partnership on Metrology Project TOCK](https://www.ptb.de/epm2022/tock/home).
See also:
- <https://github.com/INRIM/tintervals>
- <https://github.com/INRIM/optical-link-data-format>

Development is at 
- <https://github.com/INRIM/super-auto-comb>


This package is not yet on Pypi.


## Basic usage
Install using pipx directly from Github:

`$ pipx install git+https://github.com/INRIM/super-auto-comb.git`

Verify the installation and the available Command Line Interface (CLI) arguments with:

`$ super-auto-comb --help`

To simplify the inputs of CLI arguments, prepare a `super-auto-comb.txt` file in the folder where you want to process comb data similar to:

    do = [my_do1, my_do2]
    start = 2023-02-24
    stop = 2023-04-29
    dir = ./Outputs
    fig-dir = ./Outputs/Figures
    comb-dir = your-path-to-comb-data
    setup-dir = your-path-to-comb-setup-files

and invoke `$ super-auto-comb` to process the data.

For repeating data processing day-after-day you can run `$ super-auto-comb --auto` to process the data.
The appropriate start date will be read/saved in the file `super-auto-last.txt` for subsequent use. 

## Tracking comb setups

Super-auto-comb read files  that describe designed oscillators (DO) and combs, and how these setups change dover time. For both DOs and combs information are stored line by line. Each line should start with a datetime in ISO format (e.g., `2021-10-28T16:20:21`, local time is ok). It is intended that the data on the line applies from that date to the date on the next line (if any). Changes should be tracked by adding more lines. See the `tests/samples` folder for examples. If super-auto-comb is invoked by `super-auto-comb --do my_do`, it will look for a file `my_do.dat`. If this file has `my_comb` under the `comb` column, super-auto-comb will then look for a `my_comb.dat` file.

### Comb files
The columns of these files should be:

| Column name | Data type | Description |
|-------------|-----------|-------------|
| datetime    | ISO       | Datetime of the change | 
| maser       | string    | Reference maser |
| frep        | float     | Repetition rate in Hz |
| f0          | float     | Offset frequency in Hz (with sign) |
| counter_f0  | int       | Counter channel counting f0 | 

### Designed oscillators files

DO files are more complex, and should contain all information required to transform from counted frequencies to absolute frequencies, supplemented  by the details of the measurement on the counter (divided in counter1 and counter2 for double counting)


| Column name | Data type | Description |
|-------------|-----------|-------------|
| datetime    | ISO       | Datetime of the change |
| comb        | string    | Comb used for the measurement `comb1` or `comb2`    | 
| physical    | string    | Physical oscillator    |
| nominal     | string    | Nominal frequency in Hz (should be a string in quotes, e.g. `'518_295_836_590_863.6'`)|
| kscale      | float     | Frequency scaling (typically 1, 2 in case of SHG) |
| foffset     | float     | Offset frequency in Hz from the counted beatnote |
| N           | int       | comb tooth |
| fbeat_sign  | int       | sign of the physical beatnote |
| f0_scale    | int       | scaling of f0 (typically 1, 2 for measurements with visible branch) |
| counter1    | int       | Counter channel |
| flo1        | float     | Local oscillator frequency in Hz (with sign)) |
| min1        | float     | Minimum acceptable counted frequency |
| max1        | float     | Maximum acceptable counted frequency |
| counter2    | int       | Counter channel |
| flo2        | float     | Local oscillator frequency in Hz (with sign)) |
| min2        | float     | Minimum acceptable counted frequency |
| max2        | float     | Maximum acceptable counted frequency |


The math is:

- $f_N = f_{rep} N + f_0 \times scale_{f_0}$

- $f_{beat} = sign_{beat} \times |f_{counter} + f_{lo}|$

- $f_{abs} = k_{scale} \times (f_N + f_{beat}) + f_{offset}$

$f_{abs}$ should be close to the nominal frequency.
If DOs get disconnected, then a line with only the datetime of disconnection can be used.


## Acknowledgments
This work has received funding from the European Partnership on Metrology, co-financed by the European Union’s Horizon Europe Research and Innovation Programme and by the Participating States, under grant number 22IEM01 TOCK.

![badge](./Acknowledgement%20badge.png)

## Authors

(c) 2023-2024 Marco Pizzocaro - Istituto Nazionale di Ricerca Metrologica (INRIM)



```{toctree}
:caption: 'Contents:'
:maxdepth: 2
```

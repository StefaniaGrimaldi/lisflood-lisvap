## Running LISVAP

There is no difference in running LISVAP in a Docker container or directly by source code. You need to prepare your XML settings file and pass it as argument.

The layout of the settings file is detailed in [LISVAP Settings file](/lisflood-lisvap/3_2_LISVAP_settingsfile/).
Along with source code, you will have a [settings_tpl.xml](https://raw.githubusercontent.com/ec-jrc/lisflood-lisvap/master/settings_tpl.xml) file to use as a template to start writing your own settings.

### ... in a Docker container

For Docker, first thing is to map folders using volumes as in the table below. Those paths are configured in the XML settings file that you submit to LISVAP.


   **Table:** *Mapping volumes to run LISVAP in Docker*
   

| Volume                            |  Example of folder on your system |  Correspondant folder in Docker | Mapping                        |
| --------------------------------- | --------------------------------- | ------------------------------- | ------------------------------ |
| Folder with the XML settings file | ./                                | /tmp                            | -v `pwd`/:/tmp                 |
| Path containing input dataset     | /DATA/Meteo/EMA                   | /input                          | -v /DATA/Meteo/EMA:/input      |
| Path for output                   | /DATA/Lisvap/out                  | /output                         | -v /DATA/Lisvap/out:/output    |

Then, the correspondant Docker command (in Linux) to run the LISVAP container, given mysettings.xml is in current folder, will be:

```bash
docker pull efas/lisvap:latest
docker run -v $(pwd)/:/tmp -v /DATA/Meteo/2017/EMA:/input -v /DATA/Lisvap/out:/output efas/lisvap:latest /tmp/mysettings.xml
```

### ... as an installed python module

If you installed lisvap in your python environment using pip tool, you will have a binary called `lisvap` in your path.

```bash
pip install lisflood-lisvap
lisvap mysettings.xml -v -t
```

### ... from source code

Once all dependencies are installed, you can run the model using python (2.7 version) interpreter[^1]:

```bash
cd src/
python lisvap/lisvap1.py mysettings.xml -v -t
```
[^1]: As previously said, we strongly recommend using an isolated python virtualenv.

If you just type `python lisvap1.py` you will see the usage dialogue:

 ```console
LisvapPy - Lisvap (Global) using pcraster Python framework
Authors:  Peter Burek, Johan van der Knijff, Ad de Roo
Version:  Version: 0.2
Date:  10/04/2019
Status:  Development

    Arguments list:
    settings.xml     settings file

    -q --quiet       output progression given as .
    -v --veryquiet   no output progression is given
    -l --loud        output progression given as time step, date and discharge
    -c --checkfiles  input maps and stack maps are checked, output for each input map BUT no model run
    -h --noheader    .tss file have no header and start immediately with the time series
    -t --printtime   the computation time for hydrological modules are printed

 ```
In Docker, you would just type `docker run efas/lisvap:latest`, which is the equivalent of running lisvap1.py without arguments.
As a python module installed in your python environment, type `lisvap` with no arguments.
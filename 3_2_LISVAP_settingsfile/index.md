# The LISVAP settings file

## Introduction

In LISVAP, all file and parameter specifications are defined in a XML settings file. 
The purpose of the settings file is to link variables and parameters in the model to in- and output files (maps, time series) and numerical values. 
In addition, the settings file can be used to specify several *options*. 

It's convenient to download the [XML template](https://raw.githubusercontent.com/ec-jrc/lisflood-lisvap/master/settings_tpl.xml) that comes with source code and start from there 
instead of writing the settings file completely from scratch. 

In order to use the example, you should make sure the following requirements are met:
 
- All input maps are named according to default file names
- All base maps are in one directory or in its subfolders
- All meteo input is in one directory or in its subfolders
- An (empty) directory where all output data can be written exists
 
If this is all true, the settings file can be prepared very quickly by editing the items in the `lfuser` element. The following is a detailed description of the different sections of the ‘lfuser’ element. 

## Time-related constants

The ‘lfuser’ section starts with a number of constants that are related to the simulation period and the time interval used. 

 ```xml
<lfsettings>
  <lfuser>
    <group>
      <comment>
**************************************************************
TIME-RELATED CONSTANTS
**************************************************************
      </comment>

      <textvar name="CalendarDayStart" value="01/01/1981 00:00">
        <comment>
        Calendar day of 1st day in model run
        </comment>
      </textvar>

      <textvar name="DtSec" value="86400">
        <comment>
time step [seconds] ALWAYS USE 86400!!
        </comment>
      </textvar>

      <textvar name="StepStart" value="01/01/1981 00:00">
        <comment>
            Date of first time step in simulation
        </comment>
      </textvar>

      <textvar name="StepEnd" value="15/01/1981 00:00">
        <comment>
            Date of last time step
        </comment>
      </textvar>

      <textvar name="ReportSteps" value="1..15">
      </textvar>
    </group>

<!-- ... other settings ....-->

  </lfuser>
</lfsettings>
 ```

-  ***CalendarDayStart*** is the calendar day of the first time step in the model run; format is DD/MM/YYYY hh:mm
-  ***DtSec*** is the simulation time interval in seconds. It has a value of 86400  for a daily time interval. Some of the simplifying assumptions made in LISVAP related to the radiation balance are not valid at time steps smaller than days. Therefore, it is advised to use LISVAP for daily time intervals only (i.e. *DtSec* should always be 86400)
-  ***StepStart*** Date of first time step; format is DD/MM/YYYY hh:mm
-  ***StepEnd*** Date of the last time step; format is DD/MM/YYYY hh:mm
-  ***ReportSteps*** Interval of steps to be reported in output maps and tss; format is a..b, with a,b >= 1 and a, b integers.


## File paths

Here you can specify paths of all in- and output.

 ```xml
<group>

    <comment>
        **************************************************************
        FILE PATHS
        **************************************************************
    </comment>

    <textvar name="PathOut" value="/DATA/lisvap/output">
        <comment>
            Output path
        </comment>
    </textvar>

    <textvar name="PathBaseMapsIn" value="$(ProjectPath)/basemaps">
        <comment>
            Path to input base maps
        </comment>
    </textvar>

    <textvar name="PathMeteoIn" value="/DATA/lisvap/input">
        <comment>
            Path to input raw meteo maps
            E:/lisflood_test/LisvapWorld/meteo/raster
        </comment>
    </textvar>
</group>
 ```

-  ***PathOut*** is the path where all output is written
-  ***PathBaseMapsIn*** is the path where all input base maps (Table 4.1) are located
-  ***PathMeteoIn*** is the path where all meteo input (Table 4.2) is stored

**Note:** To refer to the folder where LISVAP project is running, you may use `$(ProjectPath)`, or its alias `$(ProjectDir)`.


## Prefixes of input/output meteorological variables

Each variable is read as a stack of maps. 
Name of each map is made up of its prefix followed by .nc extension.

Define in this section prefixes for all the meteorological **input** variables you would like let LISVAP run with.
Below the prefix configuration of the meteorological input variables from the EFAS dataset as an example. 

 ```xml
<group>
    <comment>
    **************************************************************
    PREFIXES OF INPUT METEO VARIABLES
    **************************************************************
    </comment>
    <textvar name="PrefixTMax" value="tx">
        <comment>
        prefix maximum temperature maps
        </comment>
    </textvar>
    <textvar name="PrefixTMin" value="tn">
        <comment>
        prefix minimum temperature maps
        </comment>
    </textvar>
    <textvar name="PrefixEAct" value="pd">
        <comment>
        prefix vapour pressure maps
        </comment>
    </textvar>
    <textvar name="PrefixWind" value="ws">
        <comment>
        prefix wind speed maps
        </comment>
    </textvar>
    <textvar name="PrefixRgd" value="rg">
        <comment>
        prefix incoming solar radiation maps
        </comment>
    </textvar>
</group>
 ```

-  ***PrefixTMax*** prefix of the maximum temperature maps
-  ***PrefixTMin*** prefix of the minimum temperature maps
-  ***PrefixEAct*** prefix of the actual vapour pressure maps
-  ***PrefixWind*** prefix of the wind speed maps
-  ***PrefixRgd*** prefix of the incoming solar radiation maps


Here you can define the prefix that is used for each meteorological **output** variable.

 ```xml
 <group>
    <comment>
    **************************************************************
    PREFIXES OF OUTPUT METEO VARIABLES
    **************************************************************
    </comment>
    
    <textvar name="PrefixTAvg" value="ta">
        <comment>
        prefix average temperature maps
        </comment>
    </textvar>
    
    <textvar name="PrefixE0" value="e">
        <comment>
        prefix E0 maps
        </comment>
    </textvar>
    
    <textvar name="PrefixES0" value="es">
        <comment>
        prefix ES0 maps
        </comment>
    </textvar>
    
    <textvar name="PrefixET0" value="et">
        <comment>
        prefix ET0 maps
        </comment>
    </textvar>
</group>
 ```

-  ***PrefixTAvg*** prefix of the average temperature maps 
-  ***PrefixE0*** prefix of the potential open-water evaporation maps 
-  ***PrefixES0*** prefix of the potential bare-soil evaporation maps
-  ***PrefixET0*** prefix of the potential (reference) evapotranspiration maps

## Constants

There are constants you define in settings file. Some of them may have different values from defaults, depending of region under simulation.
In case they are constant but not uniform for the region you are examinating, you can use a netCDF map to define it. 
Just use the path to the map instead of a numeric value.

Current list of constant and their default values are reported in the following table:

  **Table:** *LISVAP constants.*	

| Name           | Description                                                                        | Default  |
| -------------- | ---------------------------------------------------------------------------------- | -------- |
| AvSolarConst   | Average solar radiation at top atmosphere \[J/m2/s\] (I.E.A. 1978)                 | 1370     |
| StefBolt       | Stefan-Boltzmann constant \[J/m2/K4/day\]                                          | 4.903E-3 |
| Press0         | Atmosheric pressure at sea level \[mbar\]                                          | 1013     |
| PD             | Correction constant in daylength formula \[degrees\]                               | -2.65    |
| AlbedoSoil     | Albedo of bare soil surface (Supit et. al.)                                        | 0.15     |
| AlbedoWater    | Albedo of water surface (Supit et. al.)                                            | 0.05     |
| AlbedoCanopy   | Albedo of vegetation canopy (FAO,1998)                                             | 0.23     |
| FactorSoil     | Estimated value for surface roughness factor of bare soil (Supit et. al.)          | 0.75     |
| FactorWater    | Estimated value for surface roughness factor of water surface (Supit et. al.)      | 0.5      |
| FactorCanopy   | Estimated value for surface roughness factor of vegetation canopy (Supit et. al.)  | 1        |


## <a id="options"></a>LISVAP options

LISVAP has several options, which can be set in the settings file’s `lfoptions` element. Those allow you some flexibility with regard to input and output settings.
The table below lists all currently implemented options and their respective defaults. 

 **Table:** *LISVAP options.*
 

| Option                    | Description                                                                        | Default |
| ------------------------- | ---------------------------------------------------------------------------------- | ------- |
| **Input**                 |                                                                                    |         |
| TemperatureInKelvinFlag   | Temperature in Kelvin                                                              | False   |
| readNetcdfStack           | Input variables as netCDF mapstacks                                                | False   |
| useTavg                   | Use $T_{avg}$ input map. If false, will be computed out of $T_{max}$ and $T_{min}$ | False   |
| EFAS                      | Use *EFAS* setup                                                                   | True    |
| CORDEX[^1]                | Use *CORDEX* setup                                                                 | False   |
| **Output**                |                                                                                    |         |
| writeNetcdfStack          | Output variables as netCDF mapstacks                                               | False   |
| writeNetcdf               | Output variables as netCDF maps                                                    | False   |
| repAvTimeseries           | Write output TSS                                                                   | False   |
| repE0Maps                 | Write output variable $E_0$ map                                                    | True    |
| repET0Maps                | Write output variable $ET_0$ map                                                   | True    |
| repES0Maps                | Write output variable $ES_0$ map                                                   | True    |
| repTAvgMaps               | Write output variable $T_{avg}$ map                                                | True    |

[^1]: Keep in mind that EFAS and CORDEX are two mutually-exclusive flags. If both are true, EFAS flag has precedence.

These options all act as switches (1= on,  0=off). Below an example of how to change the default settings by adding/changing the respective option parameter into the settings file:

```xml

   <lfoptions>

        <setoption name="readNetcdfStack" choice="1" />
        <setoption name="writeNetcdfStack" choice="1" />
        <setoption name="TemperatureInKelvinFlag" choice="0" />
        <setoption name="repE0Maps" choice="1" />
        <setoption name="repTavgMaps" choice="1"/>

        <setoption name="EFAS" choice="1" />
        <setoption name="CORDEX" choice="0" />

    </lfoptions>
``` 

Note that each option generally requires additional items in the settings file. 
For instance, using the dew point temperature option requires that the corresponding map stack is defined in the settings file. 
The template settings file that is provided with LISVAP always contains file definitions for all implemented options.
"""

Copyright 2019 European Union

Licensed under the EUPL, Version 1.2 or as soon they will be approved by the European Commission  subsequent versions of the EUPL (the "Licence");

You may not use this work except in compliance with the Licence.
You may obtain a copy of the Licence at:

https://joinup.ec.europa.eu/sites/default/files/inline-files/EUPL%20v1_2%20EN(1).txt

Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the Licence for the specific language governing permissions and limitations under the Licence.

"""

import inspect
import os
import copy
import pprint
import sys
import getopt
import time
import xml.dom.minidom
from collections import Counter, defaultdict, namedtuple

import numpy as np
from netCDF4 import Dataset
from pcraster import pcraster

from .decorators import cached

project_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..'))


class LisfloodError(Exception):
    """
    the error handling class
    prints out an error
    """

    def __init__(self, msg):

        self._msg = msg

    def __str__(self):
        return '\n\n ========================== LISFLOOD ERROR ============================= \n{}'.format(self._msg)


class Singleton(type):
    """
    Singleton metaclass to keep single instances by init arguments
    """
    _instances = {}
    _init = {}
    _current = {}

    def __init__(cls, name, bases, dct):
        cls._init[cls] = dct.get('__init__', None)
        super(Singleton, cls).__init__(name, bases, dct)

    def __call__(cls, *args, **kwargs):
        init = cls._init[cls]
        if init is not None:
            key = (cls, frozenset(inspect.getcallargs(init, None, *args, **kwargs).items()))
        else:
            key = cls

        if key not in cls._instances:
            cls._instances[key] = super(Singleton, cls).__call__(*args, **kwargs)
        cls._current[cls] = cls._instances[key]
        return cls._instances[key]

    def instance(cls):
        return cls._current[cls]


class LisSettings(object):
    __metaclass__ = Singleton
    printer = pprint.PrettyPrinter(indent=4, width=120)

    def __init__(self, settings_file):
        dom = xml.dom.minidom.parse(settings_file)

        self.settings_path = os.path.normpath(os.path.dirname((os.path.abspath(settings_file))))
        self.flags = self.config_flags()

        user_settings, bindings = self.get_binding(dom)

        self.binding = bindings
        self.options = self.get_options(dom)
        self.report_steps = self._report_steps(user_settings, bindings)
        self.report_timeseries = self._report_tss()
        self.report_maps_steps, self.report_maps_all, self.report_maps_end = self._reported_maps()

    def get_binding(self, dom):
        binding = {}

        #  built-in user variables
        user = {
            'ProjectDir': project_dir, 'ProjectPath': project_dir,
            'SettingsDir': self.settings_path, 'SettingsPath': self.settings_path,
        }
        lfuse = dom.getElementsByTagName("lfuser")[0]
        for userset in lfuse.getElementsByTagName("textvar"):
            user[userset.attributes['name'].value] = str(userset.attributes['value'].value)
            binding[userset.attributes['name'].value] = str(userset.attributes['value'].value)

        # get all the binding in the last part of the settingsfile  = lfbinding
        bind_elem = dom.getElementsByTagName("lfbinding")[0]
        for textvar_elem in bind_elem.getElementsByTagName("textvar"):
            binding[textvar_elem.attributes['name'].value] = str(textvar_elem.attributes['value'].value)

        # replace/add the information from lfuser to lfbinding
        for i in binding:
            expr = binding[i]
            while expr.find('$(') > -1:
                a1 = expr.find('$(')
                a2 = expr.find(')')
                try:
                    s2 = user[expr[a1 + 2:a2]]
                except KeyError:
                    print 'no ', expr[a1 + 2:a2], ' in lfuser defined'
                else:
                    expr = expr.replace(expr[a1:a2 + 1], s2)
            binding[i] = expr
        return user, binding

    def __str__(self):
        res = """
Binding: {binding}
Options: {options}
report_steps: {report_steps}
report_timeseries: {report_timeseries}
report_maps_steps: {report_maps_steps}
report_maps_all: {report_maps_all}
report_maps_end: {report_maps_end}
""".format(binding=self.printer.pformat(self.binding), options=self.printer.pformat(self.options),
           report_steps=self.printer.pformat(self.report_steps), report_timeseries=self.printer.pformat(self.report_timeseries),
           report_maps_steps=self.printer.pformat(self.report_maps_steps), report_maps_all=self.printer.pformat(self.report_maps_all),
           report_maps_end=self.printer.pformat(self.report_maps_end))
        return res

    def _set_active_options(self, key, rep_maps, reported, report_temp, restricted_options):
        for rep in report_temp:
            if self.options.get(rep):
                allow = True
                for j in restricted_options:
                    if j in self.options and not self.options[j]:
                        allow = False
                        break
                if allow:
                    reported[key] = rep_maps[key]

    @staticmethod
    def _report_steps(user_settings, bindings):
        res = {}
        repsteps = user_settings['ReportSteps'].split(',')
        if repsteps[-1] == 'endtime':
            repsteps[-1] = bindings['StepEnd']
        jjj = []
        for i in repsteps:
            if '..' in i:
                j = map(int, i.split('..'))
                for jj in xrange(j[0], j[1] + 1):
                    jjj.append(jj)
            else:
                jjj.append(i)
        res['rep'] = map(int, jjj)
        return res

    def _report_tss(self):
        rep_timeseries = {}
        report_time_series_act = {}
        # running through all times series
        report_time_serie = self.options['timeseries']
        for ts in report_time_serie:
            key = ts.name
            rep_timeseries[key] = ts
            rep_opt = ts.repoption
            rest_opt = ts.restrictoption
            self._set_active_options(key, rep_timeseries, report_time_series_act, rep_opt, rest_opt)

        return report_time_series_act

    def _reported_maps(self):

        rep_maps = {}
        report_maps_steps = {}
        report_maps_all = {}
        report_maps_end = {}

        # running through all maps

        for rm in self.options['reportedmaps']:
            key = rm.name
            rep_maps[key] = rm

            rep_all = rm.all
            rep_steps = rm.steps
            rep_end = rm.end
            rest_opt = rm.restrictoption

            self._set_active_options(key, rep_maps, report_maps_all, rep_all, rest_opt)
            self._set_active_options(key, rep_maps, report_maps_steps, rep_steps, rest_opt)
            self._set_active_options(key, rep_maps, report_maps_end, rep_end, rest_opt)

        return report_maps_steps, report_maps_all, report_maps_end

    @staticmethod
    def config_flags():
        """ read flags - according to the flags the output is adjusted
            quiet, veryquiet, loud, checkfiles, noheader, printtime
        """
        flag_names = ['quiet', 'veryquiet', 'loud',
                      'checkfiles', 'noheader', 'printtime']
        flags = {'quiet': False, 'veryquiet': False, 'loud': False,
                 'checkfiles': False, 'noheader': False, 'printtime': False}

        @cached
        def _flags(argz):

            try:
                opts, arguments = getopt.getopt(argz, 'qvlcht', flag_names)
            except getopt.GetoptError as e:
                from lisvap.lisvap1 import usage
                usage()
            else:
                for o, a in opts:
                    for opt in (('-q', '--quiet'), ('-v', '--veryquiet'), ('-l', '--loud'), ('-c', '--checkfiles'), ('-h', '--noheader'), ('-t', '--printtime')):
                        if o in opt:
                            flags[opt[1].lstrip('--')] = True
                            break
            return flags

        if 'test' in sys.argv[0] or 'test' in sys.argv[1]:
            return flags
        args = sys.argv[2:]
        return _flags(args)

    @staticmethod
    def get_options(dom):
        options = copy.deepcopy(default_options)
        # getting option set in the specific settings file
        # and resetting them to their choice value
        lfoptions_elem = dom.getElementsByTagName("lfoptions")[0]
        option_setting = {}
        for optset in lfoptions_elem.getElementsByTagName("setoption"):
            option_setting[optset.attributes['name'].value] = bool(int(optset.attributes['choice'].value))

        for key in option_setting:
            # overwriting default values from setting.xml
            options[key] = option_setting[key]

        # reverse the initLisflood option to use it as a restriction for output
        # eg. produce output if not(initLisflood)
        options['nonInit'] = not (options['InitLisflood'])
        return options


class NetcdfMetadata(object):
    __metaclass__ = Singleton

    @classmethod
    def register(cls, netcdf_file):
        return cls(netcdf_file)

    def __setitem__(self, k, v):
        self._metadata[k] = v

    def __delitem__(self, k):
        del self._metadata[k]

    def __getitem__(self, k):
        return self._metadata.get(k)

    def __iter__(self):
        return iter(self._metadata)

    def __len__(self):
        return len(self._metadata)

    def __contains__(self, k):
        return k in self._metadata

    def __init__(self, netcdf_file):
        self.path = netcdf_file
        self._metadata = self._read_metadata(netcdf_file)

    @staticmethod
    def _read_metadata(nc):
        res = {}
        filename = '{}.{}'.format(os.path.splitext(nc)[0], 'nc')
        if not (os.path.isfile(filename)):
            msg = 'NetCDF file {} does not exist'.format(filename)
            raise LisfloodError(msg)
        nf1 = Dataset(filename, 'r')
        for var in nf1.variables:
            res[var] = nf1.variables[var].__dict__
        nf1.close()
        return res


class MaskMapMetadata(object):
    __metaclass__ = Singleton

    @classmethod
    def register(cls):
        return cls()

    def __init__(self):
        self._metadata = self._pcr_clone_metadata()

    @staticmethod
    def _pcr_clone_metadata():
        # Definition of cellsize, coordinates of the meteomaps and maskmap
        # need some love for error handling
        return {'x': pcraster.clone().west(), 'y': pcraster.clone().north(),
                'col': pcraster.clone().nrCols(),
                'row': pcraster.clone().nrRows(),
                'cell': pcraster.clone().cellSize()}

    def __setitem__(self, k, v):
        self._metadata[k] = v

    def __delitem__(self, k):
        del self._metadata[k]

    def __getitem__(self, k):
        return self._metadata.get(k)

    def __iter__(self):
        return iter(self._metadata)

    def __len__(self):
        return len(self._metadata)

    def __contains__(self, k):
        return k in self._metadata


class CutMap(tuple):
    __metaclass__ = Singleton

    @classmethod
    def register(cls, in_file):
        return cls(in_file)

    def __init__(self, in_file):
        self.path = in_file
        self.cuts = self.get_cuts(in_file)

    @staticmethod
    def get_cuts(in_file):
        settings = LisSettings.instance()
        filename = '{}.{}'.format(os.path.splitext(in_file)[0], 'nc')
        nf1 = Dataset(filename, 'r')
        # original code
        # x1, x2, y1, y2 = [round(nf1.variables.values()[var_ix][j], 5) for var_ix in range(2) for j in range(2)]
        # new safer code that doesn't rely on a specific variable order in netCDF file (R.COUGHLAN & D.DECREMER)
        if 'lon' in nf1.variables.keys():
            x1 = nf1.variables['lon'][0]
            x2 = nf1.variables['lon'][1]
            y1 = nf1.variables['lat'][0]
            y2 = nf1.variables['lat'][1]
        else:
            x1 = nf1.variables['x'][0]
            x2 = nf1.variables['x'][1]
            y1 = nf1.variables['y'][0]
            y2 = nf1.variables['y'][1]
        nf1.close()

        maskmap_attrs = MaskMapMetadata.instance()
        if maskmap_attrs['cell'] != round(np.abs(x2 - x1), 5) or maskmap_attrs['cell'] != round(np.abs(y2 - y1), 5):
            raise LisfloodError('Cell size different in maskmap {} and {}'.format(settings.binding['MaskMap'], filename))

        half_cell = maskmap_attrs['cell'] / 2
        x = x1 - half_cell  # |
        y = y1 + half_cell  # | coordinates of the upper left corner of the input file upper left pixel

        cut0 = int(round(np.abs(maskmap_attrs['x'] - x) / maskmap_attrs['cell']))
        cut1 = cut0 + maskmap_attrs['col']
        cut2 = int(round(np.abs(maskmap_attrs['y'] - y) / maskmap_attrs['cell']))
        cut3 = cut2 + maskmap_attrs['row']
        return cut0, cut1, cut2, cut3  # input data will be sliced using [cut2:cut3, cut0:cut1]

    @property
    def slices(self):
        return slice(self.cuts[2], self.cuts[3]), slice(self.cuts[0], self.cuts[1])


TimeSeries = namedtuple('TimeSeries', 'name, output_var, where, repoption, restrictoption, operation')
ReportedMap = namedtuple('ReportedMap','name, output_var, unit, end, steps, all, restrictoption')


class TimeProfiler(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.start = time.clock()
        self.times = defaultdict(list)
        self.times_sum = {}

    def reset(self):
        self.__init__()

    def timemeasure(self, name):
        if self.times[name]:
            t = time.clock() - self.times[name][-1]
        else:
            t = time.clock() - self.start
        self.times[name].append(t)

    def report(self):
        for name in self.times:
            self.times_sum[name] = sum(self.times[name])
        tot = sum(v for v in self.times_sum.values())
        print "\n\nTime profiling"
        print "%-17s %10s %8s" % ("Name", "time[s]", "%")
        for name in self.times_sum:
            print "%-17s %10.2f %8.1f" % (name, self.times_sum[name], 100 * self.times_sum[name] / tot)


cdf_flags = Counter({'all': 0, 'steps': 0, 'end': 0})
default_options = {
    'useTavg': False,
    'InitLisflood': False, 'InitLisfloodwithoutSplit': False,
    'readNetcdfStack': False, 'writeNetcdfStack': False, 'writeNetcdf': False,
    'repAvTimeseries': False,
    'repET0Maps': True, 'repES0Maps': True, 'repE0Maps': True, 'repTAvgMaps': True,
    'EFAS': True, 'CORDEX': False,
    'timeseries': [
        TimeSeries(name='TAvgTS', output_var='TAvg', where='1', repoption='repAvTimeseries', restrictoption='', operation=''),
        TimeSeries(name='ET0TS', output_var='ETRef', where='1', repoption='repAvTimeseries', restrictoption='', operation=''),
        TimeSeries(name='E0TS', output_var='EWRef', where='1', repoption='repAvTimeseries', restrictoption='', operation=''),
        TimeSeries(name='ES0TS', output_var='ESRef', where='1', repoption='repAvTimeseries', restrictoption='', operation=''),
    ],
    'reportedmaps': [
        ReportedMap(name='ET0Maps', output_var='ETRef', unit='mm day-1', end='', steps='', all='repET0Maps', restrictoption=''),
        ReportedMap(name='E0Maps', output_var='EWRef', unit='mm day-1', end='', steps='', all='repE0Maps', restrictoption=''),
        ReportedMap(name='ES0Maps', output_var='ESRef', unit='mm day-1', end='', steps='', all='repES0Maps', restrictoption=''),
        ReportedMap(name='TAvgMaps', output_var='TAvg', unit='degree C', end='', steps='', all='repTAvgMaps', restrictoption=''),
    ],
}
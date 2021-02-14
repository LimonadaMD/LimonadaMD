# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#    Limonada is accessible at https://limonada.univ-reims.fr/
#    Copyright (C) 2016-2020 - The Limonada Team (see the AUTHORS file)
#
#    This file is part of Limonada.
#
#    Limonada is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Limonada is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Limonada.  If not, see <http://www.gnu.org/licenses/>.

# standard library
import os
import re
from unidecode import unidecode
import numpy as np
import math

# third-party
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.palettes import Spectral6
from bokeh.plotting import figure, output_file, show
from bokeh.transform import factor_cmap
from bokeh.palettes import Viridis

# Django
from django.conf import settings

# local Django
from .choices import PROPTYPE_CHOICES 


def get_float(val):
   try:
    return True, float(val) 
   except ValueError:
    return False, val


def properties_types():
    return dict((key, unidecode(val).replace(' ', '_')) for key, val in PROPTYPE_CHOICES)


def bokeh_data(filepath):

    datafile = open(os.path.join(settings.MEDIA_ROOT, filepath)).readlines()
    dataformat = {}
    data = []
    for line in datafile:
        if re.search('^@', line):
            if re.search('^@TYPE[ \t]+', line):
                dataformat['type'] = line.split()[1]
            if re.search('^@[ \t]+title[ \t]+', line):
                if re.findall(r'\"(.+?)\"', line):
                    dataformat['title'] = re.findall(r'\"(.+?)\"', line)[0]
            if re.search('^@[ \t]+xaxis[ \t]+label[ \t]+', line):
                if re.findall(r'\"(.+?)\"', line):
                    dataformat['x_axis_label'] = re.findall(r'\"(.+?)\"', line)[0]
            if re.search('^@[ \t]+yaxis[ \t]+label[ \t]+', line):
                if re.findall(r'\"(.+?)\"', line):
                    dataformat['y_axis_label'] = re.findall(r'\"(.+?)\"', line)[0]
            if re.search('^@[ \t]+s[0-9]+[ \t]+legend[ \t]+', line):
                if re.findall(r'\"(.+?)\"', line):
                    if 'legend' not in dataformat.keys():
                        dataformat['legend'] = {}
                    dataformat['legend'][line.split()[1]] = re.findall(r'\"(.+?)\"', line)[0]
        elif line[:1] != "#" and line.strip() != '':
            if not data:
                nb = len(line.split())
                for i in range(nb):
                    data.append([])
                datatype = []
                for i in line.split():
                    test, val = get_float(i)
                    datatype.append(test)
                datatype = np.array(datatype)
            arr = line.split()
            if len(arr) == nb:
                tempdata = []
                temptest = []
                for i in arr:
                    test, val = get_float(i)
                    tempdata.append(val)
                    temptest.append(test)
                temptest = np.array(temptest)
                if np.array_equal(datatype,temptest):
                    for i in range(nb):
                        data[i].append(tempdata[i])

    if 'type' not in dataformat.keys():
        dataformat['type'] = 'xy'
    if 'title' not in dataformat.keys():
        dataformat['title'] = ''
    if 'x_axis_label' not in dataformat.keys():
        dataformat['x_axis_label'] = ''
    if 'y_axis_label' not in dataformat.keys():
        dataformat['y_axis_label'] = ''
    if 'legend' not in dataformat.keys():
        dataformat['legend'] = {}

    if not data:
        test = False  
        plot = figure(title='Line graph', x_axis_label='X-Axis', y_axis_label='Y-Axis', plot_width=400, plot_height=400)
    else:
        test = True
        legend = []
        for i in range(1,nb):
            j = 's%d' % (i-1)
            if j in dataformat['legend'].keys():
               legend.append(dataformat['legend'][j])
            else:
               legend.append('')
        if len(data[0]) == 1:

            histnames = []
            counts = []
            for i in range(1,nb):
                if datatype[i]:
                    histnames.append(legend[i-1])
                    counts.append(data[i][0])
            source = ColumnDataSource(data=dict(histnames=histnames, counts=counts))
            plot = figure(x_range=histnames, plot_height=400, toolbar_location=None, title=dataformat['y_axis_label'])
            plot.vbar(x='histnames', top='counts', width=0.9, source=source, #legend_field="histnames",
                   line_color='white', fill_color=factor_cmap('histnames', palette=Viridis[nb], factors=histnames))
            plot.xgrid.grid_line_color = None
            plot.y_range.start = 0
            #plot.y_range.end = 9
            #plot.legend.orientation = "horizontal"
            #plot.legend.location = "bottom_right"
            plot.xaxis.major_label_orientation = math.pi/4
            hover = HoverTool(tooltips = [('Value', '@counts')])
            plot.add_tools(hover)

        else:
            plot = figure(title=dataformat['title'], x_axis_label=dataformat['x_axis_label'], y_axis_label=dataformat['y_axis_label'], plot_width=600, plot_height=400)
            if nb <= 2:
                colors = Viridis[3]
            else:
                colors = Viridis[nb]
            plotlist = []
            for i in range(1,nb):
                plotlist.append(plot.line(data[0], data[i], line_width=2, line_color=colors[i-1]))
            legend_items = []
            for i in range(nb-1):
                legend_items.append((legend[i], [plotlist[i]]))
            bkh_legend = Legend(items=legend_items, location="center")
            plot.add_layout(bkh_legend, 'right')
 
    script, div = components(plot)
    return test, script, div

""" Code that plots fields from the CMAC radar object. """

import os
from datetime import datetime
import operator

import netCDF4
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pyart

from pyart.graph.common import generate_radar_name
from pyart.graph.common import generate_radar_time_begin, generate_title


def quicklooks(radar, image_directory=None, sweep=3,
               max_lat=37.0, min_lat=36.0, max_lon=-97.0, min_lon=-98.3):
    """
    Quicklooks, images produced with regards to CMAC

    Parameter
    ---------
    radar : Radar
        Radar object that has CMAC applied to it.

    Optional Parameters
    -------------------
    image_directory : str
        File path to the image folder of which to save the CMAC images. If no
        image file path is given, image path defaults to users home directory.
    sweep : int
        Sweep number to have plotted. Default is 3.
    max_lat : float
        Maximum latitude for plot bounds. Default is 37.0.
    min_lat : float
        Minimum latitude for plot bounds. Default is 36.0.
    max_lon : float
        Maximum longitude for plot bounds. Default is -97.0.
    min_lon : float
        Minimum longitude for plot bounds. Default is -98.3.

    """

    if image_directory is None:
        image_directory = os.path.expanduser('~')

    radar_start_date = netCDF4.num2date(
    radar.time['data'][0], radar.time['units'])

    date_string = datetime.strftime(radar_start_date, '%Y%m%d.%H%M%S')
    arm_name = '.sgpxsaprcmacsurI5.c1.'
    combined_name = arm_name + date_string

    # Creating a plot of reflectivity before CMAC.
    lal = np.arange(min_lat, max_lat, .2)
    lol = np.arange(min_lon, max_lon, .2)

    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('reflectivity', sweep=sweep, resolution='c',
                         vmin=-8, vmax=64, mask_outside=False,
                         cmap=pyart.graph.cm.NWSRef,
                         min_lat=min_lat, min_lon=min_lon,
                         max_lat=max_lat, max_lon=max_lon,
                         lat_lines=lal, lon_lines=lol)
    plt.savefig(
        image_directory
        + '/reflectivity' + combined_name + '.png')
    plt.close()

    # Four panel plot of gate_id, velocity_texture, reflectivity, and
    # cross_correlation_ratio.
    cat_dict = {}
    print('##')
    print('## Keys for each gate id are as follows:')
    for pair_str in radar.fields['gate_id']['notes'].split(','):
        print('##   ', str(pair_str))
        cat_dict.update({pair_str.split(':')[1]:int(pair_str.split(':')[0])})
    sorted_cats = sorted(cat_dict.items(), key=operator.itemgetter(1))
    cat_colors = {'rain': 'green',
                  'multi_trip': 'red',
                  'no_scatter': 'gray',
                  'snow': 'cyan',
                  'melting': 'yellow',
                  'clutter': 'black'}
    lab_colors = ['red', 'cyan', 'grey', 'green', 'yellow', 'black']
    lab_colors = [cat_colors[kitty[0]] for kitty in sorted_cats]
    cmap = matplotlib.colors.ListedColormap(lab_colors)

    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[15, 10])
    plt.subplot(2, 2, 1)
    display.plot_ppi_map('gate_id', sweep=sweep, min_lon=min_lon,
                         max_lon=max_lon, min_lat=min_lat,
                         max_lat=max_lat, resolution='l', cmap=cmap,
                         vmin=0, vmax=5)
    cbax = plt.gca()
    tick_locs = np.linspace(0, len(sorted_cats) - 2, len(sorted_cats)) + 0.5
    display.cbs[-1].locator = matplotlib.ticker.FixedLocator(tick_locs)
    catty_list = [sorted_cats[i][0] for i in range(len(sorted_cats))]
    display.cbs[-1].formatter = matplotlib.ticker.FixedFormatter(catty_list)
    display.cbs[-1].update_ticks()
    plt.subplot(2, 2, 2)
    display.plot_ppi_map('reflectivity', sweep=sweep, vmin=-8, vmax=64,
                         min_lon=min_lon, max_lon=max_lon, min_lat=min_lat,
                         max_lat=max_lat, resolution='l',
                         cmap=pyart.graph.cm.NWSRef)

    plt.subplot(2, 2, 3)
    display.plot_ppi_map('velocity_texture', sweep=sweep, vmin=0, vmax=14,
                         min_lon=min_lon, max_lon=max_lon, min_lat=min_lat,
                         max_lat=max_lat, resolution='l',
                         title=_generate_title(
                             radar, 'velocity_texture', sweep),
                         cmap=pyart.graph.cm.NWSRef)
    plt.subplot(2, 2, 4)
    display.plot_ppi_map('cross_correlation_ratio', sweep=sweep, vmin=.5,
                         vmax=1, min_lon=min_lon, max_lon=max_lon,
                         min_lat=min_lat, max_lat=max_lat, resolution='l',
                         cmap=pyart.graph.cm.Carbone42)
    plt.savefig(
        image_directory
        + '/cmac_four_panel_plot' + combined_name + '.png')
    plt.close()

    # Creating a plot with reflectivity corrected with gate ids.
    cmac_gates = pyart.correct.GateFilter(radar)
    cmac_gates.exclude_all()
    cmac_gates.include_equal('gate_id', cat_dict['rain'])
    cmac_gates.include_equal('gate_id', cat_dict['melting'])
    cmac_gates.include_equal('gate_id', cat_dict['snow'])

    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('reflectivity',
                         sweep=sweep, resolution='l',
                         vmin=-8, vmax=64, mask_outside=False,
                         cmap=pyart.graph.cm.NWSRef,
                         title=_generate_title(
                             radar, 'masked_corrected_reflectivity',
                             sweep),
                         min_lat=min_lat, min_lon=min_lon,
                         max_lat=max_lat, max_lon=max_lon,
                         lat_lines=lal, lon_lines=lol,
                         gatefilter=cmac_gates)
    plt.savefig(
        image_directory
        + '/masked_corrected_reflectivity' + combined_name + '.png')
    plt.close()

    # Creating a plot with reflectivity corrected with attenuation.
    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('attenuation_corrected_reflectivity', sweep=sweep,
                         vmin=0, vmax=60., resolution='l',
                         title=_generate_title(
                             radar, 'attenuation_corrected_reflectivity',
                             sweep),
                         min_lat=min_lat, min_lon=min_lon,
                         max_lat=max_lat, max_lon=max_lon,
                         lat_lines=lal, lon_lines=lol)
    plt.savefig(
        image_directory
        + '/attenuation_corrected_reflectivity' + combined_name + '.png')
    plt.close()

    # Creating a plot of specific attenuation.
    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('specific_attenuation', sweep=sweep, vmin=0,
                         vmax=1.0, resolution='l',
                         min_lat=min_lat, min_lon=min_lon,
                         max_lat=max_lat, max_lon=max_lon,
                         lat_lines=lal, lon_lines=lol)
    plt.savefig(
        image_directory
        + '/specific_attenuation' + combined_name + '.png')
    plt.close()

    # Creating a plot of corrected differential phase.
    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('corrected_differential_phase', sweep=sweep,
                         title=_generate_title(
                             radar, 'corrected_differential_phase',
                             sweep),
                         resolution='l', min_lat=min_lat,
                         min_lon=min_lon, max_lat=max_lat, max_lon=max_lon,
                         lat_lines=lal, lon_lines=lol)
    plt.savefig(
        image_directory
        + '/corrected_differential_phase' + combined_name + '.png')
    plt.close()

    # Creating a plot of corrected specific differential phase.
    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('corrected_specific_diff_phase', sweep=sweep,
                         vmin=0, vmax=6, resolution='l',
                         title=_generate_title(
                             radar, 'corrected_specific_diff_phase',
                             sweep),
                         min_lat=min_lat, min_lon=min_lon, max_lat=max_lat,
                         max_lon=max_lon, lat_lines=lal, lon_lines=lol)
    plt.savefig(
        image_directory
        + '/corrected_specific_diff_phase' + combined_name + '.png')
    plt.close()

    # Creating a plot with region dealias corrected velocity.
    nyq = radar.instrument_parameters['nyquist_velocity']['data'][0]
    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('corrected_velocity', sweep=sweep, resolution='l',
                         cmap=pyart.graph.cm.NWSVel, vmin=-1.5*nyq,
                         vmax=1.5*nyq, min_lat=min_lat, min_lon=min_lon,
                         max_lat=max_lat, max_lon=max_lon, lat_lines=lal,
                         lon_lines=lol)
    plt.savefig(
        image_directory
        + '/corrected_velocity' + combined_name + '.png')
    plt.close()

    # Creating a plot of rain rate A
    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('rain_rate_A', sweep=sweep, resolution='l',
                         vmin=0, vmax=120, min_lat=min_lat, min_lon=min_lon,
                         max_lat=max_lat, max_lon=max_lon, lat_lines=lal,
                         lon_lines=lol)
    plt.savefig(
        image_directory
        + '/rain_rate_A' + combined_name + '.png')
    plt.close()

    # Creating a plot of filtered corrected differential phase.
    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('filtered_corrected_differential_phase', sweep=sweep,
                         title=_generate_title(
                             radar, 'filtered_corrected_differential_phase',
                             sweep),
                         resolution='l', min_lat=min_lat,
                         min_lon=min_lon, max_lat=max_lat, max_lon=max_lon,
                         lat_lines=lal, lon_lines=lol,
                         cmap=pyart.graph.cm.Theodore16)
    plt.savefig(
        image_directory
        + '/filtered_corrected_differential_phase' + combined_name + '.png')
    plt.close()

    # Creating a plot of filtered corrected specific differential phase.
    display = pyart.graph.RadarMapDisplay(radar)
    fig = plt.figure(figsize=[10, 8])
    display.plot_ppi_map('filtered_corrected_specific_diff_phase', sweep=sweep,
                         title=_generate_title(
                             radar, 'filtered_corrected_specific_diff_phase',
                             sweep),
                         resolution='l', min_lat=min_lat,
                         min_lon=min_lon, max_lat=max_lat, max_lon=max_lon,
                         lat_lines=lal, lon_lines=lol,
                         cmap=pyart.graph.cm.Theodore16)
    plt.savefig(
        image_directory
        + '/filtered_corrected_specific_diff_phase' + combined_name + '.png')
    plt.close()


def _generate_title(radar, field, sweep):
    """ Generates a title for each plot. """
    time_str = generate_radar_time_begin(radar).isoformat() + 'Z'
    fixed_angle = radar.fixed_angle['data'][sweep]
    l1 = "%s %.1f Deg. %s " % (generate_radar_name(radar), fixed_angle,
                           time_str)
    field_name = str(field)
    field_name = field_name.replace('_', ' ')
    field_name = field_name[0].upper() + field_name[1:]
    return l1 + '\n' + field_name

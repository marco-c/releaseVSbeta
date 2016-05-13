from bokeh.plotting import curdoc, Figure
from bokeh.models import ColumnDataSource, HoverTool, HBox, VBoxForm
from bokeh.models.widgets import Select, Panel, Tabs, CheckboxGroup
import json
import numpy as np
import tarfile
import time
import urllib
import os

# Download the data file if it doesn't exist or if it is one day old.
if not os.path.exists('agg_data.tar.gz') or os.path.getmtime('agg_data.tar.gz') + 24 * 60 * 60 < time.time():
  # Use the preexisting file as a backup.
  try:
    os.rename('agg_data.tar.gz', 'agg_data.tar.gz.old')
  except OSError:
    pass

  try:
    urllib.URLopener().retrieve('https://analysis-output.telemetry.mozilla.org/beta_release_os_gfx/data/agg_data.tar.gz', 'agg_data.tar.gz')
  except:
    # Use the backup copy if there was an error during the download.
    try:
      os.rename('agg_data.tar.gz.old', 'agg_data.tar.gz')
    except OSError:
      pass

  # Remove the backup copy.
  try:
    os.remove('agg_data.tar.gz.old')
  except OSError:
    pass

if not os.path.exists('agg_data.json'):
  tarfile.open('agg_data.tar.gz', 'r:gz').extractall('.')

with open('agg_data.json') as data_file:
  data = json.load(data_file)

versions = []
for key in data['platforms']:
  versions.append(key)

platformData = data['platforms']
oses = [v for v in platformData['release']['oses']]
osTotalReleaseUsers = platformData['release']['total']
osTotalBetaUsers = platformData['beta']['total']


def getOSVersionNames(version, os, sort=False):
  if sort:
    return [d for d, v in sorted(platformData[version]['oses'][os]['versions'].iteritems(), key=lambda (d, v): v, reverse=True)]
  else:
    return [d for d in platformData[version]['oses'][os]['versions']]


def getUsersForOses(version, oses=oses):
  values = []
  for osName in oses:
    for k, v in platformData[version]['oses'].iteritems():
      if k == osName:
        values.append(v['total'])
        break

  return np.array(values, dtype=np.float)


def getUsersForVersions(version, os, versions=None):
  if versions is None:
    versions = getOSVersionNames('release', os, True)

  values = []
  for osVersion in versions:
    for k, v in platformData[version]['oses'][os]['versions'].iteritems():
      if k == osVersion:
        values.append(v)
        break

  return np.array(values, dtype=np.float)


def buildOSesTab():
  osesCheckbox = CheckboxGroup(labels=oses, active=[i for i in range(len(oses))])

  source_release = ColumnDataSource(data=dict(x=[], y=[], height=[]))
  source_beta = ColumnDataSource(data=dict(x=[], y=[], height=[]))

  fig = Figure(title='OS', x_range=[], y_range=[0, 0], plot_width=1000, plot_height=650)

  hover = HoverTool(tooltips=[
    ('Users', '@height %')
  ])

  fig.add_tools(hover)

  fig.rect(x='x', y='y', height='height', source=source_release,
           width=0.4, color='orange', legend='Release')

  fig.rect(x='x', y='y', height='height', source=source_beta,
           width=0.4, color='blue', legend='Beta')

  fig.xaxis.major_label_orientation = np.pi / 3

  def update(selected):
    cur_oses = [oses[i] for i in range(len(oses)) if i in selected]

    releaseUsers = 100 * getUsersForOses('release', cur_oses) / osTotalReleaseUsers
    betaUsers = 100 * getUsersForOses('beta', cur_oses) / osTotalBetaUsers

    fig.x_range.factors = cur_oses
    fig.y_range.end = max([releaseUsers.max(), betaUsers.max()])

    source_release.data = dict(
      x=[c + ':0.3' for c in cur_oses],
      y=releaseUsers / 2,
      height=releaseUsers,
    )

    source_beta.data = dict(
      x=[c + ':0.7' for c in cur_oses],
      y=betaUsers / 2,
      height=betaUsers,
    )

  osesCheckbox.on_click(update)

  update(osesCheckbox.active)

  osesComparison = HBox(HBox(VBoxForm(*[osesCheckbox]), width=300), fig, width=1100)

  return Panel(child=osesComparison, title="OS Comparison")


def buildOSVersionsTab():
  osSelect = Select(title='OS', options=oses, value=oses[0])
  versionCheckbox = CheckboxGroup()

  source_release = ColumnDataSource(data=dict(x=[], y=[], height=[]))
  source_beta = ColumnDataSource(data=dict(x=[], y=[], height=[]))

  fig = Figure(title='OS Versions', x_range=[], y_range=[0, 0], plot_width=1000, plot_height=650)

  hover = HoverTool(tooltips=[
    ('Users', '@height %')
  ])

  fig.add_tools(hover)

  fig.rect(x='x', y='y', height='height', source=source_release,
           width=0.4, color='orange', legend='Release')

  fig.rect(x='x', y='y', height='height', source=source_beta,
           width=0.4, color='blue', legend='Beta')

  fig.xaxis.major_label_orientation = np.pi / 3

  def update_view():
    os = osSelect.value
    versionNames = getOSVersionNames('release', os, True)

    versionCheckbox.labels = versionNames

    versions = [versionNames[i] for i in range(len(versionNames)) if i in versionCheckbox.active]

    releaseUsers = 100 * getUsersForVersions('release', os, versions) / osTotalReleaseUsers
    betaUsers = 100 * getUsersForVersions('beta', os, versions) / osTotalBetaUsers

    fig.x_range.factors = versions
    fig.y_range.end = max([releaseUsers.max(), betaUsers.max()])

    source_release.data = dict(
      x=[c + ':0.3' for c in versions],
      y=releaseUsers / 2,
      height=releaseUsers,
    )

    source_beta.data = dict(
      x=[c + ':0.7' for c in versions],
      y=betaUsers / 2,
      height=betaUsers,
    )

  def update(attrname, old, new):
    versionCheckbox.active = [i for i in range(5)]
    update_view()

  def click(selected):
    update_view()

  osSelect.on_change('value', update)
  versionCheckbox.on_click(click)

  update('value', '', osSelect.value)

  versionComparison = HBox(HBox(VBoxForm(*[osSelect, versionCheckbox]), width=300), fig, width=1100)

  return Panel(child=versionComparison, title="OS Version Comparison")

gfxData = data['graphics']

for i in range(len(versions)):
  version = versions[i]
  for vendor in gfxData[version]['gfxs']:
    for device in gfxData[version]['gfxs'][vendor]['devices']:
      for j in range(len(versions)):
        other_version = versions[j]
        if vendor not in gfxData[other_version]['gfxs']:
          gfxData[other_version]['gfxs'][vendor] = dict(
            total=0,
            devices=dict(),
          )
        if device not in gfxData[other_version]['gfxs'][vendor]['devices']:
          gfxData[other_version]['gfxs'][vendor]['devices'][device] = dict(
            total=0,
            versions=dict(),
          )


def getVendorNames(version, sort=False):
  if sort:
    return [v for v, u in sorted(gfxData[version]['gfxs'].iteritems(), key=lambda (v, u): u['total'], reverse=True)]
  else:
    return [v for v in gfxData['release']['gfxs']]

gfxVendors = getVendorNames('release', True)
gfxTotalReleaseUsers = gfxData['release']['total']
gfxTotalBetaUsers = gfxData['beta']['total']


def getDeviceNames(version, vendor, sort=False):
  if sort:
    return [d for d, v in sorted(gfxData[version]['gfxs'][vendor]['devices'].iteritems(), key=lambda (d, v): v['total'], reverse=True)]
  else:
    return [d for d in gfxData[version]['gfxs'][vendor]['devices']]


def getUsersForVendors(version, vendors=gfxVendors):
  values = []
  for vendor in vendors:
    for k, v in gfxData[version]['gfxs'].iteritems():
      if k == vendor:
        values.append(v['total'])
        break

  return np.array(values, dtype=np.float)


def getUsersForDevices(version, vendor, devices=None):
  if devices is None:
    devices = getDeviceNames('release', vendor, True)

  values = []
  for device in devices:
    for k, v in gfxData[version]['gfxs'][vendor]['devices'].iteritems():
      if k == device:
        values.append(v['total'])
        break

  return np.array(values, dtype=np.float)


def buildVendorsTab():
  defaultGfxVendors = [
    gfxVendors.index('NVIDIA Corporation'),
    gfxVendors.index('Advanced Micro Devices, Inc. [AMD/ATI]'),
    gfxVendors.index('Intel Corporation')
  ]

  gfxVendorCheckbox = CheckboxGroup(labels=gfxVendors, active=defaultGfxVendors)

  source_release = ColumnDataSource(data=dict(x=[], y=[], height=[]))
  source_beta = ColumnDataSource(data=dict(x=[], y=[], height=[]))

  fig = Figure(title="GFX Vendors",
               x_range=[],
               y_range=[0, 0],
               plot_width=1000, plot_height=650)

  hover = HoverTool(tooltips=[
    ('Users', '@height %')
  ])

  fig.add_tools(hover)

  fig.rect(x='x', y='y', height='height', source=source_release,
           width=0.4, color='orange', legend='Release')

  fig.rect(x='x', y='y', height='height', source=source_beta,
           width=0.4, color='blue', legend='Beta')

  fig.xaxis.major_label_orientation = np.pi / 3

  def update(selected):
    vendors = [gfxVendors[i] for i in range(len(gfxVendors)) if i in selected]

    releaseUsers = 100 * getUsersForVendors('release', vendors) / gfxTotalReleaseUsers
    betaUsers = 100 * getUsersForVendors('beta', vendors) / gfxTotalBetaUsers

    fig.x_range.factors = vendors
    fig.y_range.end = max([releaseUsers.max(), betaUsers.max()])

    source_release.data = dict(
      x=[c + ':0.3' for c in vendors],
      y=releaseUsers / 2,
      height=releaseUsers,
    )

    source_beta.data = dict(
      x=[c + ':0.7' for c in vendors],
      y=betaUsers / 2,
      height=betaUsers,
    )

  gfxVendorCheckbox.on_click(update)

  update(gfxVendorCheckbox.active)

  vendorComparison = HBox(HBox(VBoxForm(*[gfxVendorCheckbox]), width=300), fig, width=1100)

  return Panel(child=vendorComparison, title="GFX Vendor Comparison")


def buildDevicesTab():
  gfxVendorSelect = Select(title='Vendor', options=gfxVendors, value=gfxVendors[0])
  gfxDeviceCheckbox = CheckboxGroup()

  source_release = ColumnDataSource(data=dict(x=[], y=[], height=[]))
  source_beta = ColumnDataSource(data=dict(x=[], y=[], height=[]))

  fig = Figure(title="GFX Devices",
               x_range=[],
               y_range=[0, 0],
               plot_width=1000, plot_height=650)

  hover = HoverTool(tooltips=[
    ('Users', '@height %')
  ])

  fig.add_tools(hover)

  fig.rect(x='x', y='y', height='height', source=source_release,
           width=0.4, color='orange', legend='Release')

  fig.rect(x='x', y='y', height='height', source=source_beta,
           width=0.4, color='blue', legend='Beta')

  fig.xaxis.major_label_orientation = np.pi / 3

  def update_view():
    vendor = gfxVendorSelect.value
    deviceNames = getDeviceNames('release', vendor, True)

    gfxDeviceCheckbox.labels = deviceNames

    devices = [deviceNames[i] for i in range(len(deviceNames)) if i in gfxDeviceCheckbox.active]

    releaseUsers = 100 * getUsersForDevices('release', vendor, devices) / gfxTotalReleaseUsers
    betaUsers = 100 * getUsersForDevices('beta', vendor, devices) / gfxTotalBetaUsers

    fig.x_range.factors = devices
    fig.y_range.end = max([releaseUsers.max(), betaUsers.max()])

    source_release.data = dict(
      x=[c + ':0.3' for c in devices],
      y=releaseUsers / 2,
      height=releaseUsers,
    )

    source_beta.data = dict(
      x=[c + ':0.7' for c in devices],
      y=betaUsers / 2,
      height=betaUsers,
    )

  def update(attrname, old, new):
    gfxDeviceCheckbox.active = [i for i in range(5)]
    update_view()

  def click(selected):
    update_view()

  gfxVendorSelect.on_change('value', update)
  gfxDeviceCheckbox.on_click(click)

  update('value', '', gfxVendorSelect.value)

  deviceComparison = HBox(HBox(VBoxForm(*[gfxVendorSelect, gfxDeviceCheckbox]), width=300), fig, width=1100)

  return Panel(child=deviceComparison, title="GFX Device Comparison")

tabs = Tabs(tabs=[buildOSesTab(), buildOSVersionsTab(), buildVendorsTab(), buildDevicesTab()])
curdoc().add_root(tabs)

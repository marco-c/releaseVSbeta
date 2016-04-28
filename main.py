from bokeh.plotting import curdoc, Figure
from bokeh.models import ColumnDataSource, HoverTool, HBox, VBoxForm
from bokeh.models.widgets import Select, Panel, Tabs, CheckboxGroup
import json
import numpy as np
import tarfile
import os.path

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


def buildOsesTab():
  osesCheckbox = CheckboxGroup(labels=oses, active=[i for i in range(len(oses))])

  source_release = ColumnDataSource(data=dict(x=[], y=[], height=[]))
  source_beta = ColumnDataSource(data=dict(x=[], y=[], height=[]))

  fig = Figure(title='OS', x_range=[], y_range=[0, 0], plot_width=1000, plot_height=650)

  hover = HoverTool(tooltips=[
    ('Users', '@height{0.0} %')
  ])

  fig.add_tools(hover)

  fig.rect(x='x', y='y', height='height', source=source_release,
           width=0.4, color='orange', legend='Release')

  fig.rect(x='x', y='y', height='height', source=source_beta,
           width=0.4, color='blue', legend='Beta')

  fig.xaxis.major_label_orientation = np.pi / 3

  def update(selected):
    cur_oses = [oses[i] for i in range(len(oses)) if i in selected]

    releaseUsers = np.around(100 * getUsersForOses('release', cur_oses) / osTotalReleaseUsers, 1)
    betaUsers = np.around(100 * getUsersForOses('beta', cur_oses) / osTotalBetaUsers, 1)

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

'''def getWindowsVersionsChart():
  windowsVersions = []
  for version in versions:
    for key in data['platforms']['release']['oses']['Windows']['versions']:
      windowsVersions.append({
        'version': version,
        'os_version': key,
        'users': data['platforms'][version]['oses']['Windows']['versions'][key],
      })

  return Bar(pd.DataFrame(windowsVersions), label='os_version', values='users', group='version',
            title="All", legend='top_right', bar_width=0.4)'''

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
    devices = getDeviceNames('release', vendor)

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
    ('Users', '@height{0.0} %')
  ])

  fig.add_tools(hover)

  fig.rect(x='x', y='y', height='height', source=source_release,
           width=0.4, color='orange', legend='Release')

  fig.rect(x='x', y='y', height='height', source=source_beta,
           width=0.4, color='blue', legend='Beta')

  fig.xaxis.major_label_orientation = np.pi / 3

  def update(selected):
    vendors = [gfxVendors[i] for i in range(len(gfxVendors)) if i in selected]

    releaseUsers = np.around(100 * getUsersForVendors('release', vendors) / gfxTotalReleaseUsers, 1)
    betaUsers = np.around(100 * getUsersForVendors('beta', vendors) / gfxTotalBetaUsers, 1)

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
    ('Users', '@height{0.0} %')
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

    releaseUsers = np.around(100 * getUsersForDevices('release', vendor, devices) / gfxTotalReleaseUsers, 1)
    betaUsers = np.around(100 * getUsersForDevices('beta', vendor, devices) / gfxTotalBetaUsers, 1)

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

tabs = Tabs(tabs=[buildOsesTab(), buildVendorsTab(), buildDevicesTab()])
curdoc().add_root(tabs)

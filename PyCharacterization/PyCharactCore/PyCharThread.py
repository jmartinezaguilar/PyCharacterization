# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 10:56:29 2020

@author: Javier
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import numpy as np
import PyCharactCore.PyCharCore as CoreMod
import PyCharactCore.HwConf.HwConfig as BoardConf
import copy


SampSettingConf = ({'title': 'Channels Config',
                    'name': 'ChsConfig',
                    'type': 'group',
                    'children': ({'title': 'Acquire DC',
                                  'name': 'AcqDC',
                                  'type': 'bool',
                                  'value': True},
                                 {'title': 'Acquire AC',
                                  'name': 'AcqAC',
                                  'type': 'bool',
                                  'value': False},
                                 {'title': 'Gain DC',
                                  'name': 'DCGain',
                                  'type': 'float',
                                  'value': 10e3,
                                  'siPrefix': True, },
                                 {'title': 'Gain AC',
                                  'name': 'ACGain',
                                  'type': 'float',
                                  'value': 1e6,
                                  'siPrefix': True, },
                                 {'tittle': 'Selected Board',
                                  'name': 'Board',
                                  'type': 'list',
                                  'values': ['MainBoard',
                                             'MainBoard_8x8',
                                             'MainBoard_16x16',
                                             'Mos2',
                                             'MB41',
                                             'MB42'], },
                                 {'tittle': 'Row Channels',
                                  'name': 'Channels',
                                  'type': 'group',
                                  'children': (), },

                                 ), },

                   {'name': 'Sampling Settings',
                    'type': 'group',
                    'children': ({'tittle': 'Analog Outputs',
                                  'name': 'AnalogOutputs',
                                  'type': 'group',
                                  'children': (), }, ), }
                   )

ChannelParam = {'name': 'Chx',
                'type': 'bool',
                'value': True}

AnalogOutParam = {'name': 'Aox',
                  'type': 'float',
                  'value': 0.1}

###############################################################################


class SampSetParam(pTypes.GroupParameter):
    NewConf = Qt.pyqtSignal()

    Columns = []
    Rows = []
    Acq = {}
    HwSettings = {}

    def __init__(self, **kwargs):
        super(SampSetParam, self).__init__(**kwargs)
        self.addChildren(SampSettingConf)

        self.SampSet = self.param('Sampling Settings')
        self.AnalogOutputs = self.SampSet.param('AnalogOutputs')

        self.ChsConfig = self.param('ChsConfig')
        self.Config = self.ChsConfig.param('Board')
        self.RowChannels = self.ChsConfig.param('Channels')

        # Init Settings
        self.on_Acq_Changed()
        self.on_Row_Changed()
        self.on_Ao_Changed()

        print(self.children())
        # Signals
        self.Config.sigTreeStateChanged.connect(self.Hardware_Selection)
        self.RowChannels.sigTreeStateChanged.connect(self.on_Row_Changed)
        # self.ColChannels.sigTreeStateChanged.connect(self.on_Col_Changed)
        self.AnalogOutputs.sigTreeStateChanged.connect(self.on_Ao_Changed)
        self.ChsConfig.param('AcqAC').sigValueChanged.connect(self.on_Acq_Changed)
        self.ChsConfig.param('AcqDC').sigValueChanged.connect(self.on_Acq_Changed)

    def Hardware_Selection(self):
        print('Hardware_Selection')
        for k in BoardConf.HwConfig:
            if k == self.Config.value():
                self.HwSettings = BoardConf.HwConfig[k]
        self.GetChannelsChildren()
        self.GetAnalogOutputs()

    def GetChannelsChildren(self):
        print('GetChannelsChildren')
        if self.HwSettings:
            self.RowChannels.clearChildren()
            for i in sorted(self.HwSettings['aiChannels']):
                cc = copy.deepcopy(ChannelParam)
                cc['name'] = i
                print(i)
                self.RowChannels.addChild(cc)

    def GetAnalogOutputs(self):
        print('GetAnalogOutputs')
        if self.HwSettings:
            self.AnalogOutputs.clearChildren()
            for i, k in sorted(self.HwSettings['aoChannels'].items()):
                print(i, k)
                if any([i == 'ChAo2', i == 'ChAo3']) and k is not None:
                    cc = copy.deepcopy(AnalogOutParam)
                    cc['name'] = i
                    self.AnalogOutputs.addChild(cc)

    def on_Acq_Changed(self):
        for p in self.ChsConfig.children():
            if p.name() is 'AcqAC':
                self.Acq[p.name()] = p.value()
            if p.name() is 'AcqDC':
                self.Acq[p.name()] = p.value()
        self.NewConf.emit()

    def on_Row_Changed(self):
        self.Rows = []
        for p in self.RowChannels.children():
            if p.value() is True:
                self.Rows.append(p.name())
        self.NewConf.emit()

    def on_Ao_Changed(self):
        self.Ao = {}
        for p in self.AnalogOutputs.children():
            self.Ao[p.name()] = p.value()
        self.NewConf.emit()

    def GetRowNames(self):
        Ind = 0
        RowNames = {}

        if self.ChsConfig.param('AcqDC').value():
            for Row in self.Rows:
                RowNames[Row + 'DC'] = Ind
                Ind += 1

        if self.ChsConfig.param('AcqAC').value():
            for Row in self.Rows:
                RowNames[Row + 'AC'] = Ind
                Ind += 1

        return RowNames

    def GetChannelsNames(self):
        Ind = 0
        ChannelNames = {}

        if self.ChsConfig.param('AcqDC').value():
            for Row in self.Rows:
                    ChannelNames[Row] = Ind
                    Ind += 1

        return ChannelNames

    def GetSampKwargs(self):
        GenKwargs = {}
        for p in self.SampSet.children():
            print(p.name(), '-->', p.value())
            if p.name() == 'AnalogOutputs':
                GenKwargs[p.name()] = self.Ao
                print(self.Ao)
            else:
                GenKwargs[p.name()] = p.value()
        print(GenKwargs)
        return GenKwargs

    def GetChannelsConfigKwargs(self):
        ChanKwargs = {}
        for p in self.ChsConfig.children():
            if p.name() == 'Channels':
                ChanKwargs[p.name()] = self.Rows
            else:
                ChanKwargs[p.name()] = p.value()

        return ChanKwargs

###############################################################################


class DataAcquisitionThread(Qt.QThread):
    NewMuxData = Qt.pyqtSignal()

    def __init__(self, ChannelsConfigKW, SampKw):
        super(DataAcquisitionThread, self).__init__()
        self.DaqInterface = CoreMod.ChannelsConfig(**ChannelsConfigKW)
        self.DaqInterface.DataEveryNEvent = self.NewData
        self.SampKw = SampKw
        print('SampKWKWKW')
        print(SampKw)

    def run(self, *args, **kwargs):
        self.DaqInterface.StartAcquisition(**self.SampKw)
        loop = Qt.QEventLoop()
        loop.exec_()


    def NewData(self, aiDataDC, aiDataAC):
        self.OutDataDC = aiDataDC
        self.OutDataAC = aiDataAC

        self.NewMuxData.emit()
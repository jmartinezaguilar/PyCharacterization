# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 10:57:58 2020

@author: Javier
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 14:13:45 2019

@author: aguimera
"""
import PyqtTools.DaqInterface as DaqInt
import numpy as np
import PyCharactCore.HwConf.HwConfig as BoardConf


class ChannelsConfig():

    # DCChannelIndex[ch] = (index, sortindex)
    DCChannelIndex = None
    ACChannelIndex = None
    ChNamesList = None
    AnalogInputs = None
    DigitalOutputs = None
    MyConf = None
    AO2Out = None
    AO3Out = None
    InitSwitch = np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.uint8)
    DOSwitch = None
    DO = None
    IndexDigitalLines = None
    # Events list
    DataEveryNEvent = None
    DataDoneEvent = None

    def _InitAnalogInputs(self):
        print('InitAnalogInputs')
        print(self.Inds)
        self.DCChannelIndex = {}
        self.ACChannelIndex = {}
        InChans = []
        index = 0
        sortindex = 0
        for ch in self.ChNamesList:
            if self.Inds <= 1:
                InChans.append(self.aiChannels[ch])
                self.DCChannelIndex[ch] = (sortindex, sortindex)
                self.ACChannelIndex[ch] = (sortindex, sortindex)
            else:
                if self.AcqDC:
                    InChans.append(self.aiChannels[ch][0])
                    self.DCChannelIndex[ch] = (index, sortindex)
                    index += 1
                    print(ch, ' DC -->', self.aiChannels[ch][0])
                    print('SortIndex ->', self.DCChannelIndex[ch])
                if self.AcqAC:
                    InChans.append(self.aiChannels[ch][1])
                    self.ACChannelIndex[ch] = (index, sortindex)
                    index += 1
                    print(ch, ' AC -->', self.aiChannels[ch][1])
                    print('SortIndex ->', self.ACChannelIndex[ch])
            sortindex += 1
        print('Input ai', InChans)
        print(self.DCChannelIndex)
        self.AnalogInputs = DaqInt.ReadAnalog(InChans=InChans)
        # events linking
        self.AnalogInputs.EveryNEvent = self.EveryNEventCallBack
        self.AnalogInputs.DoneEvent = self.DoneEventCallBack

    def _InitDigitalOutputs(self):
        print('InitDigitalOutputs')
        print(self.DigColumns)
        DOChannels = []

        # for digc in sorted(self.DigColumns):
        for k, v in self.doColumns.items():
            DOChannels.append(v[0])
            if len(v) > 1:
                DOChannels.append(v[1])
                
        print(DOChannels)

        self.DigitalOutputs = DaqInt.WriteDigital(Channels=DOChannels)

    def _InitDecoderOutputs(self):
        
        self.DigitalOutputs = DaqInt.WriteDigital(Channels=['port0/line9:15', ])
        print('InitDecoderOutputs')

    def _InitAnalogOutputs(self, ChVds, ChVs, ChAo2, ChAo3):
        print('ChVds ->', ChVds)
        print('ChVs ->', ChVs)
        self.VsOut = DaqInt.WriteAnalog((ChVs,))
        self.VdsOut = DaqInt.WriteAnalog((ChVds,))
        if ChAo2:
            self.AO2Out = DaqInt.WriteAnalog((ChAo2,))
        if ChAo3:
            self.AO3Out = DaqInt.WriteAnalog((ChAo3,))

    def __init__(self, Channels, DigColumns,
                 AcqDC=True, AcqAC=True,
                 ChVds='ao0', ChVs='ao1',
                 ACGain=1.1e5, DCGain=10e3, Board='MB41'):
        print('InitChannels')
        # self._InitAnalogOutputs(ChVds=ChVds, ChVs=ChVs)

        self.ChNamesList = sorted(Channels)
        # Fix AC and DC config as True
        print(self.ChNamesList)
        self.AcqAC = AcqAC
        self.AcqDC = True
        self.ACGain = ACGain
        self.DCGain = DCGain
        print('Board---->', Board)

        self.MyConf = BoardConf.HwConfig[Board]
        self.aiChannels = self.MyConf['aiChannels']
        self.doColumns = self.MyConf['ColOuts']
        self.aoChannels = self.MyConf['aoChannels']
        self.DOSwitch = self.MyConf['DOSwitch']
        self._InitAnalogOutputs(ChVds=self.aoChannels['ChVds'],
                                ChVs=self.aoChannels['ChVs'],
                                ChAo2=self.aoChannels['ChAo2'],
                                ChAo3=self.aoChannels['ChAo3'],
                                )
        if Board == 'MainBoard_v3':
            self.Inds = 1
        else:
            self.Inds = 2

        self._InitAnalogInputs()

        self.DigColumns = sorted(DigColumns)
        if self.doColumns:
            if self.doColumns['Col01'] is None:
                self._InitDecoderOutputs()
            else:
                self._InitDigitalOutputs()

            MuxChannelNames = []
            for Row in self.ChNamesList:
                for Col in self.DigColumns:
                    MuxChannelNames.append(Row + Col)
            self.MuxChannelNames = MuxChannelNames
            print(self.MuxChannelNames)

        if self.DOSwitch:
            self.SwitchOut = DaqInt.WriteDigital(Channels=self.DOSwitch)
            self.SwitchOut.SetDigitalSignal(Signal=self.InitSwitch)
            # self.SetDigitalSignal(Signal=self.InitSwitch)

    def StartAcquisition(self, Fs, nSampsCo, nBlocks, Vgs, Vds,
                         AnalogOutputs, **kwargs):
        print('StartAcquisition')
        print(AnalogOutputs)
        if AnalogOutputs:
            ChAo2 = AnalogOutputs['ChAo2']
            ChAo3 = AnalogOutputs['ChAo3']
        else:
            ChAo2 = None
            ChAo3 = None
        self.SetBias(Vgs=Vgs, Vds=Vds, ChAo2=ChAo2, ChAo3=ChAo3)

        if self.doColumns:
            if self.doColumns['Col01'] is None:
                DO, self.IndexDigitalLines = self.GetDecoderSignal()
                self.DO = np.array(DO, dtype=np.uint8)
            else:
                self.DO, self.IndexDigitalLines = self.SetDigitalOutputs(nSampsCo=nSampsCo)

        print('DSig set')

        self.nBlocks = nBlocks
        self.nSampsCo = nSampsCo
#        self.OutputShape = (nColumns * nRows, nSampsCh, nblocs)
        # self.OutputShape = (len(self.MuxChannelNames), nSampsCo, nBlocks)
        EveryN = nSampsCo*nBlocks
        self.AnalogInputs.ReadContData(Fs=Fs,
                                       EverySamps=EveryN)

    def SetBias(self, Vgs, Vds, ChAo2, ChAo3):
        print('ChannelsConfig SetBias Vgs ->', Vgs, 'Vds ->', Vds,
              'Ao2 ->', ChAo2, 'Ao3 ->', ChAo3,)
        self.VdsOut.SetVal(Vds)
        self.VsOut.SetVal(-Vgs)
        if self.AO2Out:
            self.AO2Out.SetVal(ChAo2)
        if self.AO3Out:
            self.AO3Out.SetVal(ChAo3)
        self.BiasVd = Vds-Vgs
        self.Vgs = Vgs
        self.Vds = Vds

    def SetDigitalOutputs(self, nSampsCo):
        hwLinesMap = {}
        IndexDigitalLines = {}
        i = 0
        for ColName, hwLine in self.doColumns.items():
            il = int(hwLine[0][4:])
            hwLinesMap[il] = (ColName, hwLine)
            IndexDigitalLines[i] = ColName
            i += 1
        
        # Gen inverted control output, should be the next one of the digital line ('lineX', 'lineX+1')
        if len(self.doColumns[ColName]) > 1:
            GenInvert = True
        else:
            GenInvert = False

        nSampsCo = 1
        # Gen sorted indexes for demuxing
        SortIndDict = {}
        for ic, coln in enumerate(sorted(self.DigColumns)):
            SortIndDict[coln] = ic
        
        DOut = np.array([], dtype=np.bool)
        SortDInds = np.zeros((len(self.DigColumns), nSampsCo), dtype=np.int64)
        SwitchOrder = 0
        for il, (nLine, (LineName, hwLine)) in enumerate(sorted(hwLinesMap.items())):
            Lout = np.zeros((1, nSampsCo*len(self.DigColumns)), dtype=np.bool)    
            if LineName in self.DigColumns:
                # print(il, nLine, hwLine, LineName)
                Lout[0, nSampsCo * SwitchOrder: nSampsCo * (SwitchOrder + 1)] = True
                SortDInds[SortIndDict[LineName], : ] = np.arange(nSampsCo * SwitchOrder,
                                                             nSampsCo * (SwitchOrder + 1) )
                SwitchOrder += 1
            
            if GenInvert:
                Cout = np.vstack((Lout, ~Lout))
            else:
                Cout = Lout        
            DOut = np.vstack((DOut, Cout)) if DOut.size else Cout

        SortDIndsL = [inds for inds in SortDInds]
        Dout = DOut.astype(np.uint8)

        self.SortDInds = SortDInds
        # self.DigitalOutputs.SetDigitalSignal(Signal=DOut.astype(np.uint8))
        return Dout, IndexDigitalLines

    def GetDecoderSignal(self):
        print('GETDECODERSIGNAL')
        Decoder = self.DecoderDigital(5)
        Dec = np.array(Decoder, dtype=np.uint8)
        DOut = np.array([])
        IndexDigitalLines = {}

        index = 0
        for n, i in self.doColumns.items():
            if n in self.DigColumns:
                IndexDigitalLines[index] = n
                Cout = Dec[index]
                DOut = np.vstack((DOut, Cout)) if DOut.size else Cout
                index += 1
        return DOut.transpose(), IndexDigitalLines
        
    def DecoderDigital(self, n):
        if n < 1:
            return[[]]
        subtable = self.DecoderDigital(n-1)
        return [row+[v] for row in subtable for v in [0,1]]
    
    def _SortChannels(self, data, SortDict):
        # Sort by aianalog input
        (samps, inch) = data.shape
        aiData = np.zeros((samps, len(SortDict)))
        for chn, inds in sorted(SortDict.items()):
            if self.Inds <= 1:
                aiData[:, inds] = data[:, inds]
            else:
                aiData[:, inds[1]] = data[:, inds[0]]

        # Sort by digital columns
        aiData = aiData.transpose()
        # MuxData = np.ndarray(self.OutputShape)

        # if self.doColumns:
        #     nColumns = len(self.DigColumns)
        #     for indB in range(self.nBlocks):
        #         startind = indB * self.nSampsCo * nColumns
        #         stopind = self.nSampsCo * nColumns * (indB + 1)
        #         Vblock = aiData[:, startind: stopind]
        #         ind = 0
        #         for chData in Vblock[:, :]:
        #             for Inds in self.SortDInds:
        #                 MuxData[ind, :, indB] = chData[Inds]
        #                 ind += 1
        return aiData

    def EveryNEventCallBack(self, Data):
        _DataEveryNEvent = self.DataEveryNEvent
        aiDataDC = None
        aiDataAC = None

        if _DataEveryNEvent is not None:
            if self.AcqDC:
                aiDataDC = self._SortChannels(Data, self.DCChannelIndex)
                aiDataDC = (aiDataDC-self.BiasVd) / self.DCGain
            if self.AcqAC:
                aiDataAC = self._SortChannels(Data, self.ACChannelIndex)
                aiDataAC = aiDataAC / self.ACGain

            _DataEveryNEvent(aiDataDC, aiDataAC, )

            # if self.AcqAC and self.AcqDC:
            #     aiData = np.vstack((aiDataDC, aiDataAC))
            #     _DataEveryNEvent(aiData)
            # elif self.AcqAC:
            #     _DataEveryNEvent(aiDataAC)
            # elif self.AcqDC:
            #     _DataEveryNEvent(aiDataDC)

    def DoneEventCallBack(self, Data):
        print('Done callback')

    def Stop(self):
        print('Stopppp')
        self.SetBias(Vgs=0, Vds=0, ChAo2=0, ChAo3=0)
        self.AnalogInputs.StopContData()
        if self.DigitalOutputs is not None:
            print('Clear Digital')
#            self.DigitalOutputs.SetContSignal(Signal=self.ClearSig)
            self.DigitalOutputs.ClearTask()
            self.DigitalOutputs = None


#    def __del__(self):
#        print('Delete class')
#        self.Inputs.ClearTask()
#

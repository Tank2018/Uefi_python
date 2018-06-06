# -*- coding: utf-8 -*-
import os
import sys
import uuid
import copy
import struct
from firmwarevolume import *

class Firmware:
    """
    define firmwareObj
    {
        firmwareObjName
        firmwareObjSize
        firmwareObjData
        fvCount
        fvOffset
    }
    """
    byte_align = 16
    def __init__(self, firmwareObjName):
        self.firmwareObjName = firmwareObjName
        firmwareObjFile = open(self.firmwareObjName, 'r+b')
        self.firmwareObjSize = os.path.getsize(self.firmwareObjName)
        self.firmwareObjData = firmwareObjFile.read()
        self.firmwareVolumeList = []
        firmwareObjFile.close()


    """
    found the fv count & init fv offset
    """
    def process(self):
        byte_align = 0x1000
        '''find the fv offset of the bios by fv guid'''
        data = self.firmwareObjData
        volumesOffset = []
        fvList = []
        count = 0;
        for aligned in xrange(0, len(data), byte_align):
            if data[aligned+0x28:aligned+0x28+4] == '_FVH':
                volumesOffset.append(aligned)
                count += 1

        for index in range(0, count, 1):
            fvData = self.firmwareObjData[volumesOffset[index]:]
            firmwareVolume = FirmwareVolume(fvData)
            if (firmwareVolume.size != 0) :
                fvList.append(firmwareVolume)

                firmwareVolume.showinfo()
                firmwareVolume.process()
        self.firmwareVolumeList = fvList
        """
        for fv in fvList:
            fv.showinfo()
            fv.process()
        return
       """
    def showFirmwareInfo(self):
        return

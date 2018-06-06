# -*- coding: utf-8 -*-
import os
import sys
import uuid
import copy
import struct
from guid import *
import firmwarevolume
from section import *




FILE_STATE = {
    "FILE_HEADER_CONSTRUCTION":  0x01,
    "FILE_HEADER_VALID":          0x02,
    "FILE_DATA_VALID":            0x04,
    "FILE_MARKED_FOR_UPDATE":       0x08,
    "FILE_DELETED":                 0x10,
    "FILE_HEADER_INVALID":          0x20,
}
class FirmwareFileSystem:
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
    _HEADER_LEN = 0x18
    def __init__(self, firmwareFileSystemData):
        """
        typedef struct {
            EFI_GUID                Name;
            EFI_FFS_INTEGRITY_CHECK IntegrityCheck;
            EFI_FV_FILETYPE         Type;
            EFI_FFS_FILE_ATTRIBUTES Attributes;
            UINT8                   Size[3];
            EFI_FFS_FILE_STATE      State;
        } EFI_FFS_FILE_HEADER;
        :param firmwareFileSystemData:
        """
        header = firmwareFileSystemData[:self._HEADER_LEN]

        try:
            self.guid, self.checksum, self.type, self.attributes, \
                self.size, self.state = struct.unpack("<16sHBB3sB", header)
            self.size = struct.unpack("<I", self.size + "\x00")[0]
        except Exception as e:
            print("Error: invalid FirmwareFile header.")
            raise e
        self.data = firmwareFileSystemData[0:self.size]
        pass
        self.sectionList = []

    """
    found the fv count & init fv offset
    """
    def process(self):
        data = self.data[self._HEADER_LEN:]
        i = 0
        size = self.size
        sectionList = []
        while i < size :
            if len(data[i:]) < 4 :
                break
            section = Section(data[i:])
            i += section.size
            sectionList.append(section)
            section.process()
            section.showinfo()


        self.sectionList = sectionList

    def getFfsType(self):
        FFS_TYPE = {
            "EFI_FV_FILETYPE_ALL":                   0x00,
            "EFI_FV_FILETYPE_RAW":                   0x01,
            "EFI_FV_FILETYPE_FREEFORM":             0x02,
            "EFI_FV_FILETYPE_SECURITY_CORE":       0x03,
            "EFI_FV_FILETYPE_PEI_CORE":             0x04,
            "EFI_FV_FILETYPE_DXE_CORE":             0x05,
            "EFI_FV_FILETYPE_PEIM":                  0x06,
            "EFI_FV_FILETYPE_DRIVER":                0x07,
            "EFI_FV_FILETYPE_COMBINED_PEIM_DRIVER":  0x08,
            "EFI_FV_FILETYPE_APPLICATION":           0x09,
            "EFI_FV_FILETYPE_SMM":                  0x0A,
            "EFI_FV_FILETYPE_FIRMWARE_VOLUME_IMAGE":0x0B,
            "EFI_FV_FILETYPE_COMBINED_SMM_DXE":      0x0C,
            "EFI_FV_FILETYPE_SMM_CORE":              0x0D,
            "EFI_FV_FILETYPE_OEM_MIN":               0xc0,
            "EFI_FV_FILETYPE_OEM_MAX":               0xdf,
            "EFI_FV_FILETYPE_DEBUG_MIN":             0xe0,
            "EFI_FV_FILETYPE_DEBUG_MAX":             0xef,
            "EFI_FV_FILETYPE_FFS_MIN":               0xf0,
            "EFI_FV_FILETYPE_FFS_MAX":               0xff,
            "EFI_FV_FILETYPE_FFS_PAD":               0xf0,
        }
        for item,value in FFS_TYPE.items():
            if self.type == value:
                return item
        return "unkonuw"

    def getFfsState(self, erasePolarity):
        state = self.state
        if erasePolarity == True:
            state = ~state
        data = 0x80
        while (data != 0) and ((data & state) == 0):
            data = data >> 1
        return data

    def isFfsHeaderVaild(self, erasePolarity):
        state = self.getFfsState(erasePolarity)
        if state >= FILE_STATE["FILE_DELETED"]:
            return False
        header = self.data[:self._HEADER_LEN]
        sum = 0
        for i in header:
            sum += ord(i)
            sum &= 0xff
        if (sum - self.state - (self.checksum >>8) & 0xff) == 0:
            return True
        return False

    def show(self):
        print  "  ffs:{",(sguid(self.guid), self.checksum, self.getFfsType(), self.attributes, \
                self.size, self.state),"}"
        pass

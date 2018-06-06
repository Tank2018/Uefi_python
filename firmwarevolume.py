import os
import sys
import uuid
import copy
import struct

from guid import *
from ffs import *

FIRMWARE_VOLUME_GUIDS = {
    "FFS1":        "7a9354d9-0468-444a-81ce-0bf617d890df",
    "FFS2":        "8c8ce578-8a3d-4f1c-9935-896185c32dd3",
    "FFS3":        "5473c07a-3dcb-4dca-bd6f-1e9689e7349a",
    "NVRAM_EVSA":  "fff12b8d-7696-4c8b-a985-2747075b4f50",
    "NVRAM_NVAR":  "cef5b9a3-476d-497f-9fdc-e98143e0422c",
    "NVRAM_EVSA2": "00504624-8a59-4eeb-bd0f-6b36e96128e0",
}

class FirmwareVolume:

    _HEADER_SIZE = 0x38
    GUID_LEN = 16
    EFI_FVB2_ERASE_POLARITY = 0x00000800
    def __init__(self, fvData):
        self.ffsList = []
        header = fvData[0:self._HEADER_SIZE]
        """
    ///
    /// Describes the features and layout of the firmware volume.
    ///
    typedef struct {
      UINT8                     ZeroVector[16];
      EFI_GUID                  FileSystemGuid;
      UINT64                    FvLength;
      UINT32                    Signature;
      EFI_FVB_ATTRIBUTES_2      Attributes;
      UINT16                    HeaderLength;
      UINT16                    Checksum;
      UINT16                    ExtHeaderOffset;
      UINT8                     Reserved[1];
      UINT8                     Revision;
      EFI_FV_BLOCK_MAP_ENTRY    BlockMap[1];
    } EFI_FIRMWARE_VOLUME_HEADER;
        """
        self.exFvGuid = 0
        self.exFvSize = 0
        self.exFvOffset = 0
        self.erasePolarity = 0
        try:
            self.rsvd, self.guid, self.size, self.magic, self.attributes, \
                self.hdrlen, self.checksum, self.rsvd2, \
                self.revision = struct.unpack("<16s16sQ4sIHH3sB", header)
        except Exception as e:
            print "Error: cannot parse FV header (%s)." % str(e)
            return
        self.fvData = fvData[0:self.size]
        ffs_guids = [
            FIRMWARE_VOLUME_GUIDS["FFS1"],
            FIRMWARE_VOLUME_GUIDS["FFS2"],
            FIRMWARE_VOLUME_GUIDS["FFS3"],
        ]
        if sguid(self.guid) not in ffs_guids:
            self.size = 0
            return
       # print(sguid(self.guid), hex(self.size), self.magic, hex(self.attributes),hex(self.hdrlen))

        if self.attributes and self.EFI_FVB2_ERASE_POLARITY != 0:
            self.erasePolarity = 1
        #print(sguid(self.guid), hex(self.size), self.magic, hex(self.attributes), hex(self.hdrlen), hex(self.erasePolarity))

        self.exFvOffset, rsvd = struct.unpack("<HB", self.rsvd2)
        if self.exFvOffset:
            exFv = fvData[self.exFvOffset:self.exFvOffset + 0x14]
            self.exFvGuid, self.exFvSize = struct.unpack("<16sI", exFv)

        """
        data = fvData
        self.blocks = []
        self.block_map = ""
        try:
            data = data[:self.size]

            self._data = data
            self.data = data[self.hdrlen:]
            self.block_map = data[self._HEADER_SIZE:self.hdrlen]
        except Exception as e:
            print ("Error invalid FV header data (%s)." % str(e))
            return
        block_data = self.block_map
        while len(block_data) > 0:
            block = block_data[:8]

            block_size, block_length = struct.unpack("<II", block)
            if (block_size, block_length) == (0, 0):
                '''The block map ends with a (0, 0) block.'''
                break

            self.blocks.append((block_size, block_length))
            block_data = block_data[8:]
        for blockdata in self.blocks:
            print (blockdata)
        """
    pass
    def showinfo(self):
        print "FV:{",(sguid(self.guid), hex(self.size), self.magic, hex(self.attributes), hex(self.hdrlen), hex(self.erasePolarity)),"}"
        pass
    def process(self):

        ffsList=[]
        alin = 8
        data = self.fvData[self.hdrlen:]
        if self.exFvOffset != 0:
            offset = self.exFvSize+self.exFvOffset
            offset = ((offset + 7) & (~7))
            data = self.fvData[offset:]
        while len(data) >= 24 and data[:24] != ("\xff" * 24):
            ffs = FirmwareFileSystem(data)
            state = ffs.getFfsState(self.erasePolarity)
            if state == FILE_STATE["FILE_DELETED"] or state  == FILE_STATE["FILE_MARKED_FOR_UPDATE"]:
                data = data[(ffs.size + 7) & (~7):]
                continue
            if state == FILE_STATE["FILE_DATA_VALID"]:
                if ffs.isFfsHeaderVaild(self.erasePolarity) == True:
                    if ffs.guid != ("\xff" * 16):
                        ffsList.append(ffs)
                data = data[(ffs.size + 7) & (~7):]
                continue
            data = data[8:]
        for ffs1 in ffsList:
            ffs1.show()
            ffs1.process()
            if ffs1.getFfsType() == "EFI_FV_FILETYPE_FIRMWARE_VOLUME_IMAGE":
                for section in ffs1.sectionList:
                    if section.getSectionType() == "EFI_SECTION_FIRMWARE_VOLUME_IMAGE":
                        fv = FirmwareVolume(section.data[4:])
                        fv.showinfo()
                        fv.process()
                    for s in section.list:
                        if s.getSectionType() == "EFI_SECTION_FIRMWARE_VOLUME_IMAGE":
                            fv = FirmwareVolume(s.data[4:])
                            fv.showinfo()
                            fv.process()

        pass


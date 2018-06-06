# -*- coding: utf-8 -*-
import os
import sys
import uuid
import copy
import struct

from guid import *
import efi_compressor

def decompress(algorithms, compressed_data):
    '''Attempt to decompress using a set of algorithms.

    Args:
        algorithms (list): A set of decompression methods.
        compressed_data (binary): A compressed data stream.

    Return:
        pair (int, binary): Return the algorithm index, and decompressed stream.
    '''
    for i, algorithm in enumerate(algorithms):
        try:
            data = algorithm(compressed_data, len(compressed_data))
            return (i, data)
        except Exception:
            continue
    return None

SECTION_GUIDED_GUIDS = {
    "LZMA_COMPRESSED": "ee4e5898-3914-4259-9d6e-dc7bd79403cf",
    "TIANO_COMPRESSED": "a31280ad-481e-41b6-95e8-127f4c984779",
    "FIRMWARE_VOLUME": "24400798-3807-4a42-b413-a1ecee205dd8",
    "STATIC_GUID": "fc1bcdb0-7d31-49aa-936a-a4600d9dd083",
    "AUTH_GUID_RSA2018_SHA256":"a7717414-c616-4977-9420-844712a735bf",
}



class GuidCompressSection():
    _HEADER_LEN = 0x18
    def __init__(self,data):
        """

        :param data:
        """
        header = data[:self._HEADER_LEN]

        try:
            self.size, self.type,self.guid,self.offset,self.attr = struct.unpack("<3sB16sHH", header)
            self.size = struct.unpack("<I", self.size + "\x00")[0]
        except Exception as e:
            print("Error: invalid GUID Section header.")
            raise e
        pass
        self.preamble = data[20:self.offset]
        self.data = data[self.offset:]
        self.guidCompresssectionList = []
        pass

    def process(self):
        data = self.data
        def decompress_guid(alg):
            # Try to decompress the body of the section.
            results = decompress([alg], self.preamble + self.data)
            if results is None:
                # Attempt to recover by skipping the preamble.
                results = decompress([alg], self.data)
                if results is None:
                    return False
            self.subtype = results[0] + 1
            self.data = results[1]
            return True
        status = True
        if sguid(self.guid) == SECTION_GUIDED_GUIDS["LZMA_COMPRESSED"]:
            status = decompress_guid(efi_compressor.LzmaDecompress)
        if sguid(self.guid) == SECTION_GUIDED_GUIDS["TIANO_COMPRESSED"]:
            status = decompress_guid(efi_compressor.TianoDecompress)

        if status == True:
            data = self.data
            size = 0
            guidCompresssectionList = []
            while size < len(self.data) and len(data) > 4:
                section = Section(data)
                data = data[size:]
                size += section.size
                guidCompresssectionList.append(section)
            self.guidCompresssectionList = guidCompresssectionList
        pass

class RS2048GuidSection():
    _RS2048_LEN = 552
    def __init__(self,data):
        """
        ///
        /// RSA 2048 SHA 256 Guided Section header
        ///
        typedef struct {
        EFI_GUID_DEFINED_SECTION        GuidedSectionHeader;     ///< EFI guided section header
        EFI_CERT_BLOCK_RSA_2048_SHA256  CertBlockRsa2048Sha256;  ///< RSA 2048-bit Signature
        } RSA_2048_SHA_256_SECTION_HEADER;
        """
        self.size = self._RS2048_LEN
        self.data = data
        pass

    def proess(self):
        pass

class GuidSection:
    _GUID_HEADER_LEN = 0x18
    def __init__(self, data):
        """
        typedef struct {
        EFI_COMMON_SECTION_HEADER   CommonHeader;
        EFI_GUID                    SectionDefinitionGuid;
        UINT16                      DataOffset;
        UINT16                      Attributes;
        } EFI_GUID_DEFINED_SECTION;
        """
        header = data[:self._GUID_HEADER_LEN]
        self.data = data
        try:
            self.size, self.type,self.guid,self.offset,self.attr = struct.unpack("<3sB16sHH", header)
            self.size = struct.unpack("<I", self.size + "\x00")[0]
        except Exception as e:
            print("Error: invalid GUID Section header.")
            raise e
        pass
        self.guidSectionList=[]

    def process(self):
        data = self.data[:self.size]
        size = self.size
        offset = 0
        compress = ["TIANO_COMPRESSED", "LZMA_COMPRESSED"]
        sectionList = []
        while  offset < size and data [0:16] != ("\xff" * 16):
            data = data[offset:]
            section = GuidSection(data)
            """if this is a rsa2048 signed fv, press this with authed status"""
            if section.getGuidSectionType() == "AUTH_GUID_RSA2018_SHA256":
                section = RS2048GuidSection(data)
                section.proess()
                offset += section.size
                sectionList.append(section)
                continue
            """if this is section type is compressed ,just process this"""
            if section.getGuidSectionType() in compress:
                section = GuidCompressSection(data)
                section.process()
                offset += section.size
                sectionList.append(section)
                for s in  section.guidCompresssectionList:
                    if s != []:
                        sectionList.append(s)
                continue
            """if this is section type is others ,just process this, TBD"""
            offset+= section.size
            sectionList.append(section)
        self.guidSectionList = sectionList
        pass

    def getGuidSectionAttr(self):
        SECTION_ATTR = {
            "EFI_GUIDED_SECTION_PROCESSING_REQUIRED":  0x01,
            "EFI_GUIDED_SECTION_AUTH_STATUS_VALID":    0x02,
        }
        attr = []
        for item,value in SECTION_ATTR.items():
            if self.attr and value != 0:
                attr.append(item)
        return attr

    def getGuidSectionType(self):
        for item,value in SECTION_GUIDED_GUIDS.items():
            if sguid(self.guid) == value:
                return item
        return Section(self.data).getSectionType()

class Section:
    _COMMON_HEADER_LEN = 0x4
    _COMMON_HEADER2_LEN = 0x8
    def __init__(self, data):
        """
        typedef struct {
        UINT8             Size[3];
        EFI_SECTION_TYPE  Type;
        } EFI_COMMON_SECTION_HEADER;
        """
        header = data[:self._COMMON_HEADER_LEN]
        self.data = data
        self.size = 0
        try:
            size, self.type = struct.unpack("<3sB", header)
            size = struct.unpack("<I", size + "\x00")[0]
        except Exception as e:
            print("Error: invalid Section header.")
            raise e
        pass

        if size == 0:
            try:
                size = struct.unpack("<I", data[self._COMMON_HEADER_LEN:self._COMMON_HEADER2_LEN])[0]
            except Exception as e:
                print("Error: invalid Section header2.")
                raise e
        self.size = size
        self.list = []

    """
    found the fv count & init fv offset
    """
    def process(self):
        data = self.data
        size = self.size
        type = self.getSectionType()
        list = []
        if type == "EFI_SECTION_COMPRESS":
            pass
        if type == "EFI_SECTION_GUID_DEFINED":
            guidSection = GuidSection(data)
            guidSection.process()
            if guidSection.guidSectionList != []:
                for section in guidSection.guidSectionList:
                    s = Section(section.data)
                    list.append(s)
        self.list = list

        """
        if self.getSectionType() == "EFI_SECTION_COMPRESSION":
            pass
        if self.getSectionType() == "EFI_SECTION_GUID_DEFINED":
            s = GuidSection (data)
            s.process()
            if s.guidSectionList != []:
                for guidSectionList in s.guidSectionList:
                    if guidSectionList != []:
                        self.sectionList.append(Section(guidSectionList.data))
            pass
        pass
        """

    def getSectionType(self):
        SECTION_TYPE = {
            "EFI_SECTION_ALL":                          0x00,
            "EFI_SECTION_COMPRESSION":                0x01,
            "EFI_SECTION_GUID_DEFINED":               0x02,
            "EFI_SECTION_DISPOSABLE":                 0x03,
            "EFI_SECTION_FIRST_LEAF_SECTION_TYPE":  0x10,
            "EFI_SECTION_PE32":                        0x10,
            "EFI_SECTION_PIC":                         0x11,
            "EFI_SECTION_TE":                          0x12,
            "EFI_SECTION_DXE_DEPEX":                  0x13,
            "EFI_SECTION_VERSION":                    0x14,
            "EFI_SECTION_USER_INTERFACE":            0x15,
            "EFI_SECTION_COMPATIBILITY16":           0x16,
            "EFI_SECTION_FIRMWARE_VOLUME_IMAGE":    0x17,
            "EFI_SECTION_FREEFORM_SUBTYPE_GUID":    0x18,
            "EFI_SECTION_RAW":                         0x19,
            "EFI_SECTION_PEI_DEPE":                   0x1B,
            "EFI_SECTION_LAST_LEAF_SECTION_TYPE":   0x1B,
            "EFI_SECTION_LAST_SECTION_TYPE":         0x1B,
        }
        for item,value in SECTION_TYPE.items():
            if self.type == value:
                return item
        return "unkonuw"

    def showinfo(self):
        print "    section:{", self.getSectionType(), hex(self.size), "}"






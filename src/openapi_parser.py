import jsonpath_ng.ext as jp
import json
import re
from enum import Enum
from array import *

class DTOInOutEnum(Enum):
    DTOIn = 1
    DTOOut = 2
    DTOInOut = 3

class OpenApiParser:
    """Provides methods to generate delphi code from openapi"""  
    def __init__(self):
        self.DtoInOutInfosMap = {}
        print("OpenApiParser init")

    def __del__(self):
    # body of destructor
        print("OpenApiParser finalize")

    def ParseDTONameFromRef(self, openapi_dto_ref):
        ref_type = re.findall('.*/([^/]*$)', openapi_dto_ref)
        return ref_type[0]

    def SetInOutValue(self, json_ref_value, inout_enum_value):
        dto_name = self.ParseDTONameFromRef(json_ref_value)
        print('dto name is ' + dto_name)
        if dto_name in self.DtoInOutInfosMap:
            if self.DtoInOutInfosMap[dto_name] != inout_enum_value:
                self.DtoInOutInfosMap[dto_name] = DTOInOutEnum.DTOInOut
        else:
            self.DtoInOutInfosMap[dto_name] = inout_enum_value

    def ParsePaths(self, json_data):
        query = jp.parse("$.paths")
        for match in query.find(json_data):
            paths = match.value
            for path, methoddict in paths.items():
                for methodname, methodprop in methoddict.items():
                # print(methodprop)
                    query = jp.parse("$.requestBody.content.*.schema")
                    for match in query.find(methodprop):
                        ref = match.value
                        if '$ref' in ref:
                            self.SetInOutValue(ref['$ref'], DTOInOutEnum.DTOIn)
   
                    query = jp.parse("$.responses.default.content.*.schema")
                    for match in query.find(methodprop):
                        ref = match.value
                        if '$ref' in ref:
                            self.SetInOutValue(ref['$ref'], DTOInOutEnum.DTOOut)

    def DTOUsedInPaths(self, dto_name):
        return dto_name in self.DtoInOutInfosMap
    
    def GetDTOInOutStatus(self, dto_name):
        return self.DtoInOutInfosMap[dto_name]



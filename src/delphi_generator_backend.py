import os
from enum import Enum
from array import *
from openapi_parser import DTOInOutEnum
from openapi_parser import OpenApiParser


class PropertyArity(Enum):
    Single = 1
    Array = 2

class DelphiGenerator:
    """Provides methods to generate delphi code from openapi"""  
    def __init__(self, open_api_parser, prefix, output_gen_dir):
        self.DTOPrefix = prefix
        self._outfolder = output_gen_dir
        self._outfile = None
        self._parser = open_api_parser
        self._typeMapper =  {'array': 'TArray', 'integer': 'integer', 'string': 'string', 'boolean': 'boolean', 'object': 'object'}
        self._jsonTypeMapper =  {'TArray': 'TJSONArray', 'integer': 'integer', 'string': 'string', 'boolean': 'boolean', 'object': 'object'}
        self._defaultMapper =  {'TArray' : 'nil', 'integer': '0', 'string': '\'\'', 'boolean': '0', 'object': 'nil'}
        self._indent = ''
        self._dtoMap = {}
        print("DelphiGenerator init")

    def __del__(self):
    # body of destructor
        print("DelphiGenerator finalize")

    def EnterBlock(self):
        self._indent = self._indent + '  '

    def WCL(self, code_line):
        if self._outfile:
            self._outfile.write(self._indent + code_line + '\n')
        else:
            print(self._indent + code_line)
    
    def EnterSection(self, section_name):
        self.WCL(section_name)
        self.EnterBlock()

    def LeaveSection(self):
        self.LeaveBlock()
        self.WCL('end;')

    def LeaveBlock(self):
        indent_len = len(self._indent)
        if (indent_len >= 2):
            indent_len = indent_len - 2
        if (indent_len == 0):
            self._indent = ''
        else :
            self._indent = self._indent[0 : indent_len]

    def MapType(self, openapi_type):
        return self._typeMapper[openapi_type]

    def OpenUnitFile(self, unit_name):
        if self._outfolder:
            self._outfile = open(os.path.join(self._outfolder, unit_name + '.pas'), "w")
        self.WCL('unit ' + unit_name + ';')
        self.WCL('')
        self.WCL('interface')
        self.WCL('')

    def CloseUnitFile(self):
        if self._outfolder:
            self._outfile.close()
    
    def BuildDelphiDTOName(self, json_dto_name):
        return self.DTOPrefix + json_dto_name

    def DelphiRecordHelperDeclarationBlock(self, dto_name, in_out_enum):
        if in_out_enum == DTOInOutEnum.DTOIn or in_out_enum == DTOInOutEnum.DTOInOut:
            serializer_name = dto_name + 'Serializer = record helper for ' + dto_name
            self.EnterSection(serializer_name)
            self.WCL('function SerializeObject: TJSONObject;')
            self.WCL('function Serialize: string;')
            self.LeaveSection()
            self.WCL('')

        if in_out_enum == DTOInOutEnum.DTOOut or in_out_enum == DTOInOutEnum.DTOInOut:
            deserializer_name = dto_name + 'Deserializer = record helper for ' + dto_name
            self.EnterSection(deserializer_name)
            self.WCL('  class function Deserialize(jsonObject: TJSONObject): ' + dto_name + '; overload; static;')
            self.WCL('  class function Deserialize(jSonValue: string): ' + dto_name + '; overload; static;')
            self.LeaveSection()
            self.WCL('')

    def DelphiRecordHelperImplementationBlock(self, dto_name, in_out_enum, record_properties):
        if in_out_enum == DTOInOutEnum.DTOIn or in_out_enum == DTOInOutEnum.DTOInOut:
            serializer_name = dto_name + 'Serializer'
            self.WCL('function ' + serializer_name + '.SerializeObject: TJSONObject;')
            self.EnterSection('begin')
            self.WCL('Result := TJSONObject.Create();')
            self.EnterSection('try')
            for arity in record_properties.keys():
                for name,proptype in record_properties[arity].items():
                    if proptype in self._typeMapper:
                        self.WCL('Result.AddPair(\'' + name + '\', ' + name + ');')
                    else:
                        self.WCL('Result.AddPair(\'' + name + '\', ' + name + '.SerializeObject);')
            self.LeaveBlock()
            self.EnterSection('except')
            self.WCL('Result.Free;')
            self.WCL('Raise;')
            self.LeaveSection()
            self.LeaveSection()
            self.WCL('')
            self.WCL('function ' + serializer_name + '.Serialize: string;')
            self.EnterSection('var')
            self.WCL('LJsonDto: TJSONObject;')
            self.LeaveBlock()
            self.EnterSection('begin')
            self.WCL('LJsonDto := SerializeObject;')
            self.EnterSection('try')
            self.WCL('Result := LJsonDto.ToJSON;')
            self.LeaveBlock()
            self.EnterSection('finally')
            self.WCL('LJsonDto.Free;')
            self.LeaveSection()
            self.LeaveSection()
            self.WCL('')

        if in_out_enum == DTOInOutEnum.DTOOut or in_out_enum == DTOInOutEnum.DTOInOut:
            deserializer_name = dto_name + 'Deserializer'
            self.WCL('class function ' + deserializer_name + 'Deserialize(jsonObject: TJSONObject): ' + dto_name)
            if PropertyArity.Array in record_properties:
                self.EnterSection('var')
                self.WCL('items: TJSONArray;')
                self.WCL('index: integer;')
                self.LeaveBlock()
            self.EnterSection('begin')
            self.WCL('Result := Default(' + dto_name + ');')
            for name, proptype in record_properties[PropertyArity.Single].items():
                default_value = 'nil'
                if proptype in self._defaultMapper:
                    default_value = self._defaultMapper[proptype]    
                self.WCL('Result.' + name + ' := jsonObject.GetValue<' + proptype + '>(\'' + name + ' \', ' + default_value + ');')
            for name, proptype in record_properties[PropertyArity.Array].items():  
                self.WCL('items := jsonObject.GetValue<TJSONArray>(\'' + name + '\', nil);')
                self.WCL('SetLength(Result.' + name + ', items.Count);')
                self.WCL('for index := 0 to items.Count - 1 do')
                self.EnterBlock()
                self.WCL('Result.' + name + '[index] := ' + proptype + '.Deserialize(items.Items[index] as TJSONobject);')
                self.LeaveBlock()
            self.LeaveSection()
            self.WCL('')
            
            self.WCL('class function ' + deserializer_name + 'Deserialize(jsonValue: string): ' + dto_name)
            self.EnterSection('var')
            self.WCL('LJsonDto: TJSONObject;')
            self.LeaveBlock()
            self.EnterSection('begin')
            self.WCL('Result := Default(' + dto_name + ');')
            self.WCL('LJsonDto := TJSONObject.ParseJSONValue(jsonValue, True) as TJSONObject;')
            self.WCL('if LJsonDto = nil then')
            self.EnterSection('begin')
            self.WCL('// Raise exception or simply log error and return default?')
            self.WCL('// WriteLn(\'' + deserializer_name + '.Deserialize LJsonObj from jsonValue is nil\');')
            self.WCL('exit;')
            self.LeaveSection()
            self.EnterSection('try')
            self.WCL('Result := Deserialize(LJsonDto);')
            self.LeaveBlock()
            self.EnterSection('finally')
            self.WCL('LJsonDto.Free;')
            self.LeaveSection()
            self.LeaveSection()
            self.WCL('')

    def DelphiRecordDeclarationBlock(self, record_name, record_properties):
        self.EnterSection(record_name + ' = record')
        for arity in record_properties.keys():
            isArray = (arity == PropertyArity.Array)
            for name, value in record_properties[arity].items():
                if isArray:
                    value = 'TArray<' + value + '>'
                self.WCL(name + ': ' + value + ';')
        self.LeaveSection()
        self.WCL('')

    def GenerateDTO(self, json_dto_name, json_dto_properties):
        dto_name = self.BuildDelphiDTOName(json_dto_name)
        #print(dto_name)
        properties = {}
        properties[PropertyArity.Single] = {}
        properties[PropertyArity.Array] = {}
        for k,v in json_dto_properties.items():
            property_type = ''
            arity = PropertyArity.Single
            #print(v)
            if 'type' in v:
                #print(k +': '+ self.MapType(v['type']))
                property_type = self.MapType(v['type'])
                if v['type'] == 'array':
                    arity = PropertyArity.Array
                    if '$ref' in v['items']: # parsing $ref p
                        ref_type = self._parser.ParseDTONameFromRef(v['items']['$ref'])
         #               print(ref_type)
                        property_type = self.BuildDelphiDTOName(ref_type)
                    else:
                        if 'type' in v['items']:
                            property_type = self.MapType(v['items']['type'])
                
            else :
                if '$ref' in v: # parsing $ref p
                    ref_type = self._parser.ParseDTONameFromRef(v['$ref'])
                    property_type = self.BuildDelphiDTOName(ref_type)

            if property_type:
                properties[arity][k] = property_type
            else:
                print('ERROR parsing file property type not resolevd')
        #generate language DTo
        self._dtoMap[json_dto_name] = properties
        #self.DelphiRecordDeclarationBlock(dto_name, properties)
        return properties

    def GenerateDTOs(self):
        unit_name = self.DTOPrefix + '.DTOs' 
        self.OpenUnitFile(unit_name)
        self.EnterSection('type')
        for k,v in self._dtoMap.items():
            dto_name = self.BuildDelphiDTOName(k)
            self.DelphiRecordDeclarationBlock(dto_name,v)
        self.LeaveBlock()            
        self.WCL('implementation')
        self.WCL('')
        self.WCL('end.')
        self.CloseUnitFile()

    def GenerateSerializer(self, json_dto_name, dto_properties):
        dto_name = self.BuildDelphiDTOName(json_dto_name)
        self.DelphiRecordHelperDeclarationBlock(dto_name, self._parser.GetDTOInOutStatus(json_dto_name))
        self.DelphiRecordHelperImplementationBlock(dto_name, self._parser.GetDTOInOutStatus(json_dto_name), dto_properties)

    def GenerateSerializers(self):
        unit_name = self.DTOPrefix + '.Serializers' 
        self.OpenUnitFile(unit_name)
        self.EnterSection('uses')
        self.WCL('System.JSON;')
        self.LeaveBlock()
        self.WCL('')
        self.EnterSection('type')
        for k,v in self._dtoMap.items():
            dto_name = self.BuildDelphiDTOName(k)
            self.DelphiRecordHelperDeclarationBlock(dto_name, self._parser.GetDTOInOutStatus(k))
        self.LeaveBlock()
        self.WCL('implementation')
        self.WCL('')
        self.EnterSection('uses')
        self.WCL('System.StrUtils,')
        self.WCL('System.SysUtils,')
        self.WCL('System.Types;')
        self.LeaveBlock()
        self.WCL('')
        for k,v in self._dtoMap.items():
            dto_name = self.BuildDelphiDTOName(k)
            self.DelphiRecordHelperImplementationBlock(dto_name, self._parser.GetDTOInOutStatus(k), self._dtoMap[k])
        self.WCL('end.')
        self.CloseUnitFile()
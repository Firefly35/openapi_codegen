#!/usr/bin/python
import argparse
import logging
import sys
import os
import jsonpath_ng.ext as jp
import json
from array import *
from openapi_parser import OpenApiParser
from delphi_generator_backend import DelphiGenerator

parser = argparse.ArgumentParser(description='Tixeo rest api generator tool')
parser.add_argument('-f', '--file',
                    required=True,
                    type=str,
                    help="api file")
parser.add_argument('-p', '--prefix',
                    default='PFX',
                    type=str,
                    help="class prefix")
parser.add_argument('-o', '--outputdir',
                    default='',
                    type=str,
                    help="generation file output dir")      

args = parser.parse_args()


#def parse_path():

#def parse_dto():

def parse(json_data):
    openApiParser = OpenApiParser()
    codegen = DelphiGenerator(openApiParser, args.prefix, args.outputdir)
    openApiParser.ParsePaths(json_data)

    query = jp.parse("$.components.schemas")
    for match in query.find(json_data):
        schemas = match.value
        for dtoname, properties in schemas.items():
            #print(dtoname)
            query = jp.parse("$.properties")
            for match in query.find(properties):
                if openApiParser.DTOUsedInPaths(dtoname):
                    dto_properties = codegen.GenerateDTO(dtoname, match.value)
                    #codegen.GenerateSerializer(dtoname, dto_properties)
                #print(match.value)
    codegen.GenerateDTOs()
    codegen.GenerateSerializers()
            

def main():
    try:
        folder_path = args.outputdir
        os.makedirs(folder_path)
        print(f"Nested directories '{folder_path}' created successfully.")
    except FileExistsError:
        print(f"One or more directories in '{folder_path}' already exist.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{folder_path}'.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    parse(json.load(open(args.file)))

if __name__ == '__main__':
    try:
        #ciphered_pwd = cipher_pwd(args.password, args.login)
        #print("Ciphered password =" + ciphered_pwd)
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

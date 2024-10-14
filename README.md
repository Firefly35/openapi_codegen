# openapi_codegen
Open api code generator written in python

First version generates Delphi System.JSON files from a json openapi specification.

To use it, from the command line use
```
python restapi_gen.py -f [path_to_folder]/openapi-file.json -o {generation_output_folder}
```
The output folder will be created if needed.
Using the tool without the -o option will print the generation on the command line.
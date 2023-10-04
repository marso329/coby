import re
from enum import Enum
import logging
import sys
import pathlib

class FileType(Enum):
    Undecided = 0
    PrimaryModuleInterface = 1
    Moduleimplementation = 2
    ModuleInterfacePartition = 3
    InternalModulePartition = 4

ImportableModuleFileExtensions=[".cppm",".ccm",".cxxm",".c++m"]
ModuleImplementationFileExtensions=[".cpp",".cc",".cxx",".c++"] 

exportRegex = re.compile("^export\s*module\s*(.*)\s*;")
implementRegex = re.compile("^module\s*(.*)\s*;")
importRegex = re.compile("^import\s*(.*)\s*;")
exportImportRegex = re.compile("^export import\s*(.*)\s*;")

name =re.compile("([a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)*)")
importName =re.compile("([a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)*)|(<[a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)*>)")
def getName(result,file):
    modules=result.split(":")
    modulePartitions=[]
    for module in modules:
        module=module.strip()
        nameResult = name.fullmatch(module)
        if not nameResult:
            logging.error("{} is not a valid module name in {} in file {}".format(module,result,file))
            sys.exit(1)
        modulePartitions.append(nameResult.string)
    return modulePartitions

def getNameImport(result,file):
    modules=result.split(":")
    modulePartitions=[]
    for module in modules:
        module=module.strip()
        #for example import :A means that first string is empty
        if not module:
            modulePartitions.append("")
        else:
            nameResult = importName.fullmatch(module)
            if not nameResult:
                logging.error("{} is not a valid module name in {} in file {}".format(module,result,file))
                sys.exit(1)
            modulePartitions.append(nameResult.string)
    return modulePartitions

def scan(file):
    exports=[]
    imports=[]
    implements=[]
    with open(file) as f:
        for line in f:
            #find exports
            result = exportRegex.search(line)
            if result:
                modules=result.group(1)
                modules=getName(modules,file)
                exports.append(modules)
            result = importRegex.search(line)
            if result:
                modules=result.group(1)
                modules=getNameImport(modules,file)
                imports.append(modules)
            result = exportImportRegex.search(line)
            if result:
                modules=result.group(1)
                modules=getNameImport(modules,file)
                imports.append(modules)
            result = implementRegex.search(line)
            if result:
                modules=result.group(1)
                modules=getNameImport(modules,file)
                implements.append(modules)
    #remove global module fragment declaration
    if len(implements)>1 and implements[0]==[""]:
        implements.pop(0)
    
    if len(exports)>1:
        logging.error("file {} contains more than one module exports, this is currently not supported".format(file))
        sys.exit(1)
    if len(implements)>1:
        logging.error("file {} contains more than one module implementation, this is currently not supported".format(file))
        sys.exit(1)
    #decide file type
    fileType=FileType.Undecided
    if len(exports)>0 and len(implements)>0:
        logging.error("file {} both exports {} and implements {}".format(file,exports[0],implements[0]))
        sys.exit(1)
    if len(exports)==1:
        if len(exports[0])==2:
            fileType=FileType.ModuleInterfacePartition
        elif len(exports[0])==1:
            fileType=FileType.PrimaryModuleInterface
        else:
            logging.error("file {} contains an export of partitions with an hierarchy with size greater than 2: {}".format(file,exports[0]))
            sys.exit(1)
    if len(implements)==1:
        if len(implements[0])==2:
            fileType=FileType.InternalModulePartition
        elif len(implements[0])==1:
            fileType=FileType.Moduleimplementation
        else:
            logging.error("file {} contains an implementation of partitions with an hierarchy with size greater than 2: {}".format(file,implements[0]))
            sys.exit(1)
    fileExtension=pathlib.Path(file).suffix
    if fileType==FileType.ModuleInterfacePartition or fileType==FileType.PrimaryModuleInterface:
        if fileExtension not in ImportableModuleFileExtensions:
            logging.warning("file {} is an importable file but the file extension {} does not match for this kind of file. Should be: {}".format(file,fileExtension,ImportableModuleFileExtensions))
    if fileType==FileType.Moduleimplementation or fileType==FileType.InternalModulePartition:
        if fileExtension not in ModuleImplementationFileExtensions:
            logging.warning("file {} is an implementation file but the file extension {} does not match for this kind of file. Should be: {}".format(file,fileExtension,ModuleImplementationFileExtensions))

    #decide module name
    moduleName=""
    if len(exports)>0:
        moduleName=exports[0][0]
    if len(implements)>0:
        moduleName=implements[0][0]
    for element in imports:
        if element[0]=="":
            if moduleName=="":
                logging.error("importing {} in file {} using :partition but the moduleName could not be decided".format(element,file))
                sys.exit(1)
            element[0]=moduleName
    return {"imports":imports,"exports":exports,"fileType":fileType,"implements":implements}
    
            
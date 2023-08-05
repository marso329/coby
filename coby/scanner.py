import re

exportRegex = re.compile("^\s*export\s*module\s*(.*)\s*;")
importRegex = re.compile("\s*import\s*(.*)\s*;")
name =re.compile("([a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)*)")
importName =re.compile("([a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)*)|(<[a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)*>)")
def getName(result):
    modules=result.split(":")
    modulePartitions=[]
    for module in modules:
        module=module.strip()
        nameResult = name.fullmatch(module)
        if not nameResult:
            raise RuntimeError("{} is not a valid module name in {}".format(module,result))
        modulePartitions.append(nameResult.string)
    return modulePartitions

def getNameImport(result):
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
                raise RuntimeError("{} is not a valid module name in {}".format(module,result))
            modulePartitions.append(nameResult.string)
    return modulePartitions

def scan(file):
    exports=[]
    imports=[]
    with open(file) as f:
        for line in f:
            #find exports
            result = exportRegex.search(line)
            if result:
                #print(result.group(1))
                modules=result.group(1)
                modules=getName(modules)
                exports.append(modules)
            result = importRegex.search(line)
            if result:
                #print(result.group(1))
                modules=result.group(1)
                modules=getNameImport(modules)
                imports.append(modules)
    print("imports:")
    print(imports)
    print("exports:")
    print(exports)
    
            
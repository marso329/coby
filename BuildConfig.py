
#target= builddir/target_name
#input= src folder/file
#output= set by the rule, one or more files that are created
#explicit_dependencies= list of all dependecies that were explicit written for that rule
def init(vars):
    vars["CXX"]=["/tools/llvm/bin/clang++"]
    vars["CXXSTDLOCATION"]=["/usr/include/c++/11"]
    vars["CXXFLAGS"]=["-std=c++20","-g","-w"]
    vars["LDFLAGS"]=["-std=c++20","-g"]

def stdlib(vars):
    command=vars["CXX"]+vars["CXXFLAGS"]+["-xc++-system-header","--precompile"]+[vars["target"]]+["-o","{}/{}.pcm".format(vars["output_dir"],vars["target"])]
    vars["output"]="{}/{}.pcm".format(vars["output_dir"],vars["target"])
    command2=vars["CXX"]+vars["CXXFLAGS"]+["{}/{}.pcm".format(vars["output_dir"],vars["target"])]+["-c","-o","{}/{}.o".format(vars["output_dir"],vars["target"])]
    vars["output"]="{}/{}.o".format(vars["output_dir"],vars["target"])
    return [command,command2]

def user_module(vars):
    command1=vars["CXX"]+vars["CXXFLAGS"]
    for element in vars["deps"]:
        command1.append("-fmodule-file={}/{}.pcm".format(element["output_dir"],element["target"]))
    command1+=["--precompile","-xc++-module","-c",vars["input"]]
    command1+=["-o","{}/{}.pcm".format(vars["output_dir"],vars["target"])]
    vars["output"]="{}/{}.pcm".format(vars["output_dir"],vars["target"])
    command2=vars["CXX"]+vars["CXXFLAGS"]+["{}/{}.pcm".format(vars["output_dir"],vars["target"])]+["-c","-o","{}/{}.o".format(vars["output_dir"],vars["target"])]
    vars["output"]="{}/{}.o".format(vars["output_dir"],vars["target"])
    return [command1,command2]


def binary(vars):
    command1=vars["CXX"]+vars["CXXFLAGS"]
    command1.append(vars["input"])
    for element in vars["deps"]:
        if element["rule"]=="stdlib":
            command1.append("-fmodule-file={}/{}.pcm".format(element["output_dir"],element["target"]))
        elif element["rule"]=="user_module":
            command1.append("-fmodule-file={}={}/{}.pcm".format(element["target"],element["output_dir"],element["target"]))
        else:
            raise RuntimeError("rule not found")
    command1+=["-c","-o","{}/{}.o".format(vars["output_dir"],vars["target"])]
    vars["output"]="{}/{}.o".format(vars["output_dir"],vars["target"])

    command2=vars["CXX"]+vars["LDFLAGS"]
    for element in vars["all_dependencies"]:
        command2.append("{}/{}.o".format(element["output_dir"],element["target"]))
    command2+=["-o","{}/{}".format(vars["output_dir"],vars["target"])]
    vars["output"]="{}/{}".format(vars["output_dir"],vars["target"])

    return [command1,command2]
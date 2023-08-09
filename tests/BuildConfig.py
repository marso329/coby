
def user_module(vars):
    command1=vars["CXX"]+vars["CXXFLAGS"]
    for element in vars["deps"]:
        command1.append("-fmodule-file={}/{}.pcm".format(element["output_dir"],element["target"]))
    command1+=["--precompile","-xc++-module","-c",vars["input"]]
    command1+=["-o","{}/{}.pcm".format(vars["output_dir"],vars["target"])]
    vars["output"]="{}/{}.pcm".format(vars["output_dir"],vars["target"])
    vars["BMI"]="{}={}/{}.pcm".format(vars["target"],vars["output_dir"],vars["target"])
    
    command2=vars["CXX"]+vars["CXXFLAGS"]+["{}/{}.pcm".format(vars["output_dir"],vars["target"])]+["-c","-o","{}/{}.o".format(vars["output_dir"],vars["target"])]
    objectFile="{}/{}.o".format(vars["output_dir"],vars["target"])
    vars["output"]=objectFile
    vars["objectFile"]=objectFile
    return [command1,command2]
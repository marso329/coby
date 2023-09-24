import os

#target= builddir/target_name
#input= src folder/file
#output= set by the rule, one or more files that are created
#explicit_dependencies= list of all dependecies that were explicit written for that rule
def init(vars):
    vars["CXX"]=["/tools/llvm/bin/clang++"]
    vars["CXXSTDLOCATION"]=["/usr/include/c++/11"]
    vars["CXXFLAGS"]=["-std=c++20","-g","-w","-pipe","-fPIC"]
    vars["LDFLAGS"]=["-std=c++20","-g"]
    vars["UIC"]=["/usr/lib/qt6/libexec/uic"]
    vars["MOC"]=["/usr/lib/qt6/libexec/moc"]
    vars["QT6_INCLUDES"]=["/usr/include/x86_64-linux-gnu/qt6"]
    vars["QT6_MODULES"]=["QtCore", "QtGui", "QtWidgets", "QtSql"]
    vars["QT6_LIBS"]=["Qt6Widgets", "Qt6Gui", "GLX", "OpenGL","Qt6Sql","Qt6Core"]
    vars["LIB_PATH"]=["/usr/lib/x86_64-linux-gnu"]
    vars["QT6_DEFINES"]=["-DQT_NO_DEBUG","-DQT_WIDGETS_LIB","-DQT_GUI_LIB","-DQT_SQL_LIB","-DQT_CORE_LIB"]

def uic(vars):
    command1=vars["UIC"]+[vars["input"]]+["-o","{}/{}.cxx".format(vars["output_dir"],vars["target"])]
    outputFile="{}/{}.cxx".format(vars["output_dir"],vars["target"])
    vars["output"]=outputFile
    command2=["sed","-i",'1 i\\module;',outputFile]
    command3=["sed", "-i", '/^class.*/i export module {};'.format(vars["target"]),outputFile ]
    command4=["sed", "-i", '/^class.*/i export',outputFile ]
    command5=["sed", "-i", '/^namespace.*/i export',outputFile ]

    oldInput=vars["inputFile"]
    #this is ugly as fuck but it is not meant to use files in the output directory as inputs, should be fixed in the future
    relativePath=os.path.relpath( vars["output_dir"],vars["path"])
    vars["input"]="{}/{}.cxx".format(relativePath,vars["target"])
    qtModuleCommands=qt_module(vars)
    vars["input"]=oldInput
    return [command1,command2,command3,command4,command5]+qtModuleCommands

def getQTIncludes(vars):
    return ["-I"+x for x in vars["QT6_INCLUDES"]]+["-I"+vars["QT6_INCLUDES"][0]+os.sep+x for x in vars["QT6_MODULES"]]


def stdlib(vars):
    command=vars["CXX"]+vars["CXXFLAGS"]+["-xc++-system-header","--precompile"]+[vars["target"]]+["-o","{}/{}.pcm".format(vars["cache_dir"],vars["target"])]
    vars["output"]="{}/{}.pcm".format(vars["cache_dir"],vars["target"])
    vars["BMI"]="{}/{}.pcm".format(vars["cache_dir"],vars["target"])

    command2=vars["CXX"]+vars["CXXFLAGS"]+["{}/{}.pcm".format(vars["cache_dir"],vars["target"])]+["-c","-o","{}/{}.o".format(vars["cache_dir"],vars["target"])]
    objectFile="{}/{}.o".format(vars["cache_dir"],vars["target"])
    vars["output"]=objectFile
    vars["objectFile"]=objectFile
    vars["output_dir"]=vars["cache_dir"]
    return [command,command2]

def qt_object(vars):
    command1=vars["CXX"]+vars["CXXFLAGS"]
    command1+=["-dM","-E","-o","{}/moc_predefs.h".format(vars["output_dir"]),"{}/qt6/mkspecs/features/data/dummy.cpp".format(vars["LIB_PATH"][0])]
    vars["output"]="{}/{}.pcm".format(vars["output_dir"],vars["target"])
    command2=vars["MOC"]
    command2+=vars["QT6_DEFINES"]
    command2+=["-I{}/moc_predefs.h".format(vars["output_dir"])]
    command2+=getQTIncludes(vars)
    command2+=[vars["input"]]
    outputFile="{}/moc_{}.cxx".format(vars["output_dir"],vars["target"])
    vars["output"]=outputFile
    command2+=["-o",outputFile]
    newTempFile="{}/temp_{}.cxx".format(vars["output_dir"],vars["target"])
    command3=["cp",vars["input"],newTempFile]
    #command4=["sed", "-n", '/QT_BEGIN_MOC_NAMESPACE/,/QT_END_MOC_NAMESPACE/p',outputFile, "|","cat","{}".format(newTempFile), ]
    #piping data
    command4=[("command",["sed", "-n", '/QT_BEGIN_MOC_NAMESPACE/,/QT_END_MOC_NAMESPACE/p',outputFile]),("file",newTempFile)]

    oldInput=vars["inputFile"]
    relativePath=os.path.relpath( vars["output_dir"],vars["path"])
    vars["input"]="{}/temp_{}.cxx".format(relativePath,vars["target"])
    qtModuleCommands=qt_module(vars)
    vars["input"]=oldInput

    return [command1,command2,command3,command4]+qtModuleCommands


def qt_module(vars):
    command1=vars["CXX"]+vars["CXXFLAGS"]
    command1+=vars["QT6_DEFINES"]

    for element in vars["deps"]:
        command1.append("-fmodule-file={}/{}.pcm".format(element["output_dir"],element["target"]))
    command1+=["--precompile","-xc++-module","-c",vars["input"]]
    command1+=getQTIncludes(vars)
    command1+=["-o","{}/{}.pcm".format(vars["output_dir"],vars["target"])]
    vars["output"]="{}/{}.pcm".format(vars["output_dir"],vars["target"])
    vars["BMI"]="{}={}/{}.pcm".format(vars["target"],vars["output_dir"],vars["target"])
    
    command2=vars["CXX"]+vars["CXXFLAGS"]+["{}/{}.pcm".format(vars["output_dir"],vars["target"])]+["-c","-o","{}/{}.o".format(vars["output_dir"],vars["target"])]
    objectFile="{}/{}.o".format(vars["output_dir"],vars["target"])
    vars["output"]=objectFile
    vars["objectFile"]=objectFile
    return [command1,command2]

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



def binary(vars):
    command1=vars["CXX"]+vars["CXXFLAGS"]
    command1+=vars["QT6_DEFINES"]
    command1.append(vars["input"])
    for element in vars["deps"]:
        if element["BMI"]:
            command1.append("-fmodule-file={}".format(element["BMI"]))
    command1+=getQTIncludes(vars)
    command1+=["-c","-o","{}/{}.o".format(vars["output_dir"],vars["target"])]
    objectFile="{}/{}.o".format(vars["output_dir"],vars["target"])
    vars["output"]=objectFile
    vars["objectFile"]=objectFile

    command2=vars["CXX"]+vars["LDFLAGS"]
    for element in vars["all_dependencies"]:
        if element["objectFile"]:
            command2.append(element["objectFile"])
    command2+=["-o","{}/{}".format(vars["output_dir"],vars["target"])]
    for element in vars["QT6_LIBS"]:
        command2+=["{}{}lib{}.so".format(vars["LIB_PATH"][0],os.sep,element)]
    vars["output"]="{}/{}".format(vars["output_dir"],vars["target"])

    return [command1,command2]
#!/bin/python3
#start = := creation | assignment

#creation := creates "=" rule(args)

#creates := items

#items := name | enumerated

#rule := name

#name := string

#args is optional
#args :=   name=items{","name=items} 

#enumerated := [name {, name}]

#terminals= "=","(",")",string,"[","]"

import re
import argparse
import os
import importlib.util
import sys
import subprocess
from pathlib import Path


class FileCompilationTimesCache:
    def __init__(self):
        self.times={}
        if os.path.isfile("./compilationCache"):
            with open("./compilationCache") as fobj:
                for line in fobj:
                    row = line.split()
                    self.times[row[0]]=float(row[1])
    
    
    def write(self):
        with open("./compilationCache", 'w+') as fobj:
            for fileName in self.times:
                fobj.write('{} {}\n'.format(fileName,self.times[fileName]))
    
    def getCompilationTime(self,fileName):
        if fileName in self.times:
            return self.times[fileName]
        return 0.0
    def setCompilationTime(self,fileName,time):
        self.times[fileName]=time
class Target:
    def __init__(self,buildDir):
        self.rule=""
        self.target=""
        self.deps=[]
        self.input=""
        self.buildDir=buildDir
        self.output=[]
        self.commands=[]
        self.lastChangeTime=0
        self.dirty=False
    def __str__(self):
        returnString="("
        returnString+="rule: "+self.rule+", target: "+self.target+", deps: "+str(self.deps) +", input: "+self.input+", output: "+self.output
        returnString+=")"
        return returnString
    def __getitem__(self, key):
        if key=="deps":
            realTarget=[]
            for element in self.deps:
                realTarget.append(self.buildDir.findTarget(element))
            return realTarget
        if key=="input":
            return self.input
        if key=="rule":
            return self.rule
        if key=="target":
            return self.target
        if key=="all_dependencies":
            return self.buildDir.allDependencies(self.target)
        if key=="output_dir":
            return self.buildDir.getOutputDir()
        if key=="output":
            return self.output
        if key=="path":
            return self.buildDir.path
        
        return self.buildDir.searchFromTarget(key)
    def __setitem__(self, key, value):
        if key=="output":
            self.output.append(value)
        else:
            raise RuntimeError("key {} undefined".format(key))



    def checkSpecialVariables(self,variable:str,val):
        if variable.lower()=="input":
            self.input=val
            return True
        if variable.lower()=="deps":
            self.deps=val
            return True
        return False

class BuildDirectory:
    def __init__(self):
        self.targets={}
        self.rules={}
        self.subdirs=[]
        self.variables={}
        self.default_target=""
        self.path=""
        self.in_source_build=False
        self.build_directory=""
        self.compilationCache=FileCompilationTimesCache()
    def __str__(self):

        returnString=""
        returnString+="targets:\n"
        for element in self.targets:
            returnString+="\t"+element+" : "+str(self.targets[element])+"\n"
        returnString+="rules:\n"
        for element in self.rules:
            returnString+="\t"+element+" : "+str(self.rules[element])+"\n"
        returnString+="subdirs:\n"
        for element in self.subdirs:
            returnString+="\t"+element+"\n"
        returnString+="variables:\n"
        for element in self.variables:
            returnString+="\t"+element+" : "+str(self.variables[element])+"\n"
        returnString+="default_target :"+self.default_target +"\n"
        returnString+="in_source_build :"+str(self.in_source_build)+"\n" 
        returnString+="path :"+self.path
        return returnString

    def saveCache(self):
        self.compilationCache.write()

    def getOutputDir(self):
        if self.in_source_build:
            return self.path
        else:
            return self.build_directory

    def allDependencies(self,targetName):
        targetsDeps=list(self.getRequiredTargets(targetName).values())
        targetsDepsInstances=[self.targets[x] for x in self.targets]
        return targetsDepsInstances

    def findTarget(self,targetName):
        if targetName in self.targets:
            return self.targets[targetName]
        raise KeyError("target {} not found in directory {}",targetName,self.path)


    def searchFromTarget(self,key):
        if key in self.variables:
            return self.variables[key]
        raise KeyError("key {} not found in directory {}".format(key,self.path))

    def checkSpecialVariables(self,variable:str,val):
        if variable.lower()=="default_target":
            self.default_target=val
            return True
        if variable.lower()=="subdirs":
            self.subdirs=val
            return True
        if variable.lower()=="in_source_build":
            self.in_source_build=val.lower()=="true"
            return True
        if variable.lower()=="build_directory":
            self.build_directory=os.path.abspath(val)
            return True        
        return False

    def build(self):
        
        #step one, decide the main target
        decidedTarget=""
        if not self.default_target:
            #all targets
            requiredTargets=self.getRequiredTargets()
            buildOrder=self.decideBuildOrder(requiredTargets)
            if len(buildOrder)==0:
                raise RuntimeError("no build order could be decided")
            if len(buildOrder[0])>1:
                raise RuntimeError("no default target set and multiple options found  "+str(buildOrder[0]))
            decidedTarget=buildOrder[0][0]
        else:
            if self.default_target not in self.targets:
                raise RuntimeError("default target {} not found".format(self.default_target))
            decidedTarget=self.default_target
        
        #step two, find all the targets required to build the main target
        requiredTargets=self.getRequiredTargets(decidedTarget)

        #step three, find the order in which to build it
        buildOrder=self.decideBuildOrder(requiredTargets)

        #step four, build the commands for the targets
        self.buildCommands(buildOrder)

        #step five, check for dirty targets
        self.checkForDirtyFiles(requiredTargets)

        #step six remove clean targets
        buildOrder=self.removeCleanTargets(buildOrder)

        if not buildOrder:
            print("nothing to do")

        #step seven, run the commands
        self.runCommands(buildOrder)
        self.saveCache()

    def removeCleanTargets(self,buildOrder):
        newOrder=[]
        for batch in buildOrder:
            newBatch=[]
            for target in batch:
                if self.targets[target].dirty:
                    newBatch.append(target)
            if newBatch:
                newOrder.append(newBatch)
        return newOrder
    def checkForDirtyFiles(self,requiredTargets):
        buildTargets=list(requiredTargets.keys())
        dirtyTargets=[]
        #if they define an input file then we check if it has changed
        for element in buildTargets:
            if self.targets[element]["input"]:
                fileName="{}/{}".format(self.targets[element]["path"],self.targets[element]["input"])
                if self.compilationCache.getCompilationTime(fileName)!=os.path.getmtime(fileName):
                    dirtyTargets.append(element)
        #the we check if the output file(s) exists
        for element in buildTargets:
            if self.targets[element]["output"]:
                for fileName in self.targets[element]["output"]:
                    if not os.path.isfile(fileName):
                        dirtyTargets.append(element)


        dirtyTargetsVisited=[]
        while dirtyTargets:
            if dirtyTargets[0] in dirtyTargetsVisited:
                dirtyTargets.remove(element)
                continue
            self.targets[dirtyTargets[0]].dirty=True
            #find targets that depends on this target
            for element in requiredTargets:
                if dirtyTargets[0] in requiredTargets[element]:
                    dirtyTargets.append(element)
            dirtyTargetsVisited.append(dirtyTargets[0])
            dirtyTargets=dirtyTargets[1:]
        for element in requiredTargets:
            if self.targets[element].dirty:
                print("target {} is dirty".format(element))

        


    def checkFolderStructure(self,target):
        if target["output"]:
            for element in target["output"]:
                targetPath=os.path.dirname(element)
                Path(targetPath).mkdir(parents=True, exist_ok=True)

    def runCommands(self,batches):
        batches.reverse()
        while batches:
            current_batch=batches[0]
            batches.pop(0)
            commands=[]
            for element in current_batch:
                commands.append(self.targets[element].commands)
                self.checkFolderStructure(self.targets[element])
            tempCompilationTimes={}
            for element in current_batch:
                if self.targets[element]["input"]:
                    tempCompilationTimes["{}/{}".format(self.targets[element]["path"],self.targets[element]["input"])]=os.path.getmtime(self.targets[element]["input"])            
            while commands:
                commands_to_run_parallel=[]
                for command in commands[:]:
                    commands_to_run_parallel.append(command[0])
                    command.pop(0)
                    if len(command)==0:
                        commands.remove(command)

                #for element in commands_to_run_parallel:
                self.run_commands(commands_to_run_parallel)
            for element in current_batch:
                if self.targets[element]["input"]:
                    self.compilationCache.setCompilationTime("{}/{}".format(self.targets[element]["path"],self.targets[element]["input"]),tempCompilationTimes["{}/{}".format(self.targets[element]["path"],self.targets[element]["input"])])
                
    
    def run_commands(self,commands):
        children=[]
        for command in commands:
            print(" ".join(command))
            children.append( subprocess.Popen(command, stdout=subprocess.PIPE))
        for child in children:
            streamdata = child.communicate()[0]
            rc = child.returncode
            if rc:
                raise Exception("Command {} failed".format(command))
   
    def buildCommands(self,buildOrder):
        #build order is already batched so it is a list of lists
        flatList = [item for sublist in buildOrder for item in sublist]
        for element in flatList:
            self.buildCommand(element)
    
    def buildCommand(self,targetName):
        if targetName not in self.targets:
            raise RuntimeError("could not find target {}".format(targetName))
        target=self.targets[targetName]
        rule = target.rule
        if rule not in self.rules:
            raise RuntimeError("rule {} for target {} could not be found".format(rule,targetName))
        target.commands= self.rules[rule](target)
        

    def findRule(self,name):
        if name in self.rules:
            return self.rules("name")
        raise RuntimeError("rule {} not found".format(name))
    
    #return all targets required to build targetName, if no name is specified then it just return all targets
    def getRequiredTargets(self,targetName):
        if not targetName:
            depTargets={}
            for element in self.targets:
                if element in depTargets:
                    raise RuntimeError("target {} already exists in dependency tree".format(element))
                depTargets[element]=self.targets[element].deps
            #sanity check
            for element in depTargets:
                for dep in depTargets[element]:
                    if dep not in depTargets:
                        raise RuntimeError("target {} depends on {} but target is not defined".format(element,dep))
            return depTargets
        else:
            temp_nodes={}
            nodes_to_add=[]
            nodes_to_add.append(targetName)
            while nodes_to_add:
                if nodes_to_add[0] in self.targets.keys():
                    temp_nodes[nodes_to_add[0]]=self.targets[nodes_to_add[0]].deps
                    for element in self.targets[nodes_to_add[0]].deps:
                        if element not in temp_nodes.keys():
                            nodes_to_add.append(element)
                else:
                    temp_nodes[nodes_to_add[0]]=[]
                nodes_to_add.pop(0)
            return temp_nodes

    def decideBuildOrder(self,depTargets):
        sorted=self.topologicalSort(depTargets)
        batches=[[sorted[0]]]
        sorted.pop(0)
        while sorted:
            safe=True
            for element in batches[-1]:
                if element in self.targets.keys():
                    if sorted[0] in self.targets[element].deps:
                        safe=False
            if not safe:
                batches.append([])
            batches[-1].append(sorted[0])
            sorted.pop(0)
        return batches

    def topologicalSort(self,nodes: dict[str, list[str]]) -> list[str]:
        """
        Topological sort for a network of nodes

            nodes = {"A": ["B", "C"], "B": [], "C": ["B"]}
            topological_sort(nodes)
            # ["A", "C", "B"]

        :param nodes: Nodes of the network
        :return: nodes in topological ordermainObject
        """

        # Calculate the indegree for each node
        indegrees = {k: 0 for k in nodes.keys()}
        for name, dependencies in nodes.items():
            for dependency in dependencies:
                indegrees[dependency] += 1

        # Place all elements with indegree 0 in queue
        queue = [k for k in nodes.keys() if indegrees[k] == 0]

        final_order = []

        # Continue until all nodes have been dealt with
        while len(queue) > 0:

            # node of current iteration is the first one from the queue
            curr = queue.pop(0)
            final_order.append(curr)

            # remove the current node from other dependencies
            for dependency in nodes[curr]:
                indegrees[dependency] -= 1

                if indegrees[dependency] == 0:
                    queue.append(dependency)

        # check for circular dependencies
        if len(final_order) != len(nodes):
            raise Exception("Circular dependency found.")

        return final_order

def at(line):
    #print("at-> ",line)
    if not line:
        return False,"",line
    if line[0]=="@":
        val=line[0]
        line=line[1:]
        #print("success")
        return True,val,line
    return False,"",line

def right_parenthesis(line):
    #print("right_parenthesis-> ",line)
    if not line:
        return False,"",line
    if line[0]==")":
        val=line[0]
        line=line[1:]
        #print("success")
        return True,val,line
    return False,"",line


def left_parenthesis(line):
    #print("left_parenthesis-> ",line)
    if not line:
        return False,"",line
    if line[0]=="(":
        val=line[0]
        line=line[1:]
        #print("success")
        return True,val,line
    return False,"",line

def comma(line):
    #print("comma-> ",line)
    if not line:
        return False,"",line
    if line[0]==",":
        val=line[0]
        line=line[1:]
        return True,val,line
    return False,"",line

def left_square_bracket(line):
    #print("left_square-> ",line)
    if not line:
        return False,"",line
    if line[0]=="[":
        val=line[0]
        line=line[1:]
        #print("success")
        return True,val,line
    return False,"",line

def right_square_bracket(line):
    #print("right_square-> ",line)
    if not line:
        return False,"",line
    if line[0]=="]":
        val=line[0]
        line=line[1:]
        return True,val,line
    return False,"",line

def equal(line):
    #print("equal-> ",line)
    if not line:
        return False,"",line
    if line[0]=="=":
        val=line[0]
        line=line[1:]
        return True,val,line
    return False,"",line


def args(line):
    #print("args-> ",line)
    success,arg_name,new_line=name(line)
    if not success:
        return True,{},line
    success,val,new_line=equal(new_line)
    if not success:
        return True,{},line 
    success,arg_val,new_line=items(new_line)
    if not success:
        return True,{},line 
    result={}
    result[arg_name]=arg_val
    #start repetition
    while True:
        success,val,new_line_second=comma(new_line)
        if not success:
            break
        success,arg_name,new_line_second=name(new_line_second)
        if not success:
            break
        success,val,new_line_second=equal(new_line_second)
        if not success:
            break
        success,arg_val,new_line_second=items(new_line_second)
        if not success:
            break
        new_line=new_line_second
        result[arg_name]=arg_val
    return True, result,new_line

def enumerated(line):
    #print("args-> ",line)
    success,val,new_line=left_square_bracket(line)
    if not success:
        return False,"",line
    success,val,new_line=name(new_line)
    if not success:
        return False,"",line 
    result=[]
    result.append(val)
    #start repetition
    while True:
        success,val,new_line_second=comma(new_line)
        if not success:
            break
        success,val,new_line_second=name(new_line_second)
        if not success:
            break
        new_line=new_line_second
        result.append(val)
    success,val,new_line=right_square_bracket(new_line)
    if not success:
        return False,"",line
    return True, result,new_line    

def name(line):
    if not line:
        return False,"",line
    _rex = re.compile("[/0-9a-zA-Z._-]+$")
    if _rex.match(line[0]):
        val=line[0]
        val=val.replace("\n","")
        line=line[1:]
        return True,val,line
    return False,"",line

def items(line):
    #print("item-> ",line)
    success,val,new_line=name(line)
    if not success:
        success,val,new_line=enumerated(line)
        if not success:
            return False,"",line
    return success,val,new_line


def creates(line):
    #print("creates-> ",line)
    success,val,new_line=items(line)
    if not success:
        return False,"",line
    return success,val,new_line

def creation(buildDir : BuildDirectory,line):
    #print("creation-> ",line)
    success,valCreates,new_line=creates(line)
    if not success:
        return False,"",line
    success,val,new_line=equal(new_line)
    if not success:
        return False,"",line
    success,valName,new_line=name(new_line)
    if not success:
        return False,"",line
    success,val,new_line=left_parenthesis(new_line)
    if not success:
        return False,"",line
    success,valArgs,new_line=args(new_line)
    if not success:
        return False,"",line
    success,val,new_line=right_parenthesis(new_line)
    if not success:
        return False,"",line
    targets=[]
    if type(valCreates)==str:
        targets.append(valCreates)
    elif type(valCreates)==list:
        targets=valCreates
    else:
        raise RuntimeError("undefined type")
    for element in targets:
        if element in buildDir.targets:
            raise RuntimeError("duplicate target name {}".format(element))
        target=Target(buildDir)
        target.rule=valName
        target.target=element
        #target.variables=valArgs.copy()
        for arg in valArgs:
            if not target.checkSpecialVariables(arg,valArgs[arg]):
                raise RuntimeError("invalid argument {} for target".format(arg))
        buildDir.targets[element]=target
    return True,"",new_line

def assignment(buildDir : BuildDirectory,line):
    success,val,new_line=at(line)
    if not success:
        return False,"",line 
    success,valName,new_line=name(new_line)
    if not success:
        return False,"",line
    success,val,new_line=equal(new_line)
    if not success:
        return False,"",line
    success,valItems,new_line=items(new_line)
    if not success:
        return False,"",line
    if not buildDir.checkSpecialVariables(valName,valItems):
        raise RuntimeError("Undefined variable {} in target file".format(valName))
    return True,"",new_line

def start(buildDir : BuildDirectory,line):
    success,val,new_line= creation(buildDir,line)
    if success:
        return success,val,new_line
    return assignment(buildDir,line)

def match(buildDir : BuildDirectory,line):
    success,val,new_line= start(buildDir,line)
    #print(new_line)
    assert success
    assert len(new_line)==0



def loadTargetFile(buildDir : BuildDirectory,fileName:str):
    with open(fileName) as f:
        for line in f:
            if line[0]!="\n" and line[0]!="#":
                #print(line,end="")
                split_line=re.split('([,|(|)|=|\]|\[|@])', line)
                clean_line = [i for i in split_line if i and i!="\n"]
                match(buildDir,clean_line)

def pathToModuleName(path):
    return path.replace(os.sep,".")


def loadRuleFile(buildDir : BuildDirectory,currentPath:str) :
    fileName="BuildConfig.py"
    fullPath=currentPath+os.sep+fileName
    moduleName=pathToModuleName(fullPath)
    if os.path.isfile(fileName):
        spec = importlib.util.spec_from_file_location(moduleName, fileName)
        foo = importlib.util.module_from_spec(spec)
        sys.modules[moduleName] = foo
        spec.loader.exec_module(foo)
        from inspect import getmembers, isfunction
        functions=getmembers(foo, isfunction)
        for element in functions:
            if element[0]!="init":
                buildDir.rules[element[0]]=element[1]
            else:
                element[1](buildDir.variables)



parser = argparse.ArgumentParser(prog='coby')
parser.add_argument('-file',"-f")
arguments = parser.parse_args()
fileName="Build"
if arguments.file:
    fileName=arguments.file
if __name__ == "__main__":
    buildDir=BuildDirectory()
    buildDir.path=os.getcwd()
    loadRuleFile(buildDir,os.getcwd())
    loadTargetFile(buildDir,fileName)
    #print(buildDir)
    buildDir.build()

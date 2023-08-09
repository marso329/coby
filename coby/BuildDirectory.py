import re
import os
import importlib.util
import sys
import subprocess
from pathlib import Path

import coby 
from coby import FileCompilationTimesCache
from coby import TargetFile
from coby import scanner

class Target:
    def __init__(self,buildDir):
        self.rule=""
        self.target=""
        self.deps=[]
        self.input=""
        self.BMI=""
        self.objectFile=""
        self.buildDir=buildDir
        self.output=[]
        self.commands=[]
        self.lastChangeTime=0
        self.dirty=False
        self.automatic=False
        self.imports=[]
        self.exports=[]
    def __str__(self):
        returnString="("
        returnString+="rule: "+self.rule+", target: "+self.target+", deps: "+str(self.deps) +", input: "+self.input+", output: "+str(self.output)
        returnString+=")"
        return returnString
    def __getitem__(self, key):
        if key=="deps":
            realTarget=[]
            for element in self.deps:
                realTarget.append(self.buildDir.findTarget(element))
            return realTarget
        if key=="input":
            return self.buildDir.path+os.sep+self.input
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
        if key=="BMI":
            return self.BMI
        if key=="objectFile":
            return self.objectFile
        if key=="path":
            return self.buildDir.path
        
        val= self.buildDir.searchFromTarget(key)
        if val:
            return val
        raise KeyError("key {} not found in directory {}".format(key,self.buildDir.path))
    def __setitem__(self, key, value):
        if key=="output":
            self.output.append(value)
        elif key=="input":
            self.input=value
        elif key=="BMI":
            if self.BMI:
                raise RuntimeError("BMI is only allowed to be set once")
            self.BMI=value
        elif key=="objectFile":
            if self.objectFile:
                raise RuntimeError("BMI is only allowed to be set once")
            self.objectFile=value
        
        else:
            raise RuntimeError("key {} undefined".format(key))



    def checkSpecialVariables(self,variable:str,val):
        if variable.lower()=="input":
            self.input=val
            return True
        if variable.lower()=="deps":
            self.deps=val
            return True
        if variable.lower()=="automatic":
            self.automatic=val=="true"
            return True
        return False



class BuildDirectory:
    def __init__(self,ruleFile,targetFile,kid=None,parent=None,path=""):
        self.targets={}
        self.rules={}
        self.subdirs=[]
        self.variables={}
        self.default_target=""
        self.ruleFile=ruleFile
        self.targetFile=targetFile
        self.root=False
        self.parent=None
        self.kids=[]
        self.in_source_build=False

        if kid and parent:
            raise RuntimeError("a buildDirectory can't be created with a kid and a parent")
        #checking folder one stop up
        if kid:
            self.path=os.path.dirname(kid.path)
            self.kids.append(kid)
        elif parent:
            self.parent=parent
            self.path=path
        else:
            self.path=os.getcwd()

        self.build_directory=self.path+os.sep+"build"
        self.compilationCache=FileCompilationTimesCache.FileCompilationTimesCache()
        self.checkRuleFile()
        if self.ruleFile:
            self.loadRuleFile()
        self.checkTargetFile()
        if self.targetFile:
            self.loadTargetFile()
        if self.valid():
            self.checkParent()
            self.checkKids()
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
        returnString+="path :"+self.path+"\n"
        returnString+="ROOT: "+str(self.root)
        return returnString
    
    def findRule(self,rule):
        if rule in self.rules:
            return self.rules[rule]
        if self.parent:
            return self.parent.findRule(rule)
        return None

    def checkParent(self):
        if self.parent:
            return
        if self.root:
            return
        self.parent=BuildDirectory("","",self)
        if not self.parent.valid():
            self.parent=None

    def checkKids(self):
        for element in self.subdirs:
            newPath=self.path+os.sep+element
            safe=True
            for kid in self.kids:
                if kid.path==newPath:
                    safe=False
            if safe:
                newKid=BuildDirectory("","",None,self,newPath)
                if newKid.valid():
                    self.kids.append(newKid)


    def valid(self):
        if self.ruleFile or self.targetFile:
            return True
        return False


    def checkRuleFile(self):
        if self.ruleFile:
            self.ruleFile=self.path+os.sep+self.ruleFile
            if not os.path.isfile(self.ruleFile):
                raise RuntimeError("specified rule file {} does not exist".format(self.ruleFile))
        #if it is not specified then it is ok that it does not exists and it will not be loaded
        self.ruleFile="BuildConfig.py"
        self.ruleFile=self.path+os.sep+self.ruleFile
        if not os.path.isfile(self.ruleFile):
            self.ruleFile=None
    
    def checkTargetFile(self):
        if self.targetFile:
            self.targetFile=self.path+os.sep+self.targetFile
            if not os.path.isfile(self.targetFile):
                raise RuntimeError("specified target file {} does not exist".format(self.targetFile))
        #if it is not specified then it is ok that it does not exists and it will not be loaded
        self.targetFile="Build"
        self.targetFile=self.path+os.sep+self.targetFile
        if not os.path.isfile(self.targetFile):
            self.targetFile=None
        



    def loadTargetFile(self):
        self.targetFileInstance=TargetFile.TargetFile(self,self.targetFile)
        self.automaticScanning()

    def automaticScanning(self):
        #need to scan all targets first
        for element in self.targets.values():
            if element.automatic:
                if not element.input:
                    raise RuntimeError("target {} is set to automatic but has no input file".format(element.target))
                self.automaticScanningTarget(element)
        #build the dependency tree
        for element in self.targets.copy().values():
            if element.automatic:
                self.buildAutomaticDependency(element)

    def automaticScanningTarget(self,target):
        fileToScan=target["input"]
        importExports=scanner.scan(fileToScan)
        target.imports=importExports["imports"]
        target.exports=importExports["exports"]
        if target.exports:
            if len(target.exports)!=1:
                raise RuntimeError("target {} has more than one export , this is nor supported".format(target.target))
            #if target.exports[0]!=target.rule:
            #    raise RuntimeError("target {} exports {} , these names must be the same".format(target.target,target.exports[0]))
    
    def checkIfSystemHeader(self,importVal):
        if len(importVal)==1:
            if importVal[0][0]=="<" and importVal[0][-1]==">":
                return True 
        return False
    
    def addSystemHeaderTarget(self,importVal):
        name=importVal[0][1:-1]
        foundTarget=self.findTarget(name)
        if foundTarget:
            return name
        target=Target(self)
        target.target=name
        target.rule="stdlib"
        self.targets[name]=target
        return name


    def buildAutomaticDependency(self,target):
        for element in target.imports:
            if self.checkIfSystemHeader(element):
                systemHeaderTarget= self.addSystemHeaderTarget(element)
                target.deps.append(systemHeaderTarget)
                continue
            target.deps.append(element[0])
            #needs to find target after all files have been parsed
            
            # dependencyTarget=self.findTargetFromExport(element)
            # if dependencyTarget:
            #     if dependencyTarget==target:
            #         raise RuntimeError("target {} depends on it self".format(target.target))
            #     target.deps.append(dependencyTarget.target)
            # else:
            #     raise RuntimeError("target {} depends on {} but it wasn't found ".format(target.target,element))

    #search whole project, order doesn't matter since names shall be unique
    def findTargetFromExport(self,export,searcher=None):
        print("searching {}".format(self.path))
        for element in self.targets.values():
            if element.exports:
                if export ==element.exports[0]:
                    return element
        print(self.kids)
        for element in self.kids:
            if element!=searcher:
                target=element.findTargetFromExport(export,self)
                if target:
                    return target
        if self.parent and self.parent!=searcher:
            return self.parent.findTargetFromExport(export,self)

    def findTarget(self,targetName,searcher=None):
        if targetName in self.targets:
            return self.targets[targetName]
        for element in self.kids:
            if element!=searcher:
                target=element.findTarget(targetName,self)
                if target:
                    return target
        if self.parent and self.parent!=searcher:
            return self.parent.findTarget(targetName,self)
        
        return None

    def findAllTargets(self,searcher=None):
        toReturn=[]
        toReturn+=self.targets.keys()
        for element in self.kids:
            if element!=searcher:
                toReturn+=element.findAllTargets(self)
        if self.parent and self.parent!=searcher:
            toReturn+=self.parent.findAllTargets(self)
        
        return toReturn


    def pathToModuleName(self,path):
        return path.replace(os.sep,".")


    def loadRuleFile(self) :
        moduleName=self.pathToModuleName(self.ruleFile)
        spec = importlib.util.spec_from_file_location(moduleName, self.ruleFile)
        foo = importlib.util.module_from_spec(spec)
        sys.modules[moduleName] = foo
        spec.loader.exec_module(foo)
        from inspect import getmembers, isfunction
        functions=getmembers(foo, isfunction)
        for element in functions:
            if element[0]!="init":
                self.rules[element[0]]=element[1]
            else:
                element[1](self.variables)


    def saveCache(self):
        self.compilationCache.write()

    def getOutputDir(self):
        if self.in_source_build:
            return self.path
        else:
            return self.build_directory

    #this is ugly and should be optimized
    def allDependencies(self,targetName):
        targetsDeps=list(self.getRequiredTargets(targetName).values())
        targetsDepsFlatten=[]
        for element in targetsDeps:
            targetsDepsFlatten.extend(element)
        targetsDepsFlatten = list(dict.fromkeys(targetsDepsFlatten))
        targetsDepsInstances=[self.findTarget(x) for x in targetsDepsFlatten]
        #they way this is used in rules means that a target must depend on itself
        targetsDepsInstances.append(self.findTarget(targetName))
        return targetsDepsInstances




    def searchFromTarget(self,key):
        if key in self.variables:
            return self.variables[key]
        if self.parent:
            return self.parent.searchFromTarget(key)
        return None

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
        if variable.lower()=="root":
            self.root=val.lower()=="true"
            return True     
        return False

    def build(self):
        
        #step one, decide the main target
        decidedTarget=""
        if not self.default_target:
            #all targets
            requiredTargets=self.getRequiredTargets()
            if not requiredTargets:
                print("No targets to build in {}".format(self.path))
                return
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
        
        print(decidedTarget)

        #step two, find all the targets required to build the main target
        requiredTargets=self.getRequiredTargets(decidedTarget)

        print(requiredTargets)

        #step three, find the order in which to build it
        buildOrder=self.decideBuildOrder(requiredTargets)

        print(buildOrder)

        #we need to build the commands in the reverse order
        buildOrder.reverse()

        #step four, build the commands for the targets
        self.buildCommands(buildOrder)

        #revert the reverse
        buildOrder.reverse()

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
                if self.findTarget(target).dirty:
                    newBatch.append(target)
            if newBatch:
                newOrder.append(newBatch)
        return newOrder
    def checkForDirtyFiles(self,requiredTargets):
        buildTargets=list(requiredTargets.keys())
        dirtyTargets=[]
        #if they define an input file then we check if it has changed
        for element in buildTargets:
            foundTarget=self.findTarget(element)
            if foundTarget["input"]:
                fileName=foundTarget["input"]
                if self.compilationCache.getCompilationTime(fileName)!=os.path.getmtime(fileName):
                    dirtyTargets.append(element)
        #the we check if the output file(s) exists
        for element in buildTargets:
            foundTarget=self.findTarget(element)
            if foundTarget["output"]:
                for fileName in foundTarget["output"]:
                    if not os.path.isfile(fileName):
                        dirtyTargets.append(element)


        dirtyTargetsVisited=[]
        while dirtyTargets:
            if dirtyTargets[0] in dirtyTargetsVisited:
                dirtyTargets.remove(dirtyTargets[0])
                continue
            self.findTarget(dirtyTargets[0]).dirty=True
            #find targets that depends on this target
            for element in requiredTargets:
                if dirtyTargets[0] in requiredTargets[element]:
                    dirtyTargets.append(element)
            dirtyTargetsVisited.append(dirtyTargets[0])
            dirtyTargets=dirtyTargets[1:]
        for element in requiredTargets:
            if self.findTarget(element).dirty:
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
                foundTarget=self.findTarget(element)
                commands.append(foundTarget.commands)
                self.checkFolderStructure(foundTarget)
            tempCompilationTimes={}
            for element in current_batch:
                foundTarget=self.findTarget(element)
                if foundTarget["input"]:
                    tempCompilationTimes["{}/{}".format(foundTarget["path"],foundTarget["input"])]=os.path.getmtime(foundTarget["input"])            
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
                foundTarget=self.findTarget(element)
                if foundTarget["input"]:
                    self.compilationCache.setCompilationTime("{}/{}".format(foundTarget["path"],foundTarget["input"]),tempCompilationTimes["{}/{}".format(foundTarget["path"],foundTarget["input"])])
                
    
    def run_commands(self,commands):
        children=[]
        for command in commands:
            #special case when we do piping
            if type(command[0])==tuple:
                print(" ".join(command[0][1]))
                output=subprocess.PIPE
                if len(command)>1 and command[1][0]=="file":
                    output=open(command[1][1],"a")
                children.append( subprocess.Popen(command[0][1], stdout=output))
                for element in command[1:]:
                    children.append( subprocess.Popen(command[0][1], stdout=subprocess.PIPE,stdin=children[-1].stdout))
            else:    
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
        target=self.findTarget(targetName)
        if not target:
            raise RuntimeError("could not find target {}".format(targetName))
        rule = target.rule
        foundRule=self.findRule(rule)
        if not foundRule:
            raise RuntimeError("rule {} for self.rules[rule]target {} could not be found".format(rule,targetName))
        target.commands= foundRule(target)
        

    #return all targets required to build targetName, if no name is specified then it just return all targets
    def getRequiredTargets(self,targetName=""):
        if not targetName:
            depTargets={}
            allProjectTargets=self.findAllTargets()
            for element in allProjectTargets:
                if element in depTargets:
                    raise RuntimeError("target {} already exists in dependency tree".format(element))
                depTargets[element]=self.findTarget(element).deps
            #sanity check
            for element in depTargets:
                for dep in depTargets[element]:
                    print(depTargets)
                    if dep not in depTargets:
                        raise RuntimeError("target {} depends on {} but target is not defined".format(element,dep))
            return depTargets
        else:
            temp_nodes={}
            nodes_to_add=[]
            nodes_to_add.append(targetName)
            while nodes_to_add:
                foundTarget=self.findTarget(nodes_to_add[0])
                if foundTarget:
                    temp_nodes[nodes_to_add[0]]=foundTarget.deps
                    for element in foundTarget.deps:
                        if element not in temp_nodes.keys():
                            nodes_to_add.append(element)
                else:
                    #why the fuck this
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
                foundTarget=self.findTarget(element)
                if foundTarget:
                    if sorted[0] in foundTarget.deps:
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

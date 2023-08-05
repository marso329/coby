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

import argparse

import coby
from coby import BuildDirectory
from coby import scanner


def buildDirectory(ruleFile,targetFile):
    buildDir=BuildDirectory.BuildDirectory(ruleFile,targetFile)
    buildDir.build()    

def buildFunction(arguments):
    print("building")
    ruleFile=None
    if arguments.rule:
        ruleFile=arguments.rule
    targetFile=None
    if arguments.target:
        targetFile=arguments.target
    buildDirectory(ruleFile,targetFile)

def printFileImportExportsFunction(arguments):
    print("printfile")
    if not arguments.file:
        raise RuntimeError("printFileImportExports requires a file")
    scanner.scan(arguments.file)
def main():
    parser = argparse.ArgumentParser(prog='coby')
    #parser.add_argument('toDo',nargs='?',default="build",type=str)
    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands',help='additional help')
    build=subparsers.add_parser('build')
    build.add_argument('-rule',"-r")
    build.add_argument('-target',"-t")
    build.set_defaults(func=buildFunction)
    printFileImportExports=subparsers.add_parser('printFileImportExports')
    printFileImportExports.add_argument('-file',"-f")
    printFileImportExports.set_defaults(func=printFileImportExportsFunction)
    arguments = parser.parse_args()
    arguments.func(arguments)

if __name__ == "__main__":
    main()


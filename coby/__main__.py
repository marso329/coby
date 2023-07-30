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


def buildDirectory(ruleFile,targetFile):
    buildDir=BuildDirectory.BuildDirectory(ruleFile,targetFile)
    buildDir.build()    


def main():
    parser = argparse.ArgumentParser(prog='coby')
    parser.add_argument('-rule',"-r")
    parser.add_argument('-target',"-t")
    arguments = parser.parse_args()
    ruleFile=None
    if arguments.rule:
        ruleFile=arguments.rule
    targetFile=None
    if arguments.target:
        targetFile=arguments.target
    buildDirectory(ruleFile,targetFile)

if __name__ == "__main__":
    main()


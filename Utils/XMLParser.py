#!/usr/bin/python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET

def LateXML2Dict(node, ind=''):
  nodeSize = len(node)
  dDict = {}
  #print ind+"nodeSize:", nodeSize
  if nodeSize>0:
    childDict = {}
    for child_of_root in node:
      itDict = LateXML2Dict(child_of_root, ind+'  ')
      #print ind+"itDict:", itDict
      childTag = child_of_root.tag
      #print ind+"childTag:", childTag
      #childDict.update(itDict)
      #print ind+"childDict:", childDict
    
      childDictKeys = childDict.keys()
      #print ind+"==>childDictKeys:", childDictKeys
      #print ind+"==>["+childTag+"] in keys:", (childTag in childDictKeys)
      if childTag in childDictKeys:
	#print ind+"==>SWAPPING", childDict
	tmp = childDict[childTag]
	#print ind+"==>ELEMENT LIST:", tmp, ":", type(tmp)
	
	if type(childDict[childTag]) is not type([]):
	  #print ind+"==>NOT A LIST:", childDict[childTag]
	  childDict[childTag] = []
	  childDict[childTag].append(tmp)
	#else:
	  #print ind+"==>IS A LIST:", childDict[childTag]
	#print ind+"==>NOW A LIST tag:"+childTag+":", childDict[childTag]
	#print ind+"==>SWAPPING WITH", itDict[childTag], ":", type(itDict[childTag])
	childDict[childTag].append(itDict[childTag])
	#print ind+"==>SWAP RESULT:", childDict[childTag]

      else:
	childDict.update(itDict)
	#print ind+"==>NOT SWAPPING", childDict
    attrib = node.attrib.items()
    attribSize = len(attrib)
    #print ind+"==>#attrib:", attribSize
    
    if attribSize>0:
      for attrTag, attrText in attrib:
	#print ind+"-->",attrTag,":", attrText
	childDict.update({attrTag: attrText})
    #print ind+"--> childDict:", childDict
    tag = node.tag
    #print ind+"--> tag:", tag
    #print ind+"-->childDict:", childDict
    dDict[tag] = childDict
  else:
    tag = node.tag
    text= node.text
    if text is not None and len(text)>0:
      text= text.strip()
    else:
      text = ''
    #textSize = len(text)
    attrib = node.attrib.items()
    attribSize = len(attrib)
    #print ind+"tag:", tag
    #print ind+"text(",len(text), "):", text
    #print ind+"#attrib:", attribSize
    dDict[tag] = text
    
    if attribSize>0:
      for attrTag, attrText in attrib:
	#print ind+"APPEND:",attrTag,":", attrText
	dDict.update({attrTag: attrText})
  
  #print ind+"dDict:"
  #pprint.pprint(dDict)
  #print ind+"================================"
  return dDict

def ParseXml2Dict(sFile, rootName):
  tree = ET.ElementTree(file=sFile)
  root = tree.getroot()
  
  result = LateXML2Dict(root)
  return result[rootName]


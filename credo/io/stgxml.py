##  Copyright (C), 2010, Monash University
##  Copyright (C), 2010, Victorian Partnership for Advanced Computing (VPAC)
##
##  This file is part of the CREDO library.
##  Developed as part of the Simulation, Analysis, Modelling program of
##  AuScope Limited, and funded by the Australian Federal Government's
##  National Collaborative Research Infrastructure Strategy (NCRIS) program.
##
##  This library is free software; you can redistribute it and/or
##  modify it under the terms of the GNU Lesser General Public
##  License as published by the Free Software Foundation; either
##  version 2.1 of the License, or (at your option) any later version.
##
##  This library is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
##  Lesser General Public License for more details.
##
##  You should have received a copy of the GNU Lesser General Public
##  License along with this library; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
##  MA  02110-1301  USA

"""
This module is for accessing, manipulating and writing out XML files stored in
the StGermain data format.

It currently does not create a new Object-oriented representation of XML docs
themselves, but most functions operate on an ElementTree object
representative of an element in an open Stg XML document.
"""
from builtins import map

import os
import shlex
import subprocess as subp
from xml.etree import ElementTree as etree
import credo

STG_ROOT_TAG = 'StGermainData'
STG_NS = 'http://www.vpac.org/StGermain/XML_IO_Handler/Jun2003'
_STG_NS_LXML = '{%s}' % STG_NS

STG_INCLUDE_TAG = "include"
STG_STRUCT_TAG = "struct"
STG_LIST_TAG = "list"
STG_PARAM_TAG = "param"
STG_ELEMENT_TAG = "element"
_stgElementBaseTags = [STG_STRUCT_TAG, STG_LIST_TAG, STG_PARAM_TAG]
STG_MERGE_ATTRIB = "mergeType"
STG_MERGE_TYPES = ['append','merge','replace']
STG_IMPORT_TAG = "import"
STG_PLUGINS_TAG = "plugins"
STG_COMPONENTS_TAG = "components"
STG_TOOLBOX_TAG = "toolbox"
_stgSpecialListTags = [STG_IMPORT_TAG, STG_PLUGINS_TAG]
_stgSpecialStructTags = [STG_COMPONENTS_TAG, STG_ROOT_TAG]
_stgSpecialParamTags = [STG_TOOLBOX_TAG]
_stgSpecialLists = {
    STG_STRUCT_TAG:_stgSpecialStructTags,
    STG_LIST_TAG:_stgSpecialListTags,
    STG_PARAM_TAG:_stgSpecialParamTags }

############
# Utility functions

def indentForPrettyPrint(elem, level=0, spacer="  "):
    """Indent an XML file in xml.etree format, useful for pretty printing.

    Credit to http://infix.se/2007/02/06/gentlemen-indent-your-xml"""

    i = "\n" + level*spacer
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indentForPrettyPrint(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "  "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def addNsPrefix(tagName):
    """Simple utility func to add the Namespace prefix that LXML adds to element
    tag names when it parses in from a file"""
    return _STG_NS_LXML+tagName

def removeNsPrefix(tagName):
    """Simple utility func to remove the Namespace prefix that LXML adds to
    element tag names when it parses in from a file"""
    if tagName.startswith(_STG_NS_LXML):
        return tagName[len(_STG_NS_LXML):]

###################
# Key function for navigating a hierarchy when strSpec is given in StGermain
# command-line style

def navigateStrSpecHierarchy(currNode, strSpec, insertMode=False):
    """Navigate a document, based on a remaining StGermain command-line style
    element specification.
    Returns currNode, nodeName of the final entry in the hierarchy"""
    # Parse the string, checking if it specifies to recurse into a sub-struct or
    # list.

    if strSpec == "":
        raise ValueError("Can't operate on an empty strSpec string")

    structSepPrefix, structSep, structRem = strSpec.partition(".")
    listSepPrefix, listSep, listFirstRem = structSepPrefix.partition("[")

    # The list is handled slightly different to structs: since list items are
    # un-named, an immediate list spec (eg [5]) with no prefix means we're done.
    if listSep == '[':
        # Check and handle the list separator first, since the code above
        # made sure that this must occur before any structSeps

        # First re-do the partition, to get all remainder
        listStartName, listStartSep, listStartRem = strSpec.partition('[')
        listContents, listEndSep, listEndRem = listStartRem.partition(']')
        if listEndSep != ']':
            raise ValueError("Navigating section \"%s\" specified: badly"\
                " formed list found, not closed correctly with '%s'."
                % (strSpec, "]") )

        listNode = _getListNodeAtCurrent(currNode, listStartName, strSpec)
        if listNode == None:
            # TODO - insert mode
            raise ValueError("Navigating section \"%s\" specified: list"\
                " \"%s\" doesn't exist at this level of XML file."\
                % (strSpec, listStartName) )

        if listEndRem == "":
            # We are done, because there's only one list spec at current context
            # remaining in the string
            return listNode, listStartSep+listStartRem
        else:
            # Navigate into the list contents
            listItemNode = _getListItemFromStrSpec(listNode,
                '['+listContents+']')

            # Check the remaining contents appropriate
            if listEndRem[0] == '.':
                # Consume the . for a dictionary at next section
                listEndRem = listEndRem[1:]
            elif listEndRem[0] != '[':
                raise ValueError("Navigating section \"%s\" specified:"\
                    " List not followed by either a '%s' or '%s', error."\
                    % (strSpec, '[', '.'))

            #recurse again on the remainder, since there's stuff left to handle
            return navigateStrSpecHierarchy(listItemNode, listEndRem)
    elif structSep == '.':
        structName = structSepPrefix
        # There is no list separator, but a struct to recurse into.
        structNode = getStructNode(currNode, structName)
        if structNode == None:
            if insertMode:
                structNode = insertStructNode(currNode, structName)
            else:
                raise ValueError("Navigating section \"%s\" specified: struct"\
                    " \"%s\" doesn't exist at this level of XML file."\
                    % (strSpec, structName) )
        # Recursively process the rest of the specification
        return navigateStrSpecHierarchy(structNode, structRem)
    else:
        # We are at the correct hierarchy level - just return.
        return currNode, strSpec


def getItemFromStrSpec_CurrentCtx(currCtxNode, nodeSpecStr):
    """Gets the node at a current context.
    If context is a struct, treats nodeSpecStr as a named element.
    If context is a list, nodeSpecStr must be a list specifier."""
    currCtxNodeType = getElementType(currCtxNode)
    if currCtxNodeType == STG_STRUCT_TAG:
        eltNode = _getNamedElementNode(currCtxNode, nodeSpecStr)
    elif currCtxNodeType == STG_LIST_TAG:
        eltNode = _getListItemFromStrSpec(currCtxNode, nodeSpecStr)
    else:
        raise ValueError("Context node with tag %s is of incorrect type %s"\
            % (currCtxNode.tag, currCtxNodeType))
    return eltNode

def _getListItemFromStrSpec(currListNode, listItemStr):
    """ Where listItemStr is in the form [4], or []"""
    if listItemStr[0] != '[':
        raise ValueError("\"%s\" not a well specified list item:"\
            " not opened correctly with '%s'."
            % (listItemStr, "[") )
    listContents, listEndSep, listEndRem = listItemStr[1:].partition(']')
    if listEndSep != ']':
        raise ValueError("\"%s\" not a well specified list item:"\
            " not closed correctly with '%s'."
            % (listItemStr, "]") )
    elif listEndRem != "":
        raise ValueError("Navigating section \"%s\" specified: badly"\
            " formed list found, trailing characters '%s' after list"\
            " closed." % (listItemStr, listEndRem))

    listIndex = _getListIndex(listContents)
    # TODO - modify later for insertion
    assert listIndex != None
    if not listIndex < len(currListNode):
        raise ValueError("Parsing listItemStr '%s', asked for list index %d,"\
            " but list has only %d items"\
            % (listItemStr, listIndex, len(currListNode)))

    # (Using the etree concise format here)
    listItemNode = currListNode[listIndex]
    return listItemNode

def _getListIndex(listIndexStr):
    if listIndexStr == "":
        listIndex = None
    else:
        if not listIndexStr.isdigit():
            raise ValueError("list index '%s' isn't a set of digits"\
                % (listIndexStr))
        listIndex = int(listIndexStr)
    return listIndex

############################
# For getting stuff out of an existing XML doc

def getNodeFromStrSpec(parentNode, strSpec):
    """From a given specification of a node in a StGermain model file (eg
    plugins[0].Context), return the element to operate on."""

    resultNode, lastSpecStr = navigateStrSpecHierarchy(parentNode, strSpec)

    # We just need to return the element with the remaining spec string at the
    # current context
    # Remember it could be either a name (at a struct level), or an index (at a
    # list level).
    # It can also be of any any element type:-
    # thus if the calling function expects a param, list or
    # dict specifically, will need to check for that.
    elementNode = getItemFromStrSpec_CurrentCtx(resultNode, lastSpecStr)
    if elementNode == None:
        raise ValueError("Navigating str spec \"%s\": last element"\
            " \"%s\" doesn't exist at correct level of XML file."\
            % (strSpec, lastSpecStr) )
    return elementNode

def getElementType(elementNode):
    """Checks the "type" of a StGermain data node element.
    Here, we deal with 3 possibilities:

    * The <param>, <list>, <struct> node tag format.
    * The <elmement> tag format, where type is an attribute.
    * The special elements <import>, <plugins> -> list, <components> -> dict.
    """

    # The _STG_NS_LXML prefixes included below since ETree prefixes these to
    # tag names to represent the namespace used when parsing in files.

    tag = elementNode.tag

    if tag in _stgElementBaseTags:
        return tag
    elif tag in list(map(addNsPrefix, _stgElementBaseTags)):
        return removeNsPrefix(tag)
    elif tag == STG_ELEMENT_TAG or tag == addNsPrefix(STG_ELEMENT_TAG):
        try:
            typeAttr = elementNode.attrib['type']
        except KeyError:
            raise ValueError("Given node with tag '%s' doesn't specify"\
                " its type correctly." % (elementNode.tag))

        if typeAttr in _stgElementBaseTags:
            return typeAttr
        else:
            raise ValueError("Given node with tag '%s', type attr '%s' is"\
                " not a StGermainData element of known type."\
                % (elementNode.tag, typeAttr))
    elif tag in _stgSpecialParamTags \
            or tag in list(map(addNsPrefix, _stgSpecialParamTags)):
        return STG_PARAM_TAG
    elif tag in _stgSpecialListTags \
            or tag in list(map(addNsPrefix, _stgSpecialListTags)):
        return STG_LIST_TAG
    elif tag in _stgSpecialStructTags \
            or tag in list(map(addNsPrefix, _stgSpecialStructTags)):
        return STG_STRUCT_TAG
    else:
        raise ValueError("Given node with tag '%s' is not a StGermainData"
            " element of known type." % (elementNode.tag))

def _getListNodeAtCurrent(currNode, listName, strSpec):
    """Get the list named at the current XML level. Note that if the list name
    is '', then assumes current level is a list"""
    if listName == "":
        # This case is allowed - suppose we are in a recursive loop, dealing
        # with a list entry within a list - then there would be no prefix,
        # so just check we're already within a list
        listNode = currNode
        if STG_LIST_TAG != getElementType(listNode):
            raise ValueError("Navigating section \"%s\" specified: implies"\
                    " current section is a list, but is actually a %s element."\
                    % (strSpec, getElementType(listNode)))
    else:
        listNode = getListNode(currNode, listName)
    return listNode

def getParamValue(elNode, paramName, castFunc):
    """Gets the value of a parameter from a StGermain XML model file that's a
    child of the given elNode, with the given paramName.
    The value is cast according to the castFunc, which should be a standard
    Python casting function, e.g. 'int', 'double' or 'bool'."""
    paramElt = getParamNode(elNode, paramName)
    if paramElt is not None:
        # Strip any spaces around the parameter name first.
        return castFunc(paramElt.text.strip())
    else:
        return None

def strToBool(boolStr):
    """Converts a string (eg from a param in XML) to a Python Bool and
    returns this, using same idiom as in StGermain.

    (See Dictionary_Entry_Value_AsBool() in Dictionary_Entry_Value.c in
    StGermain/Base/IO)."""
    if boolStr.lower() in ['1','true','t','yes','y','on']:
        return True
    elif boolStr.lower() in ['0','false','f','no','n','off']:
        return False
    else:
        raise ValueError("String given, '%s', doesn't convert to a Boolean"\
            " using StGermain idiom." % (boolStr))

def _getSpecialTagNode(elNode, eltName, eltType):
    '''Checks to see if the current elNode has a child element with special tag
    equal to given eltName'''

    try:
        specialTagsList = _stgSpecialLists[eltType]
    except KeyError:
        raise ValueError("The eltType argument must be one of %s" \
            % list(_stgSpecialLists.keys()))

    for specialTag in specialTagsList:
        if eltName == specialTag:
            for childNode in elNode.getchildren():
                if childNode.tag == addNsPrefix(specialTag):
                    return childNode
    return None

def getParamNode(elNode, paramName):
    """Returns the element node (in etree form) of a particular Param parameter
    that's a child of the given elNode with given paramName.
    If a node with the given name not found, returns none."""
    # The default schema for written files (eg flattened files) is to use
    # "element" and set a type attribute, rather than "param" directly.
    eltNode = _getNamedElementNode_elTag(elNode, paramName, elType=STG_PARAM_TAG)
    if eltNode is not None: return eltNode
    for paramNode in elNode.getchildren():
        if paramNode.tag != addNsPrefix('param'): continue
        if paramNode.attrib['name'] == paramName:
            return paramNode

    specialNode = _getSpecialTagNode(elNode, paramName, STG_PARAM_TAG)
    if specialNode is not None: return specialNode

    return None

def getStructNode(elNode, structName):
    """Returns the element node (in etree form) of a particular struct element
    that's a child of the given elNode with given structName.
    If a node with the given name not found, returns none."""
    eltNode = _getNamedElementNode_elTag(elNode, structName, elType=STG_STRUCT_TAG)
    if eltNode is not None: return eltNode
    for structNode in elNode.getchildren():
        if structNode.tag != addNsPrefix('struct'): continue
        if structNode.attrib['name'] == structName:
            return structNode

    specialNode = _getSpecialTagNode(elNode, structName, STG_STRUCT_TAG)
    if specialNode is not None: return specialNode

    return None

def getListNode(elNode, listName):
    """Returns the element node (in etree form) of a particular list element
    that's a child of the given elNode with given listName.
    If a node with the given name not found, returns none."""
    eltNode = _getNamedElementNode_elTag(elNode, listName, elType=STG_LIST_TAG)
    if eltNode is not None: return eltNode
    for listNode in elNode.getchildren():
        if listNode.tag != addNsPrefix('list'): continue
        if listNode.attrib['name'] == listName:
            return listNode

    specialNode = _getSpecialTagNode(elNode, listName, STG_LIST_TAG)
    if specialNode is not None: return specialNode

    return None

def _getNamedElementNode(ctxNode, elName, elType=None):
    """Returns the element node (in etree form) of a particular element
    that's a child of the given ctxNode with given elName.
    If a node with the given name not found, returns none.
    If elType is specified, will only return nodes of the given type.
    (Not designed to be used directly, but by getList etc.)
    Searches in both the element tag format (used by output files), and
    the param, list, struct format - and also for 'special' model elements such
    as plugins, imports and components."""
    eltNode = _getNamedElementNode_elTag(ctxNode, elName)
    if eltNode is not None: return eltNode
    # now check for the 'special' element tags
    for eltNode in ctxNode.getchildren():
        # in this case, e.g. the list with asked for name 'import' will have
        # tag 'import'
        if eltNode.tag == addNsPrefix(elName):
            if eltNode.tag in list(map(addNsPrefix, _stgSpecialParamTags)):
                return eltNode
            if eltNode.tag in list(map(addNsPrefix, _stgSpecialListTags)):
                return eltNode
            elif eltNode.tag in list(map(addNsPrefix, _stgSpecialStructTags)):
                return eltNode
    # now check the old param, list, struct format
    for eltNode in ctxNode.getchildren():
        if eltNode.tag in list(map(addNsPrefix, _stgElementBaseTags)):
            if elName == eltNode.attrib['name']:
                return eltNode
    return None

def _getNamedElementNode_elTag(elNode, elName, elType=None):
    """Returns the element node (in etree form) of a particular element
    that's a child of the given elNode with given elName.
    If a node with the given name not found, returns none.
    If elType is specified, will only return nodes of the given type.
    (Not designed to be used directly, but by getList etc.)
    Searches in the element tag format."""

    for eltNode in elNode.getchildren():
        if eltNode.tag != addNsPrefix('element'): continue
        if eltNode.attrib['name'] == elName:
            if elType == None or eltNode.attrib['type'] == elType:
                return eltNode
    return None

#############################
# For manipulating/updating an existing XML doc, using the eTree package

def createNewStgDataDoc():
    """Create a new empty StGermain model XML file (can be merged with other
    model files).

    :returns: a tuple of the new xml doc (Element Tree), and the root node
      of the new doc."""
    nsMap = {None: STG_NS}
    # For the Python 2.5 version xml.etree, namespace mapping is simplified
    root = etree.Element(STG_ROOT_TAG, xmlns=STG_NS)
    xmlDoc = etree.ElementTree(root)
    return xmlDoc, root

def setMergeType(xmlNode, mergeType):
    """Set the "MergeType" of an XML node: usually for writing new nodes in an
    XML designed to over-ride existing XML of a model."""
    if mergeType is not None:
        if mergeType not in STG_MERGE_TYPES:
            raise ValueError("The mergeType provided, '%s', is not one of"\
                " the StGermain Model XML allowed merge types (%s)"\
                % (mergeType, STG_MERGE_TYPES))
        xmlNode.attrib[STG_MERGE_ATTRIB] = mergeType

# TODO: really needed??
def insertNamedElementNode(parentNode, elementName, createType):
    elementNode = etree.SubElement(parentNode, createType, name=elementName)
    setMergeType(paramEl, "replace")
    return elementNode

def writeParam(parentNode, paramName, paramVal, mt=None):
    """Writes a particular parameter, with name of paramName, val of paramVal,
    to the open XML file at position specified by parentNode."""
    paramEl = etree.SubElement(parentNode, STG_PARAM_TAG, name=paramName)
    setMergeType(paramEl, mt)
    paramEl.text = str(paramVal)
    return paramEl

def writeParamSet(parentNode, paramsDict, mt=None):
    """Writes a set of parameters, with name:value mappings as specified by
    paramsDict, to the open XML file at position specified by parentNode."""
    for paramName, paramVal in list(paramsDict.items()):
        writeParam(parentNode, paramName, paramVal, mt)

def writeParamList(parentNode, listName, paramVals, mt=None):
    '''Write a Stg XML List structure, made up purely of (unnamed) parameters'''
    listElt = etree.SubElement(parentNode, STG_LIST_TAG, name=listName)
    setMergeType(listElt, mt)
    for paramVal in paramVals:
        pElt = etree.SubElement(listElt, STG_PARAM_TAG)
        pElt.text = str(paramVal)
    return listElt

def writeStruct(parentNode, mt=None):
    '''Write a Stg XML List structure, made up purely of (unnamed) parameters'''
    structElt = etree.SubElement(parentNode, STG_STRUCT_TAG)
    setMergeType(structElt, mt)
    return structElt

def writeStructList(parentNode, listName, mt=None):
    '''Write a Stg XML List structure, made up purely of (unnamed) parameters'''
    listElt = etree.SubElement(parentNode, STG_LIST_TAG, name=listName)
    setMergeType(listElt, mt)
    return listElt

def writeIncludeLine(parantNode, includeValue, mt=None):
    '''Write a Stg XML include line for referencing other input xml files'''
    includeElt = etree.SubElement(parantNode, STG_INCLUDE_TAG)
    setMergeType(includeElt, mt)
    includeElt.text = str(includeValue)
    return includeElt

def writeMergeComponentStruct(rootNode):
    '''Write XML to merge a given component to the components list - and
     return new comp elt'''
    assert rootNode.tag == STG_ROOT_TAG
    compList = etree.SubElement(rootNode, STG_STRUCT_TAG, name="components",\
        mergeType="merge")
    return compList

def writeComponent(parentNode, compName, compType, mt=None):
    '''Write XML to merge a given component to the components list - and
     return new comp elt'''
    compElt = etree.SubElement(parentNode, STG_STRUCT_TAG, name=compName)
    setMergeType(compElt, mt)
    writeParam(compElt, "Type", compType)
    return compElt

def writeMergeComponent(rootNode, compName, compType):
    '''Write XML to merge a given component to the components list - and
     return new comp elt'''
    assert rootNode.tag == STG_ROOT_TAG
    compList = etree.SubElement(rootNode, STG_STRUCT_TAG, name="components",\
        mergeType="merge")
    compElt = etree.SubElement(compList, STG_STRUCT_TAG, name=compName)
    writeParam(compElt, "Type", compType)
    return compElt

# Write out using StGermain command-line specification format
def writeValueUsingStrSpec(rootNode, strSpec, value):
    pass
    # if flattened XML:
    # check str spec exists in flattened XML first

    # Get value from analysis XML (thus avoid creation of new unnec)
    # Set the value
    # This will be smart enough to know the type of variable used, and set
    #  appropriately.
    #

#def insertNodeAt
    # navigate hierarchy - replace mode
    # insert node name at remainder, of appropriate type
    #  if node is param, only allow: Bool, int, double
    #  if node is list, only allow Python lists
    #  if node is struct, only allow Python dicts
    #  Qtn: do we allow recursive of these?

############################################
# For actual file I/O

def writeXMLDoc(xmlDoc, outFile, prettyPrint=True):
    """Necessary because the xml.etree doesn't include a pretty_print
    functionality by default (unlike lxml)"""
    if prettyPrint:
        indentForPrettyPrint(xmlDoc.getroot())
    xmlDoc.write(outFile)

def writeStgDataDocToFile(xmlDoc, filename):
    """Write a given StGermain xmlDoc to the file given by filename"""
    outFile = open(filename, 'w')
    writeXMLDoc(xmlDoc, outFile)
    outFile.close()

def createFlattenedXML(inputFiles, cmdLineOverrides="",
        flatFilename="output.xml"):
    '''Flatten a list of provided XML files and optionally also
    cmdLineOverrides (string), using the StGermain FlattenXML tool.

    :returns: the file name of the newly created flattened file.'''

    flattenExe = credo.io.stgpath.getVerifyStgExePath('FlattenXML')
    outFileArg = "-output_file=%s" % (flatFilename)

    try:
        argsList = [flattenExe, outFileArg] + inputFiles \
            + shlex.split(cmdLineOverrides)
        p = subp.Popen(argsList, stdout=subp.PIPE, stderr=subp.PIPE)
        (stdout, stderr) = p.communicate()
        # The 2nd clause necessary because FlattenXML doesn't return
        # proper error codes (ie always returns 0) up to 1.4.2 release
        if p.returncode != 0 or stderr != "":
            raise OSError("Error: Command to create flattened file, '%s' on"
                " input files %s, failed, with error msg:\n%s" \
                % (flattenExe,inputFiles,stderr))
    except OSError as e:
        raise OSError("Unexpected failure to execute Flatten command '%s'"\
            " on input files %s. Error msg was:\n%s"\
            % (flattenExe, inputFiles,str(e)))

    return flatFilename

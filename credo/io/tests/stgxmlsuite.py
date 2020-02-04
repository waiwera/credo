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

import os
import tempfile
import unittest
import shutil

from credo.io import stgxml
from xml.etree import ElementTree as etree

class StgXMLTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.dataPath = "sampleData/stgXML"
        self.flatXMLDoc = etree.parse(os.path.join(self.dataPath, "flattenedModel.xml"))
        self.flatXMLRoot = self.flatXMLDoc.getroot()
        self.inXMLDoc = etree.parse(os.path.join(self.dataPath,
            "CosineHillRotateBC.xml"))
        self.inXMLRoot = self.inXMLDoc.getroot()
        self.testParamNode = etree.Element("param", name="dim")
        self.testParamNode.text = "2"

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_getParamNode(self):
        paramNode = stgxml.getParamNode(self.flatXMLRoot, "dim")
        self.assertEqual(paramNode.attrib['name'], "dim")
        self.assertEqual(paramNode.text, "2")
        paramNode = stgxml.getParamNode(self.inXMLRoot, "dim")
        self.assertEqual(paramNode.attrib['name'], "dim")
        # Whitespace not stripped automatically.
        self.assertEqual(paramNode.text.strip(), "2")
        paramNode = stgxml.getParamNode(self.flatXMLRoot, "voodoo")
        self.assertEqual(paramNode, None)

    def test_getListNode(self):
        listNode = stgxml.getListNode(self.flatXMLRoot, "FieldVariablesToCheckpoint")
        self.assertEqual(listNode.attrib['name'], "FieldVariablesToCheckpoint")
        self.assertEqual(listNode.text.strip(), "")
        self.assertEqual(len(listNode), 3)
        listNode = stgxml.getListNode(self.flatXMLRoot, "voodoo")
        self.assertEqual(listNode, None)
        # Test for the plugins and imports lists, in both
        listNode = stgxml.getListNode(self.inXMLRoot, "plugins")
        self.assertEqual(listNode.attrib['name'], "plugins")
        self.assertEqual(listNode.text.strip(), "")
        self.assertEqual(len(listNode), 2)
        listNode = stgxml.getListNode(self.flatXMLRoot, "plugins")
        self.assertEqual(listNode.tag, stgxml.addNsPrefix("plugins"))
        self.assertEqual(listNode.text.strip(), "")
        # This is a merged list, containing 3 plugin definitions
        self.assertEqual(len(listNode), 3)
        listNode = stgxml.getListNode(self.inXMLRoot, "import")
        self.assertEqual(listNode.attrib['name'], "import")
        self.assertEqual(listNode.text.strip(), "")
        self.assertEqual(len(listNode), 1)
        listNode = stgxml.getListNode(self.flatXMLRoot, "import")
        self.assertEqual(listNode.tag, stgxml.addNsPrefix("import"))
        self.assertEqual(listNode.text.strip(), "")
        self.assertEqual(len(listNode), 1)

    def test_getStructNode(self):
        structNode = stgxml.getStructNode(self.flatXMLRoot, "velocityICs")
        self.assertEqual(structNode.attrib['name'], "velocityICs")
        self.assertEqual(structNode.text.strip(), "")
        self.assertEqual(len(structNode), 2)
        structNode = stgxml.getStructNode(self.inXMLRoot, "velocityICs")
        self.assertEqual(structNode.attrib['name'], "velocityICs")
        self.assertEqual(structNode.text.strip(), "")
        self.assertEqual(len(structNode), 2)
        structNode = stgxml.getStructNode(self.flatXMLRoot, "voodoo")
        self.assertEqual(structNode, None)
        # Test for the components struct, in both
        structNode = stgxml.getStructNode(self.inXMLRoot, "components")
        self.assertEqual(structNode.attrib['name'], "components")
        self.assertEqual(structNode.text.strip(), "")
        structNode = stgxml.getStructNode(self.flatXMLRoot, "components")
        self.assertEqual(structNode.tag, stgxml.addNsPrefix("components"))
        self.assertEqual(structNode.text.strip(), "")

    def test_getParamValue(self):
        dimVal = stgxml.getParamValue(self.flatXMLRoot, "dim", int)
        self.assertEqual(dimVal, 2)
        # Should be able to cast as a string fine.
        dimVal = stgxml.getParamValue(self.flatXMLRoot, "dim", str)
        self.assertEqual(dimVal, "2")
        # Try to get non-existent
        noneVal = stgxml.getParamValue(self.flatXMLRoot, "voodoo", int)
        self.assertEqual(noneVal, None)
        # Try to get a struct
        noneVal = stgxml.getParamValue(self.flatXMLRoot, "components", int)
        self.assertEqual(noneVal, None)
        noneVal = stgxml.getParamValue(self.flatXMLRoot, "temperatureBCs", int)
        self.assertEqual(noneVal, None)
        # Try from the non-flattened file
        dimVal = None
        dimVal = stgxml.getParamValue(self.inXMLRoot, "dim", int)
        self.assertEqual(dimVal, 2)
        dimVal = stgxml.getParamValue(self.flatXMLRoot, "dim", str)
        self.assertEqual(dimVal, "2")

    def test_getElementType(self):
        # Regular params syntax
        testNode = etree.Element(stgxml.STG_PARAM_TAG, name="dim")
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_PARAM_TAG)
        testNode = etree.Element(stgxml.STG_LIST_TAG, name="test")
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_LIST_TAG)
        testNode = etree.Element(stgxml.STG_STRUCT_TAG, name="test")
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_STRUCT_TAG)
        # bad case
        testNode = etree.Element("sillyTag", name="test")
        self.assertRaises(ValueError, stgxml.getElementType, testNode)

        # Element params syntax
        testNode = etree.Element(stgxml.STG_ELEMENT_TAG,
            type=stgxml.STG_PARAM_TAG, name="dim")
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_PARAM_TAG)
        testNode = etree.Element(stgxml.STG_ELEMENT_TAG,
            type=stgxml.STG_LIST_TAG, name="test")
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_LIST_TAG)
        testNode = etree.Element(stgxml.STG_ELEMENT_TAG,
            type=stgxml.STG_STRUCT_TAG, name="test")
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_STRUCT_TAG)
        # Element params syntax - with LXML NS included
        testNode = etree.Element(stgxml._STG_NS_LXML+stgxml.STG_ELEMENT_TAG,
            type=stgxml.STG_PARAM_TAG, name="dim")
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_PARAM_TAG)
        testNode = etree.Element(stgxml._STG_NS_LXML+stgxml.STG_ELEMENT_TAG,
            type=stgxml.STG_LIST_TAG, name="test")
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_LIST_TAG)
        testNode = etree.Element(stgxml._STG_NS_LXML+stgxml.STG_ELEMENT_TAG,
            type=stgxml.STG_STRUCT_TAG, name="test")
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_STRUCT_TAG)
        # bad cases
        testNode = etree.Element(stgxml.STG_ELEMENT_TAG, name="test")
        self.assertRaises(ValueError, stgxml.getElementType, testNode)
        testNode = etree.Element(stgxml.STG_ELEMENT_TAG,
            type="sillyType", name="test")
        self.assertRaises(ValueError, stgxml.getElementType, testNode)

        # Special params - should be recognised
        testNode = etree.Element(stgxml.STG_IMPORT_TAG)
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_LIST_TAG)
        testNode = etree.Element(stgxml.STG_PLUGINS_TAG)
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_LIST_TAG)
        testNode = etree.Element(stgxml.STG_COMPONENTS_TAG)
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_STRUCT_TAG)
        # Special params - NS prefixed
        testNode = etree.Element(stgxml._STG_NS_LXML+stgxml.STG_IMPORT_TAG)
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_LIST_TAG)
        testNode = etree.Element(stgxml._STG_NS_LXML+stgxml.STG_PLUGINS_TAG)
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_LIST_TAG)
        testNode = etree.Element(stgxml._STG_NS_LXML+stgxml.STG_COMPONENTS_TAG)
        self.assertEqual(stgxml.getElementType(testNode), stgxml.STG_STRUCT_TAG)

    def test_getNodeFromStrSpec(self):
        # Try all kinds of combinations of good and bad input
        # For both an original model file, and a flattened input file.
        for xmlRoot in [self.flatXMLRoot, self.inXMLRoot]:
            # Basic elements - good cases
            node = stgxml.getNodeFromStrSpec(xmlRoot, "dim")
            self.assertEqual(node.attrib['name'], "dim")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_PARAM_TAG)
            self.assertEqual(node.text.strip(), "2")
            node = stgxml.getNodeFromStrSpec(xmlRoot, "velocityICs")
            self.assertEqual(node.attrib['name'], "velocityICs")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_STRUCT_TAG)
            # Basic elements - bad cases
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "voodoo")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, ".velocityICs")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "..")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, ".[")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, ".[]")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "[]55")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "[].")
            # TODO: figure out how to handle these below - allowable on recursion,
            # but not from the root.
            #self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
            #    xmlRoot, "[]")
            #self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
            #    xmlRoot, "[0]")

            # Struct recursion - good cases
            node = stgxml.getNodeFromStrSpec(
                xmlRoot, "velocityICs.type")
            self.assertEqual(node.attrib['name'], "type")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_PARAM_TAG)
            self.assertEqual(node.text.strip(), "CompositeVC")
            node = stgxml.getNodeFromStrSpec(xmlRoot,
                "velocityICs.vcList")
            self.assertEqual(node.attrib['name'], "vcList")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_LIST_TAG)
            # Struct recursion - bad cases
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.voodoo")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.[")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.]")

            # Struct - list recursion - good cases
            node = stgxml.getNodeFromStrSpec(
                xmlRoot, "velocityICs.vcList[0]")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_STRUCT_TAG)
            self.assertTrue('name' not in node.attrib)
            self.assertEqual(node[0].text.strip(), "AllNodesVC")
            # Struct - list recursion - bad cases
            # In this case, list is only of length 1.
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.vcList[1]")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.vcList[455]")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.vcList[")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.vcList[455")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.vcList[455]voodoo")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.vcList[455]voodoo.jabbar")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "velocityICs.vcList[.]")
            # TODO: Special case - probably need a "listAppendMode" flag
            #  to decide if this is ok or not
            #self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
            #    xmlRoot, "velocityICs.vcList[]")

            # Deep recursion - good cases
            node = stgxml.getNodeFromStrSpec(
                xmlRoot, "temperatureBCs.vcList[0].Shape")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_PARAM_TAG)
            self.assertEqual(node.attrib['name'], "Shape")
            self.assertEqual(node.text.strip(), "initialConditionShape")
            node = stgxml.getNodeFromStrSpec(
                xmlRoot, "temperatureBCs.vcList[0].variables")
            self.assertEqual(node.attrib['name'], "variables")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_LIST_TAG)
            node = stgxml.getNodeFromStrSpec(
                xmlRoot, "temperatureBCs.vcList[0].variables[0]")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_STRUCT_TAG)
            self.assertTrue('name' not in node.attrib)
            self.assertEqual(node[0].text.strip(), "temperature")
            node = stgxml.getNodeFromStrSpec(
                xmlRoot, "temperatureBCs.vcList[0].variables[0].value")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_PARAM_TAG)
            self.assertEqual(node.attrib['name'], "value")
            self.assertEqual(node.text.strip(), "Temperature_CosineHill")
            # Deep recursion - bad cases
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "temperatureBCs.vcList[0].variables[0]value")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "temperatureBCs.vcList[0].variables[0].val")
            self.assertRaises(ValueError, stgxml.getNodeFromStrSpec,
                xmlRoot, "temperatureBCs.vcList[0][0].val")

            # Getting components, plugins, import (special tags, that will be
            # different in the flattened versus import.
            #import
            node = stgxml.getNodeFromStrSpec( xmlRoot, "import")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_LIST_TAG)
            self.assertEqual(node[0].text.strip(), "StgFEM")
            node = stgxml.getNodeFromStrSpec( xmlRoot, "import[0]")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_PARAM_TAG)
            self.assertTrue('name' not in node.attrib)
            self.assertEqual(node.text.strip(), "StgFEM")
            #plugins
            node = stgxml.getNodeFromStrSpec( xmlRoot, "plugins")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_LIST_TAG)
            self.assertEqual(stgxml.getElementType(node[0]),
                stgxml.STG_STRUCT_TAG)
            node = stgxml.getNodeFromStrSpec( xmlRoot, "plugins[0].Type")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_PARAM_TAG)
            self.assertEqual(node.text.strip(),
                "StgFEM_StandardConditionFunctions")
            #components
            node = stgxml.getNodeFromStrSpec( xmlRoot, "components")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_STRUCT_TAG)
            self.assertEqual(node[0].attrib['name'], "context")
            node = stgxml.getNodeFromStrSpec(
                xmlRoot, "components.context.Type")
            self.assertEqual(stgxml.getElementType(node), stgxml.STG_PARAM_TAG)
            self.assertEqual(node.attrib['name'], "Type")
            self.assertEqual(node.text.strip(), "FiniteElementContext")
            #NB: since the components list in the first XML is un-merged, we
            #can't access this entirely.

    # TODO
    #def test_insertItemAtStrSpec_CurrentCtx(self):
        #stgxml.insertItemAtStrSpec_CurrentCtx(resultNode, lastSpecStr, "2")

    def test_createNewDataDoc(self):
        xmlDoc, root = stgxml.createNewStgDataDoc()
        stgxml.writeParam(root, "testParam", 45)
        stgxml.writeStgDataDocToFile(xmlDoc, "output/testCreate.xml")
        xmlDocRead = etree.parse("output/testCreate.xml")
        rootRead = xmlDocRead.getroot()
        testParamNode = stgxml.getParamNode(rootRead, "testParam")

    def test_getNodeFromStrSpec_CreateMode(self):
        xmlDoc, root = stgxml.createNewStgDataDoc()
        # resultNode, lastSpecStr = stgxml.navigateStrSpecHierarchy(root, "dim")
        # TODO: actually test some stuff
        stgxml.writeStgDataDocToFile(xmlDoc, "output/testInsert.xml")

    # Writing things out tests
    def test_setMergeType(self):
        stgxml.setMergeType(self.testParamNode, 'append')
        self.assertEqual(self.testParamNode.attrib['mergeType'], 'append')
        stgxml.setMergeType(self.testParamNode, 'merge')
        self.assertEqual(self.testParamNode.attrib['mergeType'], 'merge')
        stgxml.setMergeType(self.testParamNode, 'replace')
        self.assertEqual(self.testParamNode.attrib['mergeType'], 'replace')
        self.assertRaises(ValueError, stgxml.setMergeType,
            self.testParamNode, 'FooFoo')

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StgXMLTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

#! /usr/bin/env python3

import argparse
import hashlib
import itertools
import os
import re
import sys

from collections import namedtuple
from lxml import etree as ET

NIDEntry = namedtuple('NIDEntry', ['nidtype', 'nid', 'name', 'prx', 'prxName', 'libraryName', 'libraryFlags', 'versions', 'source'])

def compute_nid(name):
	return hashlib.sha1(name.encode('ascii')).digest()[:4][::-1].hex().upper()

def loadPSPLibdoc(xmlFile):
	tree = ET.parse(xmlFile)
	root = tree.getroot()

	entries = []
	for prx in root.findall("PRXFILES/PRXFILE"):
		prxFile = prx.find("PRX").text
		prxName = prx.find("PRXNAME").text
		for library in prx.findall("LIBRARIES/LIBRARY"):
			libraryName = library.find("NAME").text
			libraryFlags = library.find("FLAGS").text
			for function in library.findall("FUNCTIONS/FUNCTION"):
				functionNID = function.find("NID").text.upper().removeprefix('0X')
				functionName = function.find("NAME").text
				versions = [x.text for x in function.findall("VERSIONS/VERSION")]
				source_elem = function.find("SOURCE")
				source = '' if source_elem is None else ('' if source_elem.text is None else source_elem.text)
				entries.append(NIDEntry(nidtype='fun', nid=functionNID, name=functionName, prx=prxFile,
										prxName=prxName, libraryName=libraryName, libraryFlags=libraryFlags,
										versions=versions, source=source))
			for variable in library.findall("VARIABLES/VARIABLE"):
				variableNID = variable.find("NID").text.upper().removeprefix('0X')
				variableName = variable.find("NAME").text
				versions = [x.text for x in variable.findall("VERSIONS/VERSION")]
				source_elem = variable.find("SOURCE")
				source = '' if source_elem is None else ('' if source_elem.text is None else source_elem.text)
				entries.append(NIDEntry(nidtype='var', nid=variableNID, name=variableName, prx=prxFile,
										prxName=prxName, libraryName=libraryName, libraryFlags=libraryFlags,
										versions=versions, source=source))

	return entries

def updatePSPLibdoc(nidEntries, xmlFile, version=None):
	xmlParser = ET.XMLParser(strip_cdata=False, remove_blank_text=True)
	tree = ET.parse(xmlFile, xmlParser)
	root = tree.getroot()

	numTotalFunctions = 0
	numUnkFunctions = 0
	numUpdatedFunctions = 0

	entries = {}
	for entry in nidEntries:
		entries[entry.nid] = entry

	for prx in root.findall("PRXFILES/PRXFILE"):
		prxFile = prx.find("PRX").text
		libraryList = []
		for library in prx.findall("LIBRARIES/LIBRARY"):
			libraryName = library.find("NAME").text
			libraryList.append(libraryName)
			for funvar in library.findall("FUNCTIONS/FUNCTION") + library.findall("VARIABLES/VARIABLE"):
				numTotalFunctions = numTotalFunctions + 1
				funvarNID = funvar.find("NID").text.upper().removeprefix('0X')
				funvarName = funvar.find("NAME").text
				libDocNidNameUnk = funvarName.upper().endswith(funvarNID)

				if libDocNidNameUnk:
					numUnkFunctions = numUnkFunctions + 1

				if funvarNID in entries:# and entries[funvarNID].libraryName == libraryName:
					nidEntry = entries[funvarNID]
					dictNidNameUnk = nidEntry.name.upper().endswith(funvarNID)

					if libDocNidNameUnk and not dictNidNameUnk:
						print("Updating {} -> {}".format(funvarName, nidEntry.name))
						numUpdatedFunctions = numUpdatedFunctions + 1
						funvar.find("NAME").text = nidEntry.name

					if version is not None:
						newver = sorted(set([x.text for x in funvar.findall("VERSIONS/VERSION")] + [version]))
						versions = funvar.find("VERSIONS")
						for v in versions.findall("VERSION"):
							versions.remove(v)
						for v in newver:
							ET.SubElement(versions, "VERSION").text = v

					if len(nidEntry.source) > 0:
						if funvar.find("SOURCE") is not None:
							funvar.find("SOURCE").text = nidEntry.source
						else:
							ET.SubElement(funvar, "SOURCE").text = nidEntry.source

		for nid in entries:
			if entries[nid].prx == prxFile and entries[nid].libraryName not in libraryList:
				libs = prx.find("LIBRARIES")
				lib = ET.SubElement(libs, "LIBRARY")
				ET.SubElement(lib, "NAME").text = entries[nid].libraryName
				ET.SubElement(lib, "FLAGS").text = entries[nid].libraryFlags
				libraryList.append(entries[nid].libraryName)

		for library in prx.findall("LIBRARIES/LIBRARY"):
			libraryName = library.find("NAME").text
			nidList = []
			for (nidtype, funvar) in [('fun', x) for x in library.findall("FUNCTIONS/FUNCTION")] + [('var', x) for x in library.findall("VARIABLES/VARIABLE")]:
				funvarNID = funvar.find("NID").text.upper().removeprefix('0X')
				nidList.append((nidtype, funvarNID))

			for nid in entries:
				if entries[nid].libraryName == libraryName and entries[nid].prx == prxFile and (entries[nid].nidtype, nid) not in nidList:
					name = "FUNCTION" if entries[nid].nidtype == 'fun' else "VARIABLE"
					funvars = library.find(name + "S")
					if funvars is None:
						funvars = ET.SubElement(library, name + "S")
					funvar = ET.SubElement(funvars, name)
					ET.SubElement(funvar, "NID").text = '0x' + nid.upper()
					ET.SubElement(funvar, "NAME").text = entries[nid].name
					versions = ET.SubElement(funvar, "VERSIONS")
					ET.SubElement(versions, "VERSION").text = version

	functionsKnown = numTotalFunctions - numUnkFunctions + numUpdatedFunctions
	print("{:#04}/{:#04} unknown NIDs updated".format(numUpdatedFunctions, numUnkFunctions))
	print("{:#04}/{:#04} total NIDs known".format(functionsKnown, numTotalFunctions))

	if numTotalFunctions > 0:
		print("{:#03}%".format(int(functionsKnown / numTotalFunctions * 100)))
	else:
		print("100%")

	tree.write(xmlFile, encoding='utf-8', method="xml", xml_declaration=True, pretty_print=True)

def getNidForString(string):
	sha1Hash = hashlib.sha1(bytes(string, 'utf-8'))
	hashBytes = sha1Hash.digest()[0:4]
	nid = hashBytes[::-1].hex().upper()

	return nid

def loadPSPExportFile(exportFile):
	with open(exportFile) as f:
		lines = f.readlines()

	entries = []
	libraryName = " "
	libraryFlags = " "

	for line in lines:
		if line.startswith("PSP_EXPORT_START"):
			libraryEntry = line[line.find("(") + 1 : line.find(")")]
			library, unk, flags = libraryEntry.split(',')
			libraryName = library.strip()
			libraryFlags = flags.strip()

		elif line.startswith("PSP_EXPORT_FUNC_NID"):
			nidNamePair = line[line.find("(") + 1 : line.find(")")]
			functionName, functionNID = nidNamePair.split(',')
			functionName = functionName.strip()
			functionNID = functionNID.strip().upper().removeprefix('0X')
			entries.append(NIDEntry(nidtype="fun", nid=functionNID, name=functionName, prx=" ",
									prxName=" ", libraryName=libraryName, libraryFlags=libraryFlags,
									versions=[], source=""))

		elif line.startswith("PSP_EXPORT_FUNC_HASH"):
			functionName = line[line.find("(") + 1 : line.find(")")].strip()
			functionNID = getNidForString(functionName)
			entries.append(NIDEntry(nidtype="fun", nid=functionNID, name=functionName, prx=" ",
									prxName=" ", libraryName=libraryName, libraryFlags=libraryFlags,
									versions=[], source=""))

		elif line.startswith("PSP_EXPORT_END"):
			libraryName = " "
			libraryFlags = " "

	return entries


def loadFunctionFile(xmlFile):
	with open(xmlFile) as f:
		it = itertools.chain("<root>", f, "</root>")
		root = ET.fromstringlist(it)

	entries = []
	for function in root.findall("FUNC"):
		functionNID = function.find("NID").text.upper().removeprefix('0X')
		functionName =function.find("NAME").text
		entries.append(NIDEntry(nidtype="fun", nid=functionNID, name=functionName, prx=" ",
								prxName=" ", libraryName=" ", libraryFlags=" ", versions=[], source=""))

	return entries

def loadHLEFunctionFile(inputFile):
	with open(inputFile) as f:
		fileText = f.read()

	entries = []

	hleArrayStartRegex = re.compile(r'.*HLEFunction(.*)\[\]')
	hleArrayEntryRegex = re.compile(r'{(.*)}')

	hleArrayMatches = hleArrayStartRegex.finditer(fileText)
	for match in hleArrayMatches:
		libraryName = match.group(1).strip()
		arrayStart = match.start();
		arrayEnd = arrayStart + re.search('};', fileText[arrayStart:]).end()

		hleArray = fileText[arrayStart:arrayEnd]
		hleArrayEntryMatches = hleArrayEntryRegex.finditer(hleArray)
		for match in hleArrayEntryMatches:
			hleEntry = match.group(1).split(',')
			functionNID = hleEntry[0].upper().removeprefix('0X')
			functionName = hleEntry[2].strip()[1:-1]
			entries.append(NIDEntry(nidtype="fun", nid=functionNID, name=functionName, prx=" ",
								prxName=" ", libraryName=libraryName, libraryFlags=" ", versions=[], source=""))

	return entries

def exportNids(nidEntries, outFile):
	with open(outFile, "w") as f:
		for entry in nidEntries:
			f.write("0x" + entry.nid + '\n')

def exportUnknownNids(nidEntries, outFile):
	with open(outFile, "w") as f:
		for entry in nidEntries:
			functionNID = entry.nid
			functionName = entry.name
			libDocNidNameUnk = functionName.upper().endswith(functionNID)
			if libDocNidNameUnk:
				f.write("0x" + functionNID + '\n')

def exportFunctionNames(nidEntries, outFile):
	with open(outFile, "w") as f:
		for nidEntry in nidEntries:
			f.write(nidEntry.name + '\n')

def exportKnownFunctionNames(nidEntries, outFile):
	with open(outFile, "w") as f:
		for nidEntry in nidEntries:
			functionNID = nidEntry.nid
			functionName = nidEntry.name
			libDocNidNameUnk = functionName.upper().endswith(functionNID)
			if not libDocNidNameUnk:
				f.write(nidEntry.name + '\n')

def exportPSPLibdocCombined(nidEntries, outFile, firmwareVersion=None, includeAll=False):
	entries = sorted(nidEntries, key=lambda x: [x.prx, x.libraryName, x.versions[0], int(x.nid, 16)])
	if firmwareVersion is not None:
		entries = filter(lambda x : firmwareVersion in x.versions, entries)

	root = ET.Element("PSPLIBDOC")
	root.addprevious(ET.ProcessingInstruction('xml-stylesheet', 'type="text/xsl" href="psplibdocdisplay.xsl" '))

	prxfiles = ET.SubElement(root, "PRXFILES")

	lastPrxFile = ""
	lastLibrary = ""

	for entry in entries:
		if lastPrxFile != entry.prx:
			prxfile = ET.SubElement(prxfiles, "PRXFILE")

			prx = ET.SubElement(prxfile, "PRX")
			prx.text = entry.prx

			prxName = ET.SubElement(prxfile, "PRXNAME")
			prxName.text = entry.prxName

			libraries = ET.SubElement(prxfile, "LIBRARIES")

			lastPrxFile = entry.prx

		if lastLibrary != entry.libraryName:
			library = ET.SubElement(libraries, "LIBRARY")

			name = ET.SubElement(library, "NAME")
			name.text = entry.libraryName

			flags = ET.SubElement(library, "FLAGS")
			flags.text = entry.libraryFlags

			functions = ET.SubElement(library, "FUNCTIONS")

			lastLibrary = entry.libraryName

		function = ET.SubElement(functions, "FUNCTION")

		nid = ET.SubElement(function, "NID")
		nid.text = "0x" + entry.nid

		name = ET.SubElement(function, "NAME")
		name.text = entry.name

		# Do not export the "VERSIONS" and "SOURCE" fields in the combined libdoc, in order to save space
		if includeAll:
			if len(entry.source) > 0:
				ET.SubElement(function, "SOURCE").text = entry.source

			versions = ET.SubElement(function, "VERSIONS")
			for v in entry.versions:
				ET.SubElement(versions, "VERSION").text = v

	ET.ElementTree(root).write(outFile, encoding='utf-8', method="xml", xml_declaration=True, pretty_print=True)

def exportPSPLibdocModules(nidEntries, outFolder):
	os.makedirs(outFolder)

	prxDict = {}
	for entry in nidEntries:
		prxDict.setdefault(entry.prx, []).append(entry)

	for key in prxDict.keys():
		outfile = outFolder + "/" + key.split('.')[0] + ".xml"
		exportPSPLibdocCombined(prxDict[key], outfile)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	parser.add_argument('-l', '--libdoc',
						required=False,
						nargs='+',
						type=str,
						help='Load a PSP-Libdoc XML file.')

	parser.add_argument('-e', '--export',
						required=False,
						nargs='+',
						type=str,
						help='Load a PSP-Export file.')

	parser.add_argument('-f', '--func',
						required=False,
						nargs='+',
						type=str,
						help='Load function only XML file.')

	parser.add_argument('-p', '--ppsspp',
						required=False,
						nargs='+',
						type=str,
						help='Load ppsspp source file (HLEFunction arrays)')

	parser.add_argument('-u', '--updateLibdoc',
						required=False,
						type=str,
						help='Update specified PSP-Libdoc XML file with loaded NID names.')

	parser.add_argument('-n', '--exportNids',
						required=False,
						type=str,
						help='Export all loaded NIDs to the specified file.')

	parser.add_argument('-o', '--exportUnknownNids',
						required=False,
						type=str,
						help='Export all loaded NIDs with unknown function name to the specified file.')

	parser.add_argument('-d', '--exportFunctionNames',
						required=False,
						type=str,
						help='Export all loaded function names to the specified file.')

	parser.add_argument('-k', '--exportKnownFunctionNames',
						required=False,
						type=str,
						help='Export all known loaded function names to the specified file.')

	parser.add_argument('-c', '--writeLibdocCombined',
						required=False,
						type=str,
						help='Write combined PSP-Libdoc XML file for all loaded PRX modules to the specified file.')

	parser.add_argument('-s', '--writeLibdocSplit',
						required=False,
						type=str,
						help='Write PSP-Libdoc XML file for each loaded PRX module to the specified folder.')

	parser.add_argument('-v', '--firmwareVersion',
						required=False,
						type=str,
						help='Extract only the NIDs from a given firmware version')

	nidEntries = []
	args = parser.parse_args(sys.argv[1:])

	if(args.libdoc):
		for libdoc in args.libdoc:
			libdocEntries = loadPSPLibdoc(libdoc)
			nidEntries.extend(libdocEntries)

	if(args.export):
		for export in args.export:
			exportEntries = loadPSPExportFile(export)
			nidEntries.extend(exportEntries)

	if(args.func):
		for func in args.func:
			funcEntries = loadFunctionFile(func)
			nidEntries.extend(funcEntries)

	if(args.ppsspp):
		for ppsspp in args.ppsspp:
			ppssppEntries = loadHLEFunctionFile(ppsspp)
			nidEntries.extend(ppssppEntries)

	if(args.updateLibdoc):
		updatePSPLibdoc(nidEntries, args.updateLibdoc, args.firmwareVersion)

	if(args.exportNids):
		exportNids(nidEntries, args.exportNids)

	if(args.exportUnknownNids):
		exportUnknownNids(nidEntries, args.exportUnknownNids)

	if(args.exportFunctionNames):
		exportFunctionNames(nidEntries, args.exportFunctionNames)

	if(args.exportKnownFunctionNames):
		exportKnownFunctionNames(nidEntries, args.exportKnownFunctionNames)

	if(args.writeLibdocCombined):
		exportPSPLibdocCombined(nidEntries, args.writeLibdocCombined, args.firmwareVersion)

	if(args.writeLibdocSplit):
		exportPSPLibdocModules(nidEntries, args.writeLibdocSplit)






# AuditParser.py
#
# Ryan Kazanciyan, ryan.kazanciyan@mandiant.com
# Copyright 2012 Mandiant
#
# Mandiant licenses this file to you under the Apache License, Version
# 2.0 (the "License"); you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at:
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.
#
# Converts MIR / Redline / IOCFinder raw XML audit output to tab-separated 
# text suitable for importing into Excel and other tools.
#

import sys, datetime, time
import csv
import sys
import os
from datetime import datetime
from time import strptime
from optparse import OptionParser
from lxml import etree

### Global Variables ###

# Dictionary of XML elements to parse from each audit type
d = {}

d['FileItem'] = ['FileName', 'FullPath', 'FileAttributes', 'SizeInBytes', 'Md5sum', 'Username', 'Created', 'Modified', 'Accessed', 'Changed', 'FilenameCreated', 'FilenameModified', 'FilenameAccessed', 'FilenameChanged', 'SecurityID', 'INode', 'DevicePath', 'PEInfo','StreamList']
d['PrefetchItem'] = ['FullPath', 'Created', 'SizeInBytes', 'ApplicationFileName', 'LastRun', 'TimesExecuted', 'ApplicationFullPath']
d['UserItem'] = ['Username', 'SecurityID', 'SecurityType', 'fullname', 'description', 'homedirectory', 'scriptpath', 'grouplist', 'LastLogin', 'disabled', 'lockedout', 'passwordrequired', 'userpasswordage']
d['RegistryItem'] = ['Username','SecurityID','Path','ValueName','Type','Modified','Text','NumSubKeys','NumValues']
d['PortItem'] = ['pid', 'process', 'path', 'state', 'localIP', 'remoteIP', 'localPort', 'remotePort', 'protocol']
d['UrlHistoryItem'] = ['Profile', 'BrowserName', 'BrowserVersion', 'Username', 'URL', 'LastVisitDate', 'VisitType']
d['ProcessItem'] = ['pid', 'parentpid', 'path', 'name', 'arguments', 'Username', 'SecurityID', 'SecurityType', 'startTime']
d['EventLogItem'] = ['EID', 'log', 'index', 'type', 'genTime', 'writeTime', 'source', 'machine', 'user', 'message']
d['ServiceItem'] = ['name', 'descriptiveName', 'description', 'mode', 'startedAs', 'path', 'pathmd5sum', 'pathSignatureExists', 'pathSignatureVerified', 'pathSignatureDescription', 'pathCertificateSubject', 'pathCertificateIssuer', 'arguments', 'status', 'pid', 'type']
d['ModuleItem'] = ['ModuleAddress', 'ModuleInit', 'ModuleBase', 'ModuleSize', 'ModulePath', 'ModuleName']
d['DriverItem'] = ['DriverObjectAddress', 'ImageBase', 'ImageSize', 'DriverName', 'DriverInit', 'DriverStartIo', 'DriverUnload', 'Md5sum', 'SignatureExists', 'SignatureVerified', 'SignatureDescription', 'CertificateIssuer']
d['HiveItem'] = ['Name', 'Path']
d['HookItem'] = ['HookDescription', 'HookedFunction', 'HookedModule', 'HookingModule', 'HookingAddress', 'DigitalSignatureHooking', 'DigitalSignatureHooked']
d['VolumeItem'] = ['VolumeName', 'DevicePath', 'DriveLetter', 'Type', 'Name', 'SerialNumber', 'FileSystemFlags', 'FileSystemName', 'ActualAvailableAllocationUnits', 'TotalAllocationUnits', 'BytesPerSector', 'SectorsPerAllocationUnit', 'CreationTime', 'IsMounted']
d['ArpEntryItem'] = ['Interface', 'InterfaceType', 'PhysicalAddress', 'IPv4Address', 'IPv6Address', 'IsRouter', 'LastReachable', 'LastUnreachable', 'CacheType']
d['RouteEntryItem'] = ['Interface', 'Destination', 'Netmask', 'Gateway', 'RouteType', 'Protocol', 'RouteAge', 'Metric']
d['DnsEntryItem'] = ['Host', 'RecordName', 'RecordType', 'TimeToLive', 'Flags', 'DataLength', 'RecordData']
d['TaskItem'] = ['Name', 'VirtualPath', 'ExitCode', 'CreationDate', 'Comment', 'Creator', 'MaxRunTime', 'Flag', 'AccountName', 'AccountRunLevel', 'AccountLogonType', 'NextRunTime', 'Status', 'ActionList']
d['FileDownloadHistoryItem'] = ['Profile', 'BrowserName', 'BrowserVersion', 'username', 'DownloadType', 'FileName', 'SourceURL', 'TargetDirectory', 'LastAccessedDate', 'LastModifiedDate', 'BytesDownloaded', 'MaxBytes', 'CacheFlags', 'CacheHitCount', 'LastCheckedDate']
d['CookieHistoryItem'] = ['Profile', 'BrowserName', 'BrowserVersion', 'Username', 'FileName', 'FilePath', 'CookiePath', 'CookieName', 'CookieValue', 'CreationDate', 'ExpirationDate' 'LastAccessedDate', 'LastModifiedDate']
d['SystemInfoItem'] = ['machine', 'totalphysical', 'availphysical', 'uptime', 'OS', 'OSbitness', 'hostname', 'date', 'user', 'domain', 'processor', 'patchLevel', 'buildNumber', 'procType', 'productID', 'productName', 'regOrg', 'regOwner', 'installDate' , 'MAC', 'timezoneDST', 'timezoneStandard', 'networkArray']
d['PersistenceItem'] = ['PersistenceType', 'ServiceName', 'RegPath', 'RegText', 'RegOwner', 'RegModified', 'ServicePath', 'serviceDLL', 'arguments', 'FilePath', 'FileOwner', 'FileCreated', 'FileModified', 'FileAccessed', 'FileChanged', 'SignatureExists', 'SignatureVerified', 'SignatureDescription', 'CertificateSubject', 'CertificateIssuer', 'md5sum']
# TODO: Add parsing for Disk and System Restore Point audits


# Global for timeline data
timelineData = []

### Class Definitions ###

# Generic timeline object definition
class timelineEntry:

		# Initialize with timestamp, type of audit item, item contents
		def __init__(self, timeStamp, entryType, entryItem):
			self.timeObject= datetime.strptime(timeStamp, "%Y-%m-%dT%H:%M:%SZ")
			self.entryType = entryType
			self.entryItem = entryItem
			self.digSigInfo = ""
			self.md5 = ""
			self.user = ""
			self.timeDesc = ""
	
		# Add a hash to timeline object
		def addHash(self, md5):
			self.md5 = md5

		# Add a user to timeline object
		def addUser(self, user):
			self.user = user

		# Add digital signature data to timeline object
		def addDigSigInfo(self, digSigInfo):
			self.digSigInfo = digSigInfo

		# Add description of the sort timestamp
		def addTimeDesc(self, timeDesc):
			self.timeDesc = timeDesc
		
		# Return a list variable containing timeline object
		def getTimelineRow(self):
			rowData = [self.timeObject.isoformat(), self.timeDesc, self.entryType, self.entryItem, self.md5, self.user, self.digSigInfo]
			return rowData


### Methods ###

# Helper function to print column headers for parsed audits
def printHeaders(auditType):
	topRow = []
	for columnLabel in d["".join(auditType)]:
		topRow.append(columnLabel)
	return topRow

# Parse MIR agent XML input files into tab-delimited output
def parseXML(inFile,outFile,doTimeline,startTime,endTime):

	outHandle = open(outFile,'wb')

	writer = csv.writer(outHandle, dialect=csv.excel_tab)

	rowCount = -1

	currentAudit = ""
	
	# Iterate through XML
	for event, elem in etree.iterparse(inFile):

		# Only proceed if element is in our parsing dictionary
		if elem.tag in d: 
			row = []
			currentAudit = elem.tag
			
			# Write header row
			if rowCount < 0:
				writer.writerow(printHeaders(elem.tag))
				rowCount += 1
				
			# Iterate through each sub-element and build an output row		
			for i in d[elem.tag]:
				if(elem.find(i) is not None): 
				
					# Special case for nested DigSig data within FileItem audit results
					if((elem.find(i).tag == "PEInfo") and (elem.tag == "FileItem")): 
						digSigList = []
						for j in elem.find(i).iter():
							if(j.tag == "DigitalSignature"):
								subs = list(j)
								for k in list(j):
									digSigList.append(k.tag + " : " + (k.text or "[]"))
						separator = " | "
						row.append(separator.join(digSigList))
					
					# Special case for nested Stream data within FileItem audit results
					elif((elem.find(i).tag == "StreamList") and (elem.tag == "FileItem")): 
						streamList = []
						for j in elem.find(i).iter():
							if(j.tag == "Stream"):
								subs = list(j)
								for k in list(j):
									streamList.append(k.tag + " : " + (k.text or "[]"))
						separator = " | "
						row.append(separator.join(streamList))
						
					# Special case for nested network config data within System audit results
					elif((elem.find(i).tag == "networkArray") and (elem.tag == "SystemInfoItem")): 
						networkAdapters = []
						for j in elem.find(i).iter():
							subs = list(j)
							for k in list(j):
								networkAdapters.append(k.tag + " : " + (k.text or "[]"))
						separator = " | "
						row.append(separator.join(networkAdapters))
					
					# Special case for nested grouplist within UserItem audit results
					elif((elem.find(i).tag == "grouplist") and (elem.tag == "UserItem")): 
						groupList = []
						for j in elem.find(i).iter(tag="groupname"):
							groupList.append(j.text)
						separator = " | "
						row.append(separator.join(groupList))
						
					# Special case for nested RecordData within DNS Cache audit results
					elif((elem.find(i).tag == "RecordData") and (elem.tag == "DnsEntryItem")): 
						recordList = []
						for j in elem.find(i).iter():
							if(j.tag != "RecordData"): recordList.append(j.tag + " : " + (j.text or ""))
						separator = " | "
						row.append(separator.join(recordList))
				
					# Special case for nested DigSig data within HookItem audit results
					elif((elem.find(i).tag == "DigitalSignatureHooking" or elem.find(i).tag =="DigitalSignatureHooked") and (elem.tag == "HookItem")):
						digSigList = []
						for j in elem.find(i).iter():
							if(j.tag != "DigitalSignatureHooking" and j.tag != "DigitalSignatureHooked"): digSigList.append(j.tag + " : " + (j.text or ""))
						separator = " | "
						row.append(separator.join(digSigList))
					
					# Special case for nested ActionList within Task audit results
					elif((elem.find(i).tag == "ActionList") and (elem.tag == "TaskItem")): 
						actionList = []
						for j in elem.find(i).iter():
							if(j.tag != "Action" and j.tag != "ActionList"): actionList.append(j.tag + " : " + (j.text or ""))
						separator = " | "
						row.append(separator.join(actionList))

					elif((elem.find(i).tag == "message") and (elem.tag == "EventLogItem")): 
						
						if elem.find(i).text is not None:
							strippedMessage = elem.find(i).text.replace('\r\n', '     ')
							strippedMessage = strippedMessage.replace('\t',' ')
							strippedMessage = strippedMessage.replace('\n', '     ')
							row.append(strippedMessage.encode("utf-8"))
						
					# For all other non-nested elements
					else: 
						rowData = elem.find(i).text or ""
						row.append(rowData.encode("utf-8"))

				# Write an empty string for empty elements 
				else:
					row.append("")

			# Commit row to tab-delim file
			writer.writerow(row)
			
			# Faster to just call buildTimeline on all file items rather than first test 8 time stamps for time range
			if((currentAudit == "FileItem") and doTimeline):
				buildTimeline(elem)
			
			# Only add registry item to timeline if Last Modified within time range
			elif((currentAudit == "RegistryItem") and doTimeline and (startTime <= elem.find("Modified").text) and (endTime >= elem.find("Modified").text)):
				buildTimeline(elem)

			# Only add event log item to timeline if Event Generated within time range
			elif((currentAudit == "EventLogItem") and doTimeline and (startTime <= elem.find("genTime").text) and (endTime >= elem.find("genTime").text)):
				buildTimeline(elem)
				
			rowCount += 1

			# Free up memory by clearing no-longer needed XML element
			elem.clear()
	outHandle.close()

# Helper function to parse persistence audits, which require a different approach due to schema
def parsePersistence(inFile,outFile):
		
	outHandle = open(outFile,'wb')

	writer = csv.writer(outHandle, dialect=csv.excel_tab)

	# Write header row
	writer.writerow(printHeaders(['PersistenceItem']))

	# Iterate through each top-level XML element
	tree = etree.parse(inFile)

	for subItem in tree.iter("PersistenceItem"):
		row = []
		for columnName in d['PersistenceItem']:
			if(subItem.find(columnName) is not None): 
				rowData = subItem.find(columnName).text or ""
				row.append(rowData.encode("utf-8"))
			else: row.append("")

		# Hack to reduce and simplify schema for output file.  MD5 and digital signature information
		# for Service ImagePaths and Service DLLs is "collapsed" into the existing columns for other
		# Persistence items.  Hooray for nested XML.

		if((row[0]=="ServiceDll") and (subItem.find("serviceDLLSignatureExists") is not None)):
			row[15] = subItem.find("serviceDLLSignatureExists").text
		
		if((row[0]=="ServiceDll") and (subItem.find("serviceDLLSignatureExists") is not None)):
			row[16] = subItem.find("serviceDLLSignatureVerified").text

		if((row[0]=="ServiceDll") and (subItem.find("serviceDLLSignatureExists") is not None)):
			row[17] = subItem.find("serviceDLLSignatureDescription").text

		if((row[0]=="ServiceDll") and (subItem.find("serviceDLLSignatureExists") is not None)):
			row[18] = subItem.find("serviceDLLCertificateSubject").text

		if((row[0]=="ServiceDll") and (subItem.find("serviceDLLSignatureExists") is not None)):
			row[19] = subItem.find("serviceDLLCertificateIssuer").text
		
		if((row[0]=="ServiceDll") and (subItem.find("serviceDLLmd5sum") is not None)): 
			row[20] = subItem.find("serviceDLLmd5sum").text

		if((row[0]=="Service") and (subItem.find("pathSignatureExists") is not None)):
			row[15] = subItem.find("pathSignatureExists").text
		
		if((row[0]=="Service") and (subItem.find("pathSignatureVerified") is not None)):
			row[16] = subItem.find("pathSignatureVerified").text

		if((row[0]=="Service") and (subItem.find("pathSignatureDescription") is not None)):
			row[17] = subItem.find("pathSignatureDescription").text

		if((row[0]=="Service") and (subItem.find("pathCertificateSubject") is not None)):
			row[18] =  subItem.find("pathCertificateSubject").text

		if((row[0]=="Service") and (subItem.find("pathCertificateIssuer") is not None)):
			row[19] = subItem.find("pathCertificateIssuer").text

		if((row[0]=="Service") and (row[1].find("ServiceDll") < 0) and (subItem.find("pathmd5sum") is not None)): 
			row[20] = subItem.find("pathmd5sum").text
		
		# Fix errant unicode after substituting
		for i, rowValue in enumerate(row):
			if rowValue is not None:
				row[i] = rowValue.encode("utf-8")
		
		writer.writerow(row)
	outHandle.close()

# Helper function to parse prefetch audits, which require a different approach due to schema
def parsePrefetch(inFile,outFile):
	
	outHandle = open(outFile,'wb')

	writer = csv.writer(outHandle, dialect=csv.excel_tab)

	# Write header row
	writer.writerow(printHeaders(['PrefetchItem']))

	# Iterate through each top-level XML element
	tree = etree.parse(inFile)

	for subItem in tree.iter("PrefetchItem"):
		row = []
		for columnName in d['PrefetchItem']:
			if(subItem.find(columnName) is not None): 
				rowData = subItem.find(columnName).text or ""
				row.append(rowData.encode("utf-8"))
			else: row.append("")
					
		writer.writerow(row)
	outHandle.close()
	
# Build a timeline object from a parsed element
def buildTimeline(elem):
	
	# Case 1: File item timeline object
	if(elem.tag == "FileItem"):
		
		timeFields = ['Created', 'Modified', 'Accessed', 'Changed', 'FilenameCreated', 'FilenameModified', 'FilenameAccessed', 'FilenameChanged']
		for field in timeFields:
			if(elem.find(field) is not None): 
				timelineData.append(timelineEntry(elem.find(field).text, elem.tag, elem.find("FullPath").text))
				timelineData[-1].addTimeDesc(field)

				if elem.find("Md5sum") is not None: 
					timelineData[-1].addHash(elem.find("Md5sum").text)
		
				if elem.find("Username") is not None:
					timelineData[-1].addUser(elem.find("Username").text)

	# Case 2: Registry item timeline object
	elif(elem.tag == "RegistryItem"):
		
		timelineData.append(timelineEntry(elem.find("Modified").text, elem.tag, elem.find("Path").text))
		timelineData[-1].addTimeDesc("Modified")
		if elem.find("Username") is not None:
			timelineData[-1].addUser(elem.find("Username").text)
	
	# Case 3: Event log item timeline object
	elif(elem.tag == "EventLogItem"):
		if elem.find("message") is not None:
			timelineData.append(timelineEntry(elem.find("genTime").text, elem.tag, elem.find("message").text))
		else: timelineData.append(timelineEntry(elem.find("genTime").text, elem.tag, ""))
		
		timelineData[-1].addTimeDesc("genTime")
		if elem.find("user") is not None:
			timelineData[-1].addUser(elem.find("user").text)

			
# Prints timeline to tab delimited text
def printTimeline(timelineFile,startTime,endTime):
	
	timelineFileHandle = open(timelineFile,'wb')
	
	# Sort timeline data on primary date object
	timelineData.sort(key=lambda r: r.timeObject)
	
	# Output header row
	writer = csv.writer(timelineFileHandle, dialect=csv.excel_tab)
	headerRow = ["Timestamp", "Time Desc", "Entry Type", "Entry", "MD5", "User", "Digital Signature"]
	writer.writerow(headerRow)
	
	# Print each timeline object that is within start and end time ranges
	for i in timelineData:
		if (i.timeObject >= datetime.strptime(startTime, "%Y-%m-%dT%H:%M:%SZ")) and (i.timeObject <= datetime.strptime(endTime, "%Y-%m-%dT%H:%M:%SZ")):
			writer.writerow(i.getTimelineRow())
			
	timelineFileHandle.close()
	
def main():
	
	# Handle arguments
	parser = OptionParser()
	parser.add_option("-i", "--input", help="XML input directory (req). NO TRAILING SLASHES", action="store", type="string", dest="inPath")
	parser.add_option("-o", "--output", help="Output directory (req). NO TRAILING SLASHES", action="store", type="string", dest="outPath")
	parser.add_option("-t", "--timeline", help="Build timeline, requires --starttime and --endtime", action="store_true", dest="doTimeline")
	parser.add_option("--starttime", help="Start time, format yyyy-mm-ddThh:mm:ssZ", action="store", type="string", dest="startTime")
	parser.add_option("--endtime", help="End time, format yyyy-mm-ddThh:mm:ssZ", action="store", type="string", dest="endTime")
	(options, args) = parser.parse_args()

	if(len(sys.argv) < 3) or  (not options.inPath) or (not options.outPath): 
		parser.print_help()
		sys.exit(-1)
	
	inPath = options.inPath
	outPath = options.outPath
	doTimeline = options.doTimeline
	
	# Ensure user supplies time ranges for timeline option
	if options.doTimeline and (not options.startTime or not options.endTime):
		print "Timeline option requires --starttime and --endtime\n"
		parser.print_help()
		sys.exit(-1)

	# Normalize input paths
	if not inPath.endswith(os.path.sep):
		inPath += os.path.sep
	
	if not outPath.endswith(os.path.sep):
		outPath += os.path.sep

	# Iterate through and parse each input file
	for filename in os.listdir(inPath):
		
		#Simple match on filename to avoid having to open and parse initial XML to determine doctype
		if (filename.find("issues") is -1) and (filename.find(".xml") is not -1) and (filename.find("BatchResults") is -1):

			inFile = inPath + filename	
			outFile = outPath + filename+".txt"
			
			# Parse XML into delimited text
			print "Parsing input file: " + inFile
	
			if (filename.find("persistence") > 0): parsePersistence(inFile, outFile)
			elif (filename.find("prefetch") > 0): parsePrefetch(inFile, outFile)
			else: parseXML(inFile,outFile,doTimeline,options.startTime,options.endTime)
	
		#else: print "No more input XML files to parse!"
		
	# Output timeline (if option enabled) once we're done processing
	if(doTimeline): 
		print "Outputting timeline: " + outPath + "timeline.txt"
		printTimeline(outPath+"timeline.txt", options.startTime, options.endTime)

if __name__ == "__main__":
	main()
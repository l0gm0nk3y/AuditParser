#Modified 
Written by l0gm0nk3y

Tweaked this parser to handle FireEye HX collection (*.mans) files.

The only thing that changes is the type of input.  This version expects
a .mans file instead of a directory containing Redline audit results.

See Step 2 below.

# AuditParser.py
Written by Ryan Kazanciyan at Mandiant

Audit Parser was designed to convert the raw XML output generated by
by Mandiant Intelligent Response, Redline, or IOC Finder into tab-delimited
text files.  These files contain extensive evidence from disk, registry, event
logs, memory, and other parsed Windows artifacts that can be used for
live response analysis.  The tab-delimited data can easily be reviewed in 
spreadsheet applications like Microsoft Excel.

Audit Parser is written in Python and requires the "lxml" library 
(http://lxml.de/).  An EXE package converted via Py2Exe is also provided
with this distribution.

# Usage

## Step 1 - Collect and Analyze Evidence!

Use IOC Finder or Redline to collect evidence from your target system.
Redline version 1.6 or later is recommended.  

* IOC Finder: http://www.mandiant.com/resources/download/ioc-finder/
* Redline: http://www.mandiant.com/resources/download/redline

If using Redline, select "Create a Comprehensive Collector" in the start-up 
screen.  This will build a collection script that gathers sufficient data for 
live response analysis.  It will also let you further edit the script to enable,
disable, or change settings for each audit modules as desired.

## Step 2 - Parse with Audit Parser

Run Audit Parser against the directory containing your IOC Finder or
Redline audit results:

AuditParser.py -m *.mans -o output_path

* Supplied paths must not have trailing slashes
* input_path should contain the XML output files from IOC Finder or Redline
* output_path is where Audit Parser will save the converted results.  This
path should already exist.

### Timeline Option
AuditParser.py -i input_path -o output_path --timeline --starttime yyyy-mm-ddThh:mm:ssZ --endtime yyyy-mm-ddThh:mm:ssZ

The --timeline switch is optional; if enabled, --starttime and --endtime must
be provided.  This will produce a file named "timeline.txt" in the output
directory containing a sorted timeline of File, Event Log, Registry, Process,
and Prefetch items that fall within the supplied time range.  Other audit 
types are not yet supported.

An example of a valid date format for the --starttime and --endtime options:
2012-01-01T00:00:00Z

## Step 3 - Review the Data

Once Audit Parser has completed, your specified output directory will contain
tab-delimited text files - each named identically to its corresponding input file.
You can easily view, sort, and filter the columns and rows within these files
files using a spreadsheet application like Excel, CSV file-viewers like "CSVed"
or "CSVFileView", import them into a database, etc.

The following list summarizes the types of audit results that a Redline 
comprehensive collector will acquire, and its output file naming conventions.  
Since Audit Parser retains the original input filename, this can help you
quickly identify what's-what when looking at a directory full of processed
results.

# Redline Output Filename Prefix : Corresponding Evidence
* mir.cookiehistory : Web Browser Cookie History
* mir.filedownloadhistory : Web Browser File Download History
* mir.formhistory : Web Browser Form History
* mir.urlhistory : Web Browser URL History
* mir.w32apifiles : File Enumeration (API)
* mir.w32disks : Disk Listing
* mir.w32drivers-modulelist : Driver Listing
* mir.w32drivers-signature : Driver Listing
* mir.w32eventlogs : Event Logs
* mir.w32hivelist	: Registry Hive Listing
* mir.w32kernel-hookdetection : Hook Detection
* mir.w32network-arp : Network ARP Tables
* mir.w32network-dns : Network DNS Cache
* mir.w32network-route : Network Routing Tables
* mir.w32ports : Network Ports / Netstat Data
* mir.w32prefetch : Prefetch Analysis
* mir.w32processes-memory : Process Enumeration (Memory)
* mir.w32rawfiles : File Enumeration (Raw)
* mir.w32registryapi : Registry Enumeration (API)
* mir.w32registryraw : Registry Enumeration (Raw)
* mir.w32scripting-persistence : File and Registry Persistence
* mir.w32services : Windows Services
* mir.w32system : System Information
* mir.w32systemrestore : System Restore Points
* mir.w32tasks : Task Listing
* mir.w32useraccounts : User Accounts
* mir.w32volumes : Volume Listing
* mir.stateagentinspector : HX State Agent Inspector 

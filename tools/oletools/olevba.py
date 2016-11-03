#!/usr/bin/env python
"""
olevba.py

olevba is a script to parse OLE and OpenXML files such as MS Office documents
(e.g. Word, Excel), to extract VBA Macro code in clear text, deobfuscate
and analyze malicious macros.

Supported formats:
- Word 97-2003 (.doc, .dot), Word 2007+ (.docm, .dotm)
- Excel 97-2003 (.xls), Excel 2007+ (.xlsm, .xlsb)
- PowerPoint 2007+ (.pptm, .ppsm)
- Word 2003 XML (.xml)
- Word/Excel Single File Web Page / MHTML (.mht)

Author: Philippe Lagadec - http://www.decalage.info
License: BSD, see source code or documentation

olevba is part of the python-oletools package:
http://www.decalage.info/python/oletools

olevba is based on source code from officeparser by John William Davison
https://github.com/unixfreak0037/officeparser
"""

# === LICENSE ==================================================================

# olevba is copyright (c) 2014-2016 Philippe Lagadec (http://www.decalage.info)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# olevba contains modified source code from the officeparser project, published
# under the following MIT License (MIT):
#
# officeparser is copyright (c) 2014 John William Davison
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#------------------------------------------------------------------------------
# CHANGELOG:
# 2014-08-05 v0.01 PL: - first version based on officeparser code
# 2014-08-14 v0.02 PL: - fixed bugs in code, added license from officeparser
# 2014-08-15       PL: - fixed incorrect value check in PROJECTHELPFILEPATH Record
# 2014-08-15 v0.03 PL: - refactored extract_macros to support OpenXML formats
#                        and to find the VBA project root anywhere in the file
# 2014-11-29 v0.04 PL: - use olefile instead of OleFileIO_PL
# 2014-12-05 v0.05 PL: - refactored most functions into a class, new API
#                      - added detect_vba_macros
# 2014-12-10 v0.06 PL: - hide first lines with VB attributes
#                      - detect auto-executable macros
#                      - ignore empty macros
# 2014-12-14 v0.07 PL: - detect_autoexec() is now case-insensitive
# 2014-12-15 v0.08 PL: - improved display for empty macros
#                      - added pattern extraction
# 2014-12-25 v0.09 PL: - added suspicious keywords detection
# 2014-12-27 v0.10 PL: - added OptionParser, main and process_file
#                      - uses xglob to scan several files with wildcards
#                      - option -r to recurse subdirectories
#                      - option -z to scan files in password-protected zips
# 2015-01-02 v0.11 PL: - improved filter_vba to detect colons
# 2015-01-03 v0.12 PL: - fixed detect_patterns to detect all patterns
#                      - process_file: improved display, shows container file
#                      - improved list of executable file extensions
# 2015-01-04 v0.13 PL: - added several suspicious keywords, improved display
# 2015-01-08 v0.14 PL: - added hex strings detection and decoding
#                      - fixed issue #2, decoding VBA stream names using
#                        specified codepage and unicode stream names
# 2015-01-11 v0.15 PL: - added new triage mode, options -t and -d
# 2015-01-16 v0.16 PL: - fix for issue #3 (exception when module name="text")
#                      - added several suspicious keywords
#                      - added option -i to analyze VBA source code directly
# 2015-01-17 v0.17 PL: - removed .com from the list of executable extensions
#                      - added scan_vba to run all detection algorithms
#                      - decoded hex strings are now also scanned + reversed
# 2015-01-23 v0.18 PL: - fixed issue #3, case-insensitive search in code_modules
# 2015-01-24 v0.19 PL: - improved the detection of IOCs obfuscated with hex
#                        strings and StrReverse
# 2015-01-26 v0.20 PL: - added option --hex to show all hex strings decoded
# 2015-01-29 v0.21 PL: - added Dridex obfuscation decoding
#                      - improved display, shows obfuscation name
# 2015-02-01 v0.22 PL: - fixed issue #4: regex for URL, e-mail and exe filename
#                      - added Base64 obfuscation decoding (contribution from
#                        @JamesHabben)
# 2015-02-03 v0.23 PL: - triage now uses VBA_Scanner results, shows Base64 and
#                        Dridex strings
#                      - exception handling in detect_base64_strings
# 2015-02-07 v0.24 PL: - renamed option --hex to --decode, fixed display
#                      - display exceptions with stack trace
#                      - added several suspicious keywords
#                      - improved Base64 detection and decoding
#                      - fixed triage mode not to scan attrib lines
# 2015-03-04 v0.25 PL: - added support for Word 2003 XML
# 2015-03-22 v0.26 PL: - added suspicious keywords for sandboxing and
#                        virtualisation detection
# 2015-05-06 v0.27 PL: - added support for MHTML files with VBA macros
#                        (issue #10 reported by Greg from SpamStopsHere)
# 2015-05-24 v0.28 PL: - improved support for MHTML files with modified header
#                        (issue #11 reported by Thomas Chopitea)
# 2015-05-26 v0.29 PL: - improved MSO files parsing, taking into account
#                        various data offsets (issue #12)
#                      - improved detection of MSO files, avoiding incorrect
#                        parsing errors (issue #7)
# 2015-05-29 v0.30 PL: - added suspicious keywords suggested by @ozhermit,
#                        Davy Douhine (issue #9), issue #13
# 2015-06-16 v0.31 PL: - added generic VBA expression deobfuscation (chr,asc,etc)
# 2015-06-19       PL: - added options -a, -c, --each, --attr
# 2015-06-21 v0.32 PL: - always display decoded strings which are printable
#                      - fix VBA_Scanner.scan to return raw strings, not repr()
# 2015-07-09 v0.40 PL: - removed usage of sys.stderr which causes issues
# 2015-07-12       PL: - added Hex function decoding to VBA Parser
# 2015-07-13       PL: - added Base64 function decoding to VBA Parser
# 2015-09-06       PL: - improved VBA_Parser, refactored the main functions
# 2015-09-13       PL: - moved main functions to a class VBA_Parser_CLI
#                      - fixed issue when analysis was done twice
# 2015-09-15       PL: - remove duplicate IOCs from results
# 2015-09-16       PL: - join long VBA lines ending with underscore before scan
#                      - disabled unused option --each
# 2015-09-22 v0.41 PL: - added new option --reveal
#                      - added suspicious strings for PowerShell.exe options
# 2015-10-09 v0.42 PL: - VBA_Parser: split each format into a separate method
# 2015-10-10       PL: - added support for text files with VBA source code
# 2015-11-17       PL: - fixed bug with --decode option
# 2015-12-16       PL: - fixed bug in main (no options input anymore)
#                      - improved logging, added -l option
# 2016-01-31       PL: - fixed issue #31 in VBA_Parser.open_mht
#                      - fixed issue #32 by monkeypatching email.feedparser
# 2016-02-07       PL: - KeyboardInterrupt is now raised properly
# 2016-02-20 v0.43 PL: - fixed issue #34 in the VBA parser and vba_chr
# 2016-02-29       PL: - added Workbook_Activate to suspicious keywords
# 2016-03-08 v0.44 PL: - added VBA Form strings extraction and analysis
# 2016-03-04 v0.45 CH: - added JSON output (by Christian Herdtweck)
# 2016-03-16       CH: - added option --no-deobfuscate (temporary)
# 2016-04-19 v0.46 PL: - new option --deobf instead of --no-deobfuscate
#                      - updated suspicious keywords

__version__ = '0.46'

#------------------------------------------------------------------------------
# TODO:
# + setup logging (common with other oletools)
# + add xor bruteforcing like bbharvest
# + options -a and -c should imply -d

# TODO later:
# + performance improvement: instead of searching each keyword separately,
#   first split vba code into a list of words (per line), then check each
#   word against a dict. (or put vba words into a set/dict?)
# + for regex, maybe combine them into a single re with named groups?
# + add Yara support, include sample rules? plugins like balbuzard?
# + add balbuzard support
# + output to file (replace print by file.write, sys.stdout by default)
# + look for VBA in embedded documents (e.g. Excel in Word)
# + support SRP streams (see Lenny's article + links and sample)
# - python 3.x support
# - add support for PowerPoint macros (see libclamav, libgsf), use oledump heuristic?
# - check VBA macros in Visio, Access, Project, etc
# - extract_macros: convert to a class, split long function into smaller methods
# - extract_macros: read bytes from stream file objects instead of strings
# - extract_macros: use combined struct.unpack instead of many calls
# - all except clauses should target specific exceptions

#------------------------------------------------------------------------------
# REFERENCES:
# - [MS-OVBA]: Microsoft Office VBA File Format Structure
#   http://msdn.microsoft.com/en-us/library/office/cc313094%28v=office.12%29.aspx
# - officeparser: https://github.com/unixfreak0037/officeparser


#--- IMPORTS ------------------------------------------------------------------

import sys, logging
import struct
import cStringIO
import math
import zipfile
import re
import optparse
import os.path
import binascii
import base64
import traceback
import zlib
import email  # for MHTML parsing
import string # for printable
import json   # for json output mode (argument --json)

# import lxml or ElementTree for XML parsing:
try:
    # lxml: best performance for XML processing
    import lxml.etree as ET
except ImportError:
    try:
        # Python 2.5+: batteries included
        import xml.etree.cElementTree as ET
    except ImportError:
        try:
            # Python <2.5: standalone ElementTree install
            import elementtree.cElementTree as ET
        except ImportError:
            raise ImportError, "lxml or ElementTree are not installed, " \
                               + "see http://codespeak.net/lxml " \
                               + "or http://effbot.org/zone/element-index.htm"

import thirdparty.olefile as olefile
from thirdparty.prettytable import prettytable
from thirdparty.xglob import xglob
from thirdparty.pyparsing.pyparsing import *

# monkeypatch email to fix issue #32:
# allow header lines without ":"
import email.feedparser
email.feedparser.headerRE = re.compile(r'^(From |[\041-\071\073-\176]{1,}:?|[\t ])')


# === LOGGING =================================================================

class NullHandler(logging.Handler):
    """
    Log Handler without output, to avoid printing messages if logging is not
    configured by the main application.
    Python 2.7 has logging.NullHandler, but this is necessary for 2.6:
    see https://docs.python.org/2.6/library/logging.html#configuring-logging-for-a-library
    """
    def emit(self, record):
        pass

def get_logger(name, level=logging.CRITICAL+1):
    """
    Create a suitable logger object for this module.
    The goal is not to change settings of the root logger, to avoid getting
    other modules' logs on the screen.
    If a logger exists with same name, reuse it. (Else it would have duplicate
    handlers and messages would be doubled.)
    The level is set to CRITICAL+1 by default, to avoid any logging.
    """
    # First, test if there is already a logger with the same name, else it
    # will generate duplicate messages (due to duplicate handlers):
    if name in logging.Logger.manager.loggerDict:
        #NOTE: another less intrusive but more "hackish" solution would be to
        # use getLogger then test if its effective level is not default.
        logger = logging.getLogger(name)
        # make sure level is OK:
        logger.setLevel(level)
        return logger
    # get a new logger:
    logger = logging.getLogger(name)
    # only add a NullHandler for this logger, it is up to the application
    # to configure its own logging:
    logger.addHandler(NullHandler())
    logger.setLevel(level)
    return logger

# a global logger object used for debugging:
log = get_logger('olevba')


#--- CONSTANTS ----------------------------------------------------------------

# URL and message to report issues:
URL_OLEVBA_ISSUES = 'https://bitbucket.org/decalage/oletools/issues'
MSG_OLEVBA_ISSUES = 'Please report this issue on %s' % URL_OLEVBA_ISSUES

# Container types:
TYPE_OLE = 'OLE'
TYPE_OpenXML = 'OpenXML'
TYPE_Word2003_XML = 'Word2003_XML'
TYPE_MHTML = 'MHTML'
TYPE_TEXT = 'Text'

# short tag to display file types in triage mode:
TYPE2TAG = {
    TYPE_OLE: 'OLE:',
    TYPE_OpenXML: 'OpX:',
    TYPE_Word2003_XML: 'XML:',
    TYPE_MHTML: 'MHT:',
    TYPE_TEXT: 'TXT:',
}


# MSO files ActiveMime header magic
MSO_ACTIVEMIME_HEADER = 'ActiveMime'

MODULE_EXTENSION = "bas"
CLASS_EXTENSION = "cls"
FORM_EXTENSION = "frm"

# Namespaces and tags for Word2003 XML parsing:
NS_W = '{http://schemas.microsoft.com/office/word/2003/wordml}'
# the tag <w:binData w:name="editdata.mso"> contains the VBA macro code:
TAG_BINDATA = NS_W + 'binData'
ATTR_NAME = NS_W + 'name'

# Keywords to detect auto-executable macros
AUTOEXEC_KEYWORDS = {
    # MS Word:
    'Runs when the Word document is opened':
        ('AutoExec', 'AutoOpen', 'Document_Open', 'DocumentOpen'),
    'Runs when the Word document is closed':
        ('AutoExit', 'AutoClose', 'Document_Close', 'DocumentBeforeClose'),
    'Runs when the Word document is modified':
        ('DocumentChange',),
    'Runs when a new Word document is created':
        ('AutoNew', 'Document_New', 'NewDocument'),

    # MS Excel:
    'Runs when the Excel Workbook is opened':
        ('Auto_Open', 'Workbook_Open', 'Workbook_Activate'),
    'Runs when the Excel Workbook is closed':
        ('Auto_Close', 'Workbook_Close'),

    #TODO: full list in MS specs??
}

# Suspicious Keywords that may be used by malware
# See VBA language reference: http://msdn.microsoft.com/en-us/library/office/jj692818%28v=office.15%29.aspx
SUSPICIOUS_KEYWORDS = {
    #TODO: use regex to support variable whitespaces
    'May read system environment variables':
        ('Environ',),
    'May open a file':
        ('Open',),
    'May write to a file (if combined with Open)':
    #TODO: regex to find Open+Write on same line
        ('Write', 'Put', 'Output', 'Print #'),
    'May read or write a binary file (if combined with Open)':
    #TODO: regex to find Open+Binary on same line
        ('Binary',),
    'May copy a file':
        ('FileCopy', 'CopyFile'),
    #FileCopy: http://msdn.microsoft.com/en-us/library/office/gg264390%28v=office.15%29.aspx
    #CopyFile: http://msdn.microsoft.com/en-us/library/office/gg264089%28v=office.15%29.aspx
    'May delete a file':
        ('Kill',),
    'May create a text file':
        ('CreateTextFile', 'ADODB.Stream', 'WriteText', 'SaveToFile'),
    #CreateTextFile: http://msdn.microsoft.com/en-us/library/office/gg264617%28v=office.15%29.aspx
    #ADODB.Stream sample: http://pastebin.com/Z4TMyuq6
    'May run an executable file or a system command':
        ('Shell', 'vbNormal', 'vbNormalFocus', 'vbHide', 'vbMinimizedFocus', 'vbMaximizedFocus', 'vbNormalNoFocus',
         'vbMinimizedNoFocus', 'WScript.Shell', 'Run'),
    #Shell: http://msdn.microsoft.com/en-us/library/office/gg278437%28v=office.15%29.aspx
    #WScript.Shell+Run sample: http://pastebin.com/Z4TMyuq6
    'May run PowerShell commands':
    #sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
    #also: https://bitbucket.org/decalage/oletools/issues/14/olevba-library-update-ioc
    # ref: https://blog.netspi.com/15-ways-to-bypass-the-powershell-execution-policy/
    # TODO: add support for keywords starting with a non-alpha character, such as "-noexit"
    # TODO: '-command', '-EncodedCommand', '-scriptblock'
        ('PowerShell', 'noexit', 'ExecutionPolicy', 'noprofile', 'command', 'EncodedCommand',
         'invoke-command', 'scriptblock', 'Invoke-Expression', 'AuthorizationManager'),
    'May run an executable file or a system command using PowerShell':
        ('Start-Process',),
    'May hide the application':
        ('Application.Visible', 'ShowWindow', 'SW_HIDE'),
    'May create a directory':
        ('MkDir',),
    'May save the current workbook':
        ('ActiveWorkbook.SaveAs',),
    'May change which directory contains files to open at startup':
    #TODO: confirm the actual effect
        ('Application.AltStartupPath',),
    'May create an OLE object':
        ('CreateObject',),
    'May create an OLE object using PowerShell':
        ('New-Object',),
    'May run an application (if combined with CreateObject)':
        ('Shell.Application',),
    'May enumerate application windows (if combined with Shell.Application object)':
        ('Windows', 'FindWindow'),
    'May run code from a DLL':
    #TODO: regex to find declare+lib on same line
        ('Lib',),
    'May inject code into another process':
        ('CreateThread', 'VirtualAlloc', # (issue #9) suggested by Davy Douhine - used by MSF payload
        ),
    'May download files from the Internet':
    #TODO: regex to find urlmon+URLDownloadToFileA on same line
        ('URLDownloadToFileA', 'Msxml2.XMLHTTP', 'Microsoft.XMLHTTP',
         'MSXML2.ServerXMLHTTP', # suggested in issue #13
         'User-Agent', # sample from @ozhermit: http://pastebin.com/MPc3iV6z
        ),
    'May download files from the Internet using PowerShell':
    #sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
        ('Net.WebClient', 'DownloadFile', 'DownloadString'),
    'May control another application by simulating user keystrokes':
        ('SendKeys', 'AppActivate'),
    #SendKeys: http://msdn.microsoft.com/en-us/library/office/gg278655%28v=office.15%29.aspx
    'May attempt to obfuscate malicious function calls':
        ('CallByName',),
    #CallByName: http://msdn.microsoft.com/en-us/library/office/gg278760%28v=office.15%29.aspx
    'May attempt to obfuscate specific strings':
    #TODO: regex to find several Chr*, not just one
        ('Chr', 'ChrB', 'ChrW', 'StrReverse', 'Xor'),
    #Chr: http://msdn.microsoft.com/en-us/library/office/gg264465%28v=office.15%29.aspx
    'May read or write registry keys':
    #sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
        ('RegOpenKeyExA', 'RegOpenKeyEx', 'RegCloseKey'),
    'May read registry keys':
    #sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
        ('RegQueryValueExA', 'RegQueryValueEx',
         'RegRead',  #with Wscript.Shell
        ),
    'May detect virtualization':
    # sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
        (r'SYSTEM\ControlSet001\Services\Disk\Enum', 'VIRTUAL', 'VMWARE', 'VBOX'),
    'May detect Anubis Sandbox':
    # sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
    # NOTES: this sample also checks App.EXEName but that seems to be a bug, it works in VB6 but not in VBA
    # ref: http://www.syssec-project.eu/m/page-media/3/disarm-raid11.pdf
        ('GetVolumeInformationA', 'GetVolumeInformation',  # with kernel32.dll
         '1824245000', r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProductId',
         '76487-337-8429955-22614', 'andy', 'sample', r'C:\exec\exec.exe', 'popupkiller'
        ),
    'May detect Sandboxie':
    # sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
    # ref: http://www.cplusplus.com/forum/windows/96874/
        ('SbieDll.dll', 'SandboxieControlWndClass'),
    'May detect Sunbelt Sandbox':
    # ref: http://www.cplusplus.com/forum/windows/96874/
        (r'C:\file.exe',),
    'May detect Norman Sandbox':
    # ref: http://www.cplusplus.com/forum/windows/96874/
        ('currentuser',),
    'May detect CW Sandbox':
    # ref: http://www.cplusplus.com/forum/windows/96874/
        ('Schmidti',),
    'May detect WinJail Sandbox':
    # ref: http://www.cplusplus.com/forum/windows/96874/
        ('Afx:400000:0',),
}

# Regular Expression for a URL:
# http://en.wikipedia.org/wiki/Uniform_resource_locator
# http://www.w3.org/Addressing/URL/uri-spec.html
#TODO: also support username:password@server
#TODO: other protocols (file, gopher, wais, ...?)
SCHEME = r'\b(?:http|ftp)s?'
# see http://en.wikipedia.org/wiki/List_of_Internet_top-level_domains
TLD = r'(?:xn--[a-zA-Z0-9]{4,20}|[a-zA-Z]{2,20})'
DNS_NAME = r'(?:[a-zA-Z0-9\-\.]+\.' + TLD + ')'
#TODO: IPv6 - see https://www.debuggex.com/
# A literal numeric IPv6 address may be given, but must be enclosed in [ ] e.g. [db8:0cec::99:123a]
NUMBER_0_255 = r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])'
IPv4 = r'(?:' + NUMBER_0_255 + r'\.){3}' + NUMBER_0_255
# IPv4 must come before the DNS name because it is more specific
SERVER = r'(?:' + IPv4 + '|' + DNS_NAME + ')'
PORT = r'(?:\:[0-9]{1,5})?'
SERVER_PORT = SERVER + PORT
URL_PATH = r'(?:/[a-zA-Z0-9\-\._\?\,\'/\\\+&%\$#\=~]*)?'  # [^\.\,\)\(\s"]
URL_RE = SCHEME + r'\://' + SERVER_PORT + URL_PATH
re_url = re.compile(URL_RE)


# Patterns to be extracted (IP addresses, URLs, etc)
# From patterns.py in balbuzard
RE_PATTERNS = (
    ('URL', re.compile(URL_RE)),
    ('IPv4 address', re.compile(IPv4)),
    # TODO: add IPv6
    ('E-mail address', re.compile(r'(?i)\b[A-Z0-9._%+-]+@' + SERVER + '\b')),
    # ('Domain name', re.compile(r'(?=^.{1,254}$)(^(?:(?!\d+\.|-)[a-zA-Z0-9_\-]{1,63}(?<!-)\.?)+(?:[a-zA-Z]{2,})$)')),
    # Executable file name with known extensions (except .com which is present in many URLs, and .application):
    ("Executable file name", re.compile(
        r"(?i)\b\w+\.(EXE|PIF|GADGET|MSI|MSP|MSC|VBS|VBE|VB|JSE|JS|WSF|WSC|WSH|WS|BAT|CMD|DLL|SCR|HTA|CPL|CLASS|JAR|PS1XML|PS1|PS2XML|PS2|PSC1|PSC2|SCF|LNK|INF|REG)\b")),
    # Sources: http://www.howtogeek.com/137270/50-file-extensions-that-are-potentially-dangerous-on-windows/
    # TODO: https://support.office.com/en-us/article/Blocked-attachments-in-Outlook-3811cddc-17c3-4279-a30c-060ba0207372#__attachment_file_types
    # TODO: add win & unix file paths
    #('Hex string', re.compile(r'(?:[0-9A-Fa-f]{2}){4,}')),
)

# regex to detect strings encoded in hexadecimal
re_hex_string = re.compile(r'(?:[0-9A-Fa-f]{2}){4,}')

# regex to detect strings encoded in base64
#re_base64_string = re.compile(r'"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?"')
# better version from balbuzard, less false positives:
# (plain version without double quotes, used also below in quoted_base64_string)
BASE64_RE = r'(?:[A-Za-z0-9+/]{4}){1,}(?:[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=|[A-Za-z0-9+/][AQgw]==)?'
re_base64_string = re.compile('"' + BASE64_RE + '"')
# white list of common strings matching the base64 regex, but which are not base64 strings (all lowercase):
BASE64_WHITELIST = set(['thisdocument', 'thisworkbook', 'test', 'temp', 'http', 'open', 'exit'])

# regex to detect strings encoded with a specific Dridex algorithm
# (see https://github.com/JamesHabben/MalwareStuff)
re_dridex_string = re.compile(r'"[0-9A-Za-z]{20,}"')
# regex to check that it is not just a hex string:
re_nothex_check = re.compile(r'[G-Zg-z]')

# regex to extract printable strings (at least 5 chars) from VBA Forms:
re_printable_string = re.compile(r'[\t\r\n\x20-\xFF]{5,}')


# === PARTIAL VBA GRAMMAR ====================================================

# REFERENCES:
# - [MS-VBAL]: VBA Language Specification
#   https://msdn.microsoft.com/en-us/library/dd361851.aspx
# - pyparsing: http://pyparsing.wikispaces.com/

# TODO: set whitespaces according to VBA
# TODO: merge extended lines before parsing

# VBA identifier chars (from MS-VBAL 3.3.5)
vba_identifier_chars = alphanums + '_'

class VbaExpressionString(str):
    """
    Class identical to str, used to distinguish plain strings from strings
    obfuscated using VBA expressions (Chr, StrReverse, etc)
    Usage: each VBA expression parse action should convert strings to
    VbaExpressionString.
    Then isinstance(s, VbaExpressionString) is True only for VBA expressions.
     (see detect_vba_strings)
    """
    # TODO: use Unicode everywhere instead of str
    pass


# --- NUMBER TOKENS ----------------------------------------------------------

# 3.3.2 Number Tokens
# INTEGER = integer-literal ["%" / "&" / "^"]
# integer-literal = decimal-literal / octal-literal / hex-literal
# decimal-literal = 1*decimal-digit
# octal-literal = "&" [%x004F / %x006F] 1*octal-digit
# ; & or &o or &O
# hex-literal = "&" (%x0048 / %x0068) 1*hex-digit
# ; &h or &H
# octal-digit = "0" / "1" / "2" / "3" / "4" / "5" / "6" / "7"
# decimal-digit = octal-digit / "8" / "9"
# hex-digit = decimal-digit / %x0041-0046 / %x0061-0066 ;A-F / a-f

# NOTE: here Combine() is required to avoid spaces between elements
# NOTE: here WordStart is necessary to avoid matching a number preceded by
#       letters or underscore (e.g. "VBT1" or "ABC_34"), when using scanString
decimal_literal = Combine(WordStart(vba_identifier_chars) + Word(nums)
                          + Suppress(Optional(Word('%&^', exact=1))))
decimal_literal.setParseAction(lambda t: int(t[0]))

octal_literal = Combine(Suppress(Literal('&') + Optional((CaselessLiteral('o')))) + Word(srange('[0-7]'))
                + Suppress(Optional(Word('%&^', exact=1))))
octal_literal.setParseAction(lambda t: int(t[0], base=8))

hex_literal = Combine(Suppress(CaselessLiteral('&h')) + Word(srange('[0-9a-fA-F]'))
                + Suppress(Optional(Word('%&^', exact=1))))
hex_literal.setParseAction(lambda t: int(t[0], base=16))

integer = decimal_literal | octal_literal | hex_literal


# --- QUOTED STRINGS ---------------------------------------------------------

# 3.3.4 String Tokens
# STRING = double-quote *string-character (double-quote / line-continuation / LINE-END)
# double-quote = %x0022 ; "
# string-character = NO-LINE-CONTINUATION ((double-quote double-quote) termination-character)

quoted_string = QuotedString('"', escQuote='""')
quoted_string.setParseAction(lambda t: str(t[0]))


#--- VBA Expressions ---------------------------------------------------------

# See MS-VBAL 5.6 Expressions

# need to pre-declare using Forward() because it is recursive
# VBA string expression and integer expression
vba_expr_str = Forward()
vba_expr_int = Forward()

# --- CHR --------------------------------------------------------------------

# MS-VBAL 6.1.2.11.1.4 Chr / Chr$
# Function Chr(CharCode As Long) As Variant
# Function Chr$(CharCode As Long) As String
# Parameter Description
# CharCode Long whose value is a code point.
# Returns a String data value consisting of a single character containing the character whose code
# point is the data value of the argument.
# - If the argument is not in the range 0 to 255, Error Number 5 ("Invalid procedure call or
# argument") is raised unless the implementation supports a character set with a larger code point
# range.
# - If the argument value is in the range of 0 to 127, it is interpreted as a 7-bit ASCII code point.
# - If the argument value is in the range of 128 to 255, the code point interpretation of the value is
# implementation defined.
# - Chr$ has the same runtime semantics as Chr, however the declared type of its function result is
# String rather than Variant.

# 6.1.2.11.1.5 ChrB / ChrB$
# Function ChrB(CharCode As Long) As Variant
# Function ChrB$(CharCode As Long) As String
# CharCode Long whose value is a code point.
# Returns a String data value consisting of a single byte character whose code point value is the
# data value of the argument.
# - If the argument is not in the range 0 to 255, Error Number 6 ("Overflow") is raised.
# - ChrB$ has the same runtime semantics as ChrB however the declared type of its function result
# is String rather than Variant.
# - Note: the ChrB function is used with byte data contained in a String. Instead of returning a
# character, which may be one or two bytes, ChrB always returns a single byte. The ChrW function
# returns a String containing the Unicode character except on platforms where Unicode is not
# supported, in which case, the behavior is identical to the Chr function.

# 6.1.2.11.1.6 ChrW/ ChrW$
# Function ChrW(CharCode As Long) As Variant
# Function ChrW$(CharCode As Long) As String
# CharCode Long whose value is a code point.
# Returns a String data value consisting of a single character containing the character whose code
# point is the data value of the argument.
# - If the argument is not in the range -32,767 to 65,535 then Error Number 5 ("Invalid procedure
# call or argument") is raised.
# - If the argument is a negative value it is treated as if it was the value: CharCode + 65,536.
# - If the implemented uses 16-bit Unicode code points argument, data value is interpreted as a 16-
# bit Unicode code point.
# - If the implementation does not support Unicode, ChrW has the same semantics as Chr.
# - ChrW$ has the same runtime semantics as ChrW, however the declared type of its function result
# is String rather than Variant.

# Chr, Chr$, ChrB, ChrW(int) => char
vba_chr = Suppress(
            Combine(WordStart(vba_identifier_chars) + CaselessLiteral('Chr')
            + Optional(CaselessLiteral('B') | CaselessLiteral('W')) + Optional('$'))
            + '(') + vba_expr_int + Suppress(')')

def vba_chr_tostr(t):
    try:
        i = t[0]
        # normal, non-unicode character:
        if i>=0 and i<=255:
            return VbaExpressionString(chr(i))
        else:
            return VbaExpressionString(unichr(i).encode('utf-8', 'backslashreplace'))
    except ValueError:
        log.exception('ERROR: incorrect parameter value for chr(): %r' % i)
        return VbaExpressionString('Chr(%r)' % i)

vba_chr.setParseAction(vba_chr_tostr)


# --- ASC --------------------------------------------------------------------

# Asc(char) => int
#TODO: see MS-VBAL 6.1.2.11.1.1 page 240 => AscB, AscW
vba_asc = Suppress(CaselessKeyword('Asc') + '(') + vba_expr_str + Suppress(')')
vba_asc.setParseAction(lambda t: ord(t[0]))


# --- VAL --------------------------------------------------------------------

# Val(string) => int
# TODO: make sure the behavior of VBA's val is fully covered
vba_val = Suppress(CaselessKeyword('Val') + '(') + vba_expr_str + Suppress(')')
vba_val.setParseAction(lambda t: int(t[0].strip()))


# --- StrReverse() --------------------------------------------------------------------

# StrReverse(string) => string
strReverse = Suppress(CaselessKeyword('StrReverse') + '(') + vba_expr_str + Suppress(')')
strReverse.setParseAction(lambda t: VbaExpressionString(str(t[0])[::-1]))


# --- ENVIRON() --------------------------------------------------------------------

# Environ("name") => just translated to "%name%", that is enough for malware analysis
environ = Suppress(CaselessKeyword('Environ') + '(') + vba_expr_str + Suppress(')')
environ.setParseAction(lambda t: VbaExpressionString('%%%s%%' % t[0]))


# --- IDENTIFIER -------------------------------------------------------------

#TODO: see MS-VBAL 3.3.5 page 33
# 3.3.5 Identifier Tokens
# Latin-identifier = first-Latin-identifier-character *subsequent-Latin-identifier-character
# first-Latin-identifier-character = (%x0041-005A / %x0061-007A) ; A-Z / a-z
# subsequent-Latin-identifier-character = first-Latin-identifier-character / DIGIT / %x5F ; underscore
latin_identifier = Word(initChars=alphas, bodyChars=alphanums + '_')

# --- HEX FUNCTION -----------------------------------------------------------

# match any custom function name with a hex string as argument:
# TODO: accept vba_expr_str_item as argument, check if it is a hex or base64 string at runtime

# quoted string of at least two hexadecimal numbers of two digits:
quoted_hex_string = Suppress('"') + Combine(Word(hexnums, exact=2) * (2, None)) + Suppress('"')
quoted_hex_string.setParseAction(lambda t: str(t[0]))

hex_function_call = Suppress(latin_identifier) + Suppress('(') + \
                    quoted_hex_string('hex_string') + Suppress(')')
hex_function_call.setParseAction(lambda t: VbaExpressionString(binascii.a2b_hex(t.hex_string)))


# --- BASE64 FUNCTION -----------------------------------------------------------

# match any custom function name with a Base64 string as argument:
# TODO: accept vba_expr_str_item as argument, check if it is a hex or base64 string at runtime

# quoted string of at least two hexadecimal numbers of two digits:
quoted_base64_string = Suppress('"') + Regex(BASE64_RE) + Suppress('"')
quoted_base64_string.setParseAction(lambda t: str(t[0]))

base64_function_call = Suppress(latin_identifier) + Suppress('(') + \
                    quoted_base64_string('base64_string') + Suppress(')')
base64_function_call.setParseAction(lambda t: VbaExpressionString(binascii.a2b_base64(t.base64_string)))


# ---STRING EXPRESSION -------------------------------------------------------

def concat_strings_list(tokens):
    """
    parse action to concatenate strings in a VBA expression with operators '+' or '&'
    """
    # extract argument from the tokens:
    # expected to be a tuple containing a list of strings such as [a,'&',b,'&',c,...]
    strings = tokens[0][::2]
    return VbaExpressionString(''.join(strings))


vba_expr_str_item = (vba_chr | strReverse | environ | quoted_string | hex_function_call | base64_function_call)

vba_expr_str <<= infixNotation(vba_expr_str_item,
    [
        ("+", 2, opAssoc.LEFT, concat_strings_list),
        ("&", 2, opAssoc.LEFT, concat_strings_list),
    ])


# --- INTEGER EXPRESSION -------------------------------------------------------

def sum_ints_list(tokens):
    """
    parse action to sum integers in a VBA expression with operator '+'
    """
    # extract argument from the tokens:
    # expected to be a tuple containing a list of integers such as [a,'&',b,'&',c,...]
    integers = tokens[0][::2]
    return sum(integers)


def subtract_ints_list(tokens):
    """
    parse action to subtract integers in a VBA expression with operator '-'
    """
    # extract argument from the tokens:
    # expected to be a tuple containing a list of integers such as [a,'&',b,'&',c,...]
    integers = tokens[0][::2]
    return reduce(lambda x,y:x-y, integers)


def multiply_ints_list(tokens):
    """
    parse action to multiply integers in a VBA expression with operator '*'
    """
    # extract argument from the tokens:
    # expected to be a tuple containing a list of integers such as [a,'&',b,'&',c,...]
    integers = tokens[0][::2]
    return reduce(lambda x,y:x*y, integers)


def divide_ints_list(tokens):
    """
    parse action to divide integers in a VBA expression with operator '/'
    """
    # extract argument from the tokens:
    # expected to be a tuple containing a list of integers such as [a,'&',b,'&',c,...]
    integers = tokens[0][::2]
    return reduce(lambda x,y:x/y, integers)


vba_expr_int_item = (vba_asc | vba_val | integer)

# operators associativity:
# https://en.wikipedia.org/wiki/Operator_associativity

vba_expr_int <<= infixNotation(vba_expr_int_item,
    [
        ("*", 2, opAssoc.LEFT, multiply_ints_list),
        ("/", 2, opAssoc.LEFT, divide_ints_list),
        ("-", 2, opAssoc.LEFT, subtract_ints_list),
        ("+", 2, opAssoc.LEFT, sum_ints_list),
    ])


# see detect_vba_strings for the deobfuscation code using this grammar

# === MSO/ActiveMime files parsing ===========================================

def is_mso_file(data):
    """
    Check if the provided data is the content of a MSO/ActiveMime file, such as
    the ones created by Outlook in some cases, or Word/Excel when saving a
    file with the MHTML format or the Word 2003 XML format.
    This function only checks the ActiveMime magic at the beginning of data.
    :param data: bytes string, MSO/ActiveMime file content
    :return: bool, True if the file is MSO, False otherwise
    """
    return data.startswith(MSO_ACTIVEMIME_HEADER)


# regex to find zlib block headers, starting with byte 0x78 = 'x'
re_zlib_header = re.compile(r'x')


def mso_file_extract(data):
    """
    Extract the data stored into a MSO/ActiveMime file, such as
    the ones created by Outlook in some cases, or Word/Excel when saving a
    file with the MHTML format or the Word 2003 XML format.

    :param data: bytes string, MSO/ActiveMime file content
    :return: bytes string, extracted data (uncompressed)

    raise a RuntimeError if the data cannot be extracted
    """
    # check the magic:
    assert is_mso_file(data)
    # First, attempt to get the compressed data offset from the header
    # According to my tests, it should be an unsigned 16 bits integer,
    # at offset 0x1E (little endian) + add 46:
    try:
        offset = struct.unpack_from('<H', data, offset=0x1E)[0] + 46
        log.debug('Parsing MSO file: data offset = 0x%X' % offset)
    except KeyboardInterrupt:
        # do not ignore exceptions when the user presses Ctrl+C/Pause:
        raise
    except:
        log.exception('Unable to parse MSO/ActiveMime file header')
        raise RuntimeError('Unable to parse MSO/ActiveMime file header')
    # In all the samples seen so far, Word always uses an offset of 0x32,
    # and Excel 0x22A. But we read the offset from the header to be more
    # generic.
    # Let's try that offset, then 0x32 and 0x22A, just in case:
    for start in (offset, 0x32, 0x22A):
        try:
            log.debug('Attempting zlib decompression from MSO file offset 0x%X' % start)
            extracted_data = zlib.decompress(data[start:])
            return extracted_data
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:
            log.exception('zlib decompression failed')
    # None of the guessed offsets worked, let's try brute-forcing by looking
    # for potential zlib-compressed blocks starting with 0x78:
    log.debug('Looking for potential zlib-compressed blocks in MSO file')
    for match in re_zlib_header.finditer(data):
        start = match.start()
        try:
            log.debug('Attempting zlib decompression from MSO file offset 0x%X' % start)
            extracted_data = zlib.decompress(data[start:])
            return extracted_data
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:
            log.exception('zlib decompression failed')
    raise RuntimeError('Unable to decompress data from a MSO/ActiveMime file')


#--- FUNCTIONS ----------------------------------------------------------------

# set of printable characters, for is_printable
_PRINTABLE_SET = set(string.printable)

def is_printable(s):
    """
    returns True if string s only contains printable ASCII characters
    (i.e. contained in string.printable)
    This is similar to Python 3's str.isprintable, for Python 2.x.
    :param s: str
    :return: bool
    """
    # inspired from http://stackoverflow.com/questions/3636928/test-if-a-python-string-is-printable
    # check if the set of chars from s is contained into the set of printable chars:
    return set(s).issubset(_PRINTABLE_SET)


def print_json(j):
    """
    Print a dictionary, a list or any other object to stdout
    :param j: object to be printed
    :return:
    """
    if isinstance(j, dict):
        for key, val in j.items():
            print_json(key)
            print_json(val)
    elif isinstance(j, list):
        for elem in j:
            print_json(elem)
    else:
        try:
            if len(j) > 20:
                print type(j), repr(j[:20]), '...(len {0})'.format(len(j))
            else:
                print type(j), repr(j)
        except TypeError:
            print type(j), repr(j)


def copytoken_help(decompressed_current, decompressed_chunk_start):
    """
    compute bit masks to decode a CopyToken according to MS-OVBA 2.4.1.3.19.1 CopyToken Help

    decompressed_current: number of decompressed bytes so far, i.e. len(decompressed_container)
    decompressed_chunk_start: offset of the current chunk in the decompressed container
    return length_mask, offset_mask, bit_count, maximum_length
    """
    difference = decompressed_current - decompressed_chunk_start
    bit_count = int(math.ceil(math.log(difference, 2)))
    bit_count = max([bit_count, 4])
    length_mask = 0xFFFF >> bit_count
    offset_mask = ~length_mask
    maximum_length = (0xFFFF >> bit_count) + 3
    return length_mask, offset_mask, bit_count, maximum_length


def decompress_stream(compressed_container):
    """
    Decompress a stream according to MS-OVBA section 2.4.1

    compressed_container: string compressed according to the MS-OVBA 2.4.1.3.6 Compression algorithm
    return the decompressed container as a string (bytes)
    """
    # 2.4.1.2 State Variables

    # The following state is maintained for the CompressedContainer (section 2.4.1.1.1):
    # CompressedRecordEnd: The location of the byte after the last byte in the CompressedContainer (section 2.4.1.1.1).
    # CompressedCurrent: The location of the next byte in the CompressedContainer (section 2.4.1.1.1) to be read by
    #                    decompression or to be written by compression.

    # The following state is maintained for the current CompressedChunk (section 2.4.1.1.4):
    # CompressedChunkStart: The location of the first byte of the CompressedChunk (section 2.4.1.1.4) within the
    #                       CompressedContainer (section 2.4.1.1.1).

    # The following state is maintained for a DecompressedBuffer (section 2.4.1.1.2):
    # DecompressedCurrent: The location of the next byte in the DecompressedBuffer (section 2.4.1.1.2) to be written by
    #                      decompression or to be read by compression.
    # DecompressedBufferEnd: The location of the byte after the last byte in the DecompressedBuffer (section 2.4.1.1.2).

    # The following state is maintained for the current DecompressedChunk (section 2.4.1.1.3):
    # DecompressedChunkStart: The location of the first byte of the DecompressedChunk (section 2.4.1.1.3) within the
    #                         DecompressedBuffer (section 2.4.1.1.2).

    decompressed_container = ''  # result
    compressed_current = 0

    sig_byte = ord(compressed_container[compressed_current])
    if sig_byte != 0x01:
        raise ValueError('invalid signature byte {0:02X}'.format(sig_byte))

    compressed_current += 1

    #NOTE: the definition of CompressedRecordEnd is ambiguous. Here we assume that
    # CompressedRecordEnd = len(compressed_container)
    while compressed_current < len(compressed_container):
        # 2.4.1.1.5
        compressed_chunk_start = compressed_current
        # chunk header = first 16 bits
        compressed_chunk_header = \
            struct.unpack("<H", compressed_container[compressed_chunk_start:compressed_chunk_start + 2])[0]
        # chunk size = 12 first bits of header + 3
        chunk_size = (compressed_chunk_header & 0x0FFF) + 3
        # chunk signature = 3 next bits - should always be 0b011
        chunk_signature = (compressed_chunk_header >> 12) & 0x07
        if chunk_signature != 0b011:
            raise ValueError('Invalid CompressedChunkSignature in VBA compressed stream')
        # chunk flag = next bit - 1 == compressed, 0 == uncompressed
        chunk_flag = (compressed_chunk_header >> 15) & 0x01
        log.debug("chunk size = {0}, compressed flag = {1}".format(chunk_size, chunk_flag))

        #MS-OVBA 2.4.1.3.12: the maximum size of a chunk including its header is 4098 bytes (header 2 + data 4096)
        # The minimum size is 3 bytes
        # NOTE: there seems to be a typo in MS-OVBA, the check should be with 4098, not 4095 (which is the max value
        # in chunk header before adding 3.
        # Also the first test is not useful since a 12 bits value cannot be larger than 4095.
        if chunk_flag == 1 and chunk_size > 4098:
            raise ValueError('CompressedChunkSize > 4098 but CompressedChunkFlag == 1')
        if chunk_flag == 0 and chunk_size != 4098:
            raise ValueError('CompressedChunkSize != 4098 but CompressedChunkFlag == 0')

        # check if chunk_size goes beyond the compressed data, instead of silently cutting it:
        #TODO: raise an exception?
        if compressed_chunk_start + chunk_size > len(compressed_container):
            log.warning('Chunk size is larger than remaining compressed data')
        compressed_end = min([len(compressed_container), compressed_chunk_start + chunk_size])
        # read after chunk header:
        compressed_current = compressed_chunk_start + 2

        if chunk_flag == 0:
            # MS-OVBA 2.4.1.3.3 Decompressing a RawChunk
            # uncompressed chunk: read the next 4096 bytes as-is
            #TODO: check if there are at least 4096 bytes left
            decompressed_container += compressed_container[compressed_current:compressed_current + 4096]
            compressed_current += 4096
        else:
            # MS-OVBA 2.4.1.3.2 Decompressing a CompressedChunk
            # compressed chunk
            decompressed_chunk_start = len(decompressed_container)
            while compressed_current < compressed_end:
                # MS-OVBA 2.4.1.3.4 Decompressing a TokenSequence
                # log.debug('compressed_current = %d / compressed_end = %d' % (compressed_current, compressed_end))
                # FlagByte: 8 bits indicating if the following 8 tokens are either literal (1 byte of plain text) or
                # copy tokens (reference to a previous literal token)
                flag_byte = ord(compressed_container[compressed_current])
                compressed_current += 1
                for bit_index in xrange(0, 8):
                    # log.debug('bit_index=%d / compressed_current=%d / compressed_end=%d' % (bit_index, compressed_current, compressed_end))
                    if compressed_current >= compressed_end:
                        break
                    # MS-OVBA 2.4.1.3.5 Decompressing a Token
                    # MS-OVBA 2.4.1.3.17 Extract FlagBit
                    flag_bit = (flag_byte >> bit_index) & 1
                    #log.debug('bit_index=%d: flag_bit=%d' % (bit_index, flag_bit))
                    if flag_bit == 0:  # LiteralToken
                        # copy one byte directly to output
                        decompressed_container += compressed_container[compressed_current]
                        compressed_current += 1
                    else:  # CopyToken
                        # MS-OVBA 2.4.1.3.19.2 Unpack CopyToken
                        copy_token = \
                            struct.unpack("<H", compressed_container[compressed_current:compressed_current + 2])[0]
                        #TODO: check this
                        length_mask, offset_mask, bit_count, maximum_length = copytoken_help(
                            len(decompressed_container), decompressed_chunk_start)
                        length = (copy_token & length_mask) + 3
                        temp1 = copy_token & offset_mask
                        temp2 = 16 - bit_count
                        offset = (temp1 >> temp2) + 1
                        #log.debug('offset=%d length=%d' % (offset, length))
                        copy_source = len(decompressed_container) - offset
                        for index in xrange(copy_source, copy_source + length):
                            decompressed_container += decompressed_container[index]
                        compressed_current += 2
    return decompressed_container


def _extract_vba(ole, vba_root, project_path, dir_path):
    """
    Extract VBA macros from an OleFileIO object.
    Internal function, do not call directly.

    vba_root: path to the VBA root storage, containing the VBA storage and the PROJECT stream
    vba_project: path to the PROJECT stream
    This is a generator, yielding (stream path, VBA filename, VBA source code) for each VBA code stream
    """
    # Open the PROJECT stream:
    project = ole.openstream(project_path)

    # sample content of the PROJECT stream:

    ##    ID="{5312AC8A-349D-4950-BDD0-49BE3C4DD0F0}"
    ##    Document=ThisDocument/&H00000000
    ##    Module=NewMacros
    ##    Name="Project"
    ##    HelpContextID="0"
    ##    VersionCompatible32="393222000"
    ##    CMG="F1F301E705E705E705E705"
    ##    DPB="8F8D7FE3831F2020202020"
    ##    GC="2D2FDD81E51EE61EE6E1"
    ##
    ##    [Host Extender Info]
    ##    &H00000001={3832D640-CF90-11CF-8E43-00A0C911005A};VBE;&H00000000
    ##    &H00000002={000209F2-0000-0000-C000-000000000046};Word8.0;&H00000000
    ##
    ##    [Workspace]
    ##    ThisDocument=22, 29, 339, 477, Z
    ##    NewMacros=-4, 42, 832, 510, C

    code_modules = {}

    for line in project:
        line = line.strip()
        if '=' in line:
            # split line at the 1st equal sign:
            name, value = line.split('=', 1)
            # looking for code modules
            # add the code module as a key in the dictionary
            # the value will be the extension needed later
            # The value is converted to lowercase, to allow case-insensitive matching (issue #3)
            value = value.lower()
            if name == 'Document':
                # split value at the 1st slash, keep 1st part:
                value = value.split('/', 1)[0]
                code_modules[value] = CLASS_EXTENSION
            elif name == 'Module':
                code_modules[value] = MODULE_EXTENSION
            elif name == 'Class':
                code_modules[value] = CLASS_EXTENSION
            elif name == 'BaseClass':
                code_modules[value] = FORM_EXTENSION

    # read data from dir stream (compressed)
    dir_compressed = ole.openstream(dir_path).read()

    def check_value(name, expected, value):
        if expected != value:
            log.error("invalid value for {0} expected {1:04X} got {2:04X}".format(name, expected, value))

    dir_stream = cStringIO.StringIO(decompress_stream(dir_compressed))

    # PROJECTSYSKIND Record
    PROJECTSYSKIND_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTSYSKIND_Id', 0x0001, PROJECTSYSKIND_Id)
    PROJECTSYSKIND_Size = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTSYSKIND_Size', 0x0004, PROJECTSYSKIND_Size)
    PROJECTSYSKIND_SysKind = struct.unpack("<L", dir_stream.read(4))[0]
    if PROJECTSYSKIND_SysKind == 0x00:
        log.debug("16-bit Windows")
    elif PROJECTSYSKIND_SysKind == 0x01:
        log.debug("32-bit Windows")
    elif PROJECTSYSKIND_SysKind == 0x02:
        log.debug("Macintosh")
    elif PROJECTSYSKIND_SysKind == 0x03:
        log.debug("64-bit Windows")
    else:
        log.error("invalid PROJECTSYSKIND_SysKind {0:04X}".format(PROJECTSYSKIND_SysKind))

    # PROJECTLCID Record
    PROJECTLCID_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTLCID_Id', 0x0002, PROJECTLCID_Id)
    PROJECTLCID_Size = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTLCID_Size', 0x0004, PROJECTLCID_Size)
    PROJECTLCID_Lcid = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTLCID_Lcid', 0x409, PROJECTLCID_Lcid)

    # PROJECTLCIDINVOKE Record
    PROJECTLCIDINVOKE_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTLCIDINVOKE_Id', 0x0014, PROJECTLCIDINVOKE_Id)
    PROJECTLCIDINVOKE_Size = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTLCIDINVOKE_Size', 0x0004, PROJECTLCIDINVOKE_Size)
    PROJECTLCIDINVOKE_LcidInvoke = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTLCIDINVOKE_LcidInvoke', 0x409, PROJECTLCIDINVOKE_LcidInvoke)

    # PROJECTCODEPAGE Record
    PROJECTCODEPAGE_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTCODEPAGE_Id', 0x0003, PROJECTCODEPAGE_Id)
    PROJECTCODEPAGE_Size = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTCODEPAGE_Size', 0x0002, PROJECTCODEPAGE_Size)
    PROJECTCODEPAGE_CodePage = struct.unpack("<H", dir_stream.read(2))[0]

    # PROJECTNAME Record
    PROJECTNAME_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTNAME_Id', 0x0004, PROJECTNAME_Id)
    PROJECTNAME_SizeOfProjectName = struct.unpack("<L", dir_stream.read(4))[0]
    if PROJECTNAME_SizeOfProjectName < 1 or PROJECTNAME_SizeOfProjectName > 128:
        log.error("PROJECTNAME_SizeOfProjectName value not in range: {0}".format(PROJECTNAME_SizeOfProjectName))
    PROJECTNAME_ProjectName = dir_stream.read(PROJECTNAME_SizeOfProjectName)

    # PROJECTDOCSTRING Record
    PROJECTDOCSTRING_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTDOCSTRING_Id', 0x0005, PROJECTDOCSTRING_Id)
    PROJECTDOCSTRING_SizeOfDocString = struct.unpack("<L", dir_stream.read(4))[0]
    if PROJECTNAME_SizeOfProjectName > 2000:
        log.error(
            "PROJECTDOCSTRING_SizeOfDocString value not in range: {0}".format(PROJECTDOCSTRING_SizeOfDocString))
    PROJECTDOCSTRING_DocString = dir_stream.read(PROJECTDOCSTRING_SizeOfDocString)
    PROJECTDOCSTRING_Reserved = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTDOCSTRING_Reserved', 0x0040, PROJECTDOCSTRING_Reserved)
    PROJECTDOCSTRING_SizeOfDocStringUnicode = struct.unpack("<L", dir_stream.read(4))[0]
    if PROJECTDOCSTRING_SizeOfDocStringUnicode % 2 != 0:
        log.error("PROJECTDOCSTRING_SizeOfDocStringUnicode is not even")
    PROJECTDOCSTRING_DocStringUnicode = dir_stream.read(PROJECTDOCSTRING_SizeOfDocStringUnicode)

    # PROJECTHELPFILEPATH Record - MS-OVBA 2.3.4.2.1.7
    PROJECTHELPFILEPATH_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTHELPFILEPATH_Id', 0x0006, PROJECTHELPFILEPATH_Id)
    PROJECTHELPFILEPATH_SizeOfHelpFile1 = struct.unpack("<L", dir_stream.read(4))[0]
    if PROJECTHELPFILEPATH_SizeOfHelpFile1 > 260:
        log.error(
            "PROJECTHELPFILEPATH_SizeOfHelpFile1 value not in range: {0}".format(PROJECTHELPFILEPATH_SizeOfHelpFile1))
    PROJECTHELPFILEPATH_HelpFile1 = dir_stream.read(PROJECTHELPFILEPATH_SizeOfHelpFile1)
    PROJECTHELPFILEPATH_Reserved = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTHELPFILEPATH_Reserved', 0x003D, PROJECTHELPFILEPATH_Reserved)
    PROJECTHELPFILEPATH_SizeOfHelpFile2 = struct.unpack("<L", dir_stream.read(4))[0]
    if PROJECTHELPFILEPATH_SizeOfHelpFile2 != PROJECTHELPFILEPATH_SizeOfHelpFile1:
        log.error("PROJECTHELPFILEPATH_SizeOfHelpFile1 does not equal PROJECTHELPFILEPATH_SizeOfHelpFile2")
    PROJECTHELPFILEPATH_HelpFile2 = dir_stream.read(PROJECTHELPFILEPATH_SizeOfHelpFile2)
    if PROJECTHELPFILEPATH_HelpFile2 != PROJECTHELPFILEPATH_HelpFile1:
        log.error("PROJECTHELPFILEPATH_HelpFile1 does not equal PROJECTHELPFILEPATH_HelpFile2")

    # PROJECTHELPCONTEXT Record
    PROJECTHELPCONTEXT_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTHELPCONTEXT_Id', 0x0007, PROJECTHELPCONTEXT_Id)
    PROJECTHELPCONTEXT_Size = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTHELPCONTEXT_Size', 0x0004, PROJECTHELPCONTEXT_Size)
    PROJECTHELPCONTEXT_HelpContext = struct.unpack("<L", dir_stream.read(4))[0]

    # PROJECTLIBFLAGS Record
    PROJECTLIBFLAGS_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTLIBFLAGS_Id', 0x0008, PROJECTLIBFLAGS_Id)
    PROJECTLIBFLAGS_Size = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTLIBFLAGS_Size', 0x0004, PROJECTLIBFLAGS_Size)
    PROJECTLIBFLAGS_ProjectLibFlags = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTLIBFLAGS_ProjectLibFlags', 0x0000, PROJECTLIBFLAGS_ProjectLibFlags)

    # PROJECTVERSION Record
    PROJECTVERSION_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTVERSION_Id', 0x0009, PROJECTVERSION_Id)
    PROJECTVERSION_Reserved = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTVERSION_Reserved', 0x0004, PROJECTVERSION_Reserved)
    PROJECTVERSION_VersionMajor = struct.unpack("<L", dir_stream.read(4))[0]
    PROJECTVERSION_VersionMinor = struct.unpack("<H", dir_stream.read(2))[0]

    # PROJECTCONSTANTS Record
    PROJECTCONSTANTS_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTCONSTANTS_Id', 0x000C, PROJECTCONSTANTS_Id)
    PROJECTCONSTANTS_SizeOfConstants = struct.unpack("<L", dir_stream.read(4))[0]
    if PROJECTCONSTANTS_SizeOfConstants > 1015:
        log.error(
            "PROJECTCONSTANTS_SizeOfConstants value not in range: {0}".format(PROJECTCONSTANTS_SizeOfConstants))
    PROJECTCONSTANTS_Constants = dir_stream.read(PROJECTCONSTANTS_SizeOfConstants)
    PROJECTCONSTANTS_Reserved = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTCONSTANTS_Reserved', 0x003C, PROJECTCONSTANTS_Reserved)
    PROJECTCONSTANTS_SizeOfConstantsUnicode = struct.unpack("<L", dir_stream.read(4))[0]
    if PROJECTCONSTANTS_SizeOfConstantsUnicode % 2 != 0:
        log.error("PROJECTCONSTANTS_SizeOfConstantsUnicode is not even")
    PROJECTCONSTANTS_ConstantsUnicode = dir_stream.read(PROJECTCONSTANTS_SizeOfConstantsUnicode)

    # array of REFERENCE records
    check = None
    while True:
        check = struct.unpack("<H", dir_stream.read(2))[0]
        log.debug("reference type = {0:04X}".format(check))
        if check == 0x000F:
            break

        if check == 0x0016:
            # REFERENCENAME
            REFERENCE_Id = check
            REFERENCE_SizeOfName = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCE_Name = dir_stream.read(REFERENCE_SizeOfName)
            REFERENCE_Reserved = struct.unpack("<H", dir_stream.read(2))[0]
            check_value('REFERENCE_Reserved', 0x003E, REFERENCE_Reserved)
            REFERENCE_SizeOfNameUnicode = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCE_NameUnicode = dir_stream.read(REFERENCE_SizeOfNameUnicode)
            continue

        if check == 0x0033:
            # REFERENCEORIGINAL (followed by REFERENCECONTROL)
            REFERENCEORIGINAL_Id = check
            REFERENCEORIGINAL_SizeOfLibidOriginal = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCEORIGINAL_LibidOriginal = dir_stream.read(REFERENCEORIGINAL_SizeOfLibidOriginal)
            continue

        if check == 0x002F:
            # REFERENCECONTROL
            REFERENCECONTROL_Id = check
            REFERENCECONTROL_SizeTwiddled = struct.unpack("<L", dir_stream.read(4))[0]  # ignore
            REFERENCECONTROL_SizeOfLibidTwiddled = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCECONTROL_LibidTwiddled = dir_stream.read(REFERENCECONTROL_SizeOfLibidTwiddled)
            REFERENCECONTROL_Reserved1 = struct.unpack("<L", dir_stream.read(4))[0]  # ignore
            check_value('REFERENCECONTROL_Reserved1', 0x0000, REFERENCECONTROL_Reserved1)
            REFERENCECONTROL_Reserved2 = struct.unpack("<H", dir_stream.read(2))[0]  # ignore
            check_value('REFERENCECONTROL_Reserved2', 0x0000, REFERENCECONTROL_Reserved2)
            # optional field
            check2 = struct.unpack("<H", dir_stream.read(2))[0]
            if check2 == 0x0016:
                REFERENCECONTROL_NameRecordExtended_Id = check
                REFERENCECONTROL_NameRecordExtended_SizeofName = struct.unpack("<L", dir_stream.read(4))[0]
                REFERENCECONTROL_NameRecordExtended_Name = dir_stream.read(
                    REFERENCECONTROL_NameRecordExtended_SizeofName)
                REFERENCECONTROL_NameRecordExtended_Reserved = struct.unpack("<H", dir_stream.read(2))[0]
                check_value('REFERENCECONTROL_NameRecordExtended_Reserved', 0x003E,
                            REFERENCECONTROL_NameRecordExtended_Reserved)
                REFERENCECONTROL_NameRecordExtended_SizeOfNameUnicode = struct.unpack("<L", dir_stream.read(4))[0]
                REFERENCECONTROL_NameRecordExtended_NameUnicode = dir_stream.read(
                    REFERENCECONTROL_NameRecordExtended_SizeOfNameUnicode)
                REFERENCECONTROL_Reserved3 = struct.unpack("<H", dir_stream.read(2))[0]
            else:
                REFERENCECONTROL_Reserved3 = check2

            check_value('REFERENCECONTROL_Reserved3', 0x0030, REFERENCECONTROL_Reserved3)
            REFERENCECONTROL_SizeExtended = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCECONTROL_SizeOfLibidExtended = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCECONTROL_LibidExtended = dir_stream.read(REFERENCECONTROL_SizeOfLibidExtended)
            REFERENCECONTROL_Reserved4 = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCECONTROL_Reserved5 = struct.unpack("<H", dir_stream.read(2))[0]
            REFERENCECONTROL_OriginalTypeLib = dir_stream.read(16)
            REFERENCECONTROL_Cookie = struct.unpack("<L", dir_stream.read(4))[0]
            continue

        if check == 0x000D:
            # REFERENCEREGISTERED
            REFERENCEREGISTERED_Id = check
            REFERENCEREGISTERED_Size = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCEREGISTERED_SizeOfLibid = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCEREGISTERED_Libid = dir_stream.read(REFERENCEREGISTERED_SizeOfLibid)
            REFERENCEREGISTERED_Reserved1 = struct.unpack("<L", dir_stream.read(4))[0]
            check_value('REFERENCEREGISTERED_Reserved1', 0x0000, REFERENCEREGISTERED_Reserved1)
            REFERENCEREGISTERED_Reserved2 = struct.unpack("<H", dir_stream.read(2))[0]
            check_value('REFERENCEREGISTERED_Reserved2', 0x0000, REFERENCEREGISTERED_Reserved2)
            continue

        if check == 0x000E:
            # REFERENCEPROJECT
            REFERENCEPROJECT_Id = check
            REFERENCEPROJECT_Size = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCEPROJECT_SizeOfLibidAbsolute = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCEPROJECT_LibidAbsolute = dir_stream.read(REFERENCEPROJECT_SizeOfLibidAbsolute)
            REFERENCEPROJECT_SizeOfLibidRelative = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCEPROJECT_LibidRelative = dir_stream.read(REFERENCEPROJECT_SizeOfLibidRelative)
            REFERENCEPROJECT_MajorVersion = struct.unpack("<L", dir_stream.read(4))[0]
            REFERENCEPROJECT_MinorVersion = struct.unpack("<H", dir_stream.read(2))[0]
            continue

        log.error('invalid or unknown check Id {0:04X}'.format(check))
        sys.exit(0)

    PROJECTMODULES_Id = check  #struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTMODULES_Id', 0x000F, PROJECTMODULES_Id)
    PROJECTMODULES_Size = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTMODULES_Size', 0x0002, PROJECTMODULES_Size)
    PROJECTMODULES_Count = struct.unpack("<H", dir_stream.read(2))[0]
    PROJECTMODULES_ProjectCookieRecord_Id = struct.unpack("<H", dir_stream.read(2))[0]
    check_value('PROJECTMODULES_ProjectCookieRecord_Id', 0x0013, PROJECTMODULES_ProjectCookieRecord_Id)
    PROJECTMODULES_ProjectCookieRecord_Size = struct.unpack("<L", dir_stream.read(4))[0]
    check_value('PROJECTMODULES_ProjectCookieRecord_Size', 0x0002, PROJECTMODULES_ProjectCookieRecord_Size)
    PROJECTMODULES_ProjectCookieRecord_Cookie = struct.unpack("<H", dir_stream.read(2))[0]

    log.debug("parsing {0} modules".format(PROJECTMODULES_Count))
    for x in xrange(0, PROJECTMODULES_Count):
        MODULENAME_Id = struct.unpack("<H", dir_stream.read(2))[0]
        check_value('MODULENAME_Id', 0x0019, MODULENAME_Id)
        MODULENAME_SizeOfModuleName = struct.unpack("<L", dir_stream.read(4))[0]
        MODULENAME_ModuleName = dir_stream.read(MODULENAME_SizeOfModuleName)
        # account for optional sections
        section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x0047:
            MODULENAMEUNICODE_Id = section_id
            MODULENAMEUNICODE_SizeOfModuleNameUnicode = struct.unpack("<L", dir_stream.read(4))[0]
            MODULENAMEUNICODE_ModuleNameUnicode = dir_stream.read(MODULENAMEUNICODE_SizeOfModuleNameUnicode)
            section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x001A:
            MODULESTREAMNAME_id = section_id
            MODULESTREAMNAME_SizeOfStreamName = struct.unpack("<L", dir_stream.read(4))[0]
            MODULESTREAMNAME_StreamName = dir_stream.read(MODULESTREAMNAME_SizeOfStreamName)
            MODULESTREAMNAME_Reserved = struct.unpack("<H", dir_stream.read(2))[0]
            check_value('MODULESTREAMNAME_Reserved', 0x0032, MODULESTREAMNAME_Reserved)
            MODULESTREAMNAME_SizeOfStreamNameUnicode = struct.unpack("<L", dir_stream.read(4))[0]
            MODULESTREAMNAME_StreamNameUnicode = dir_stream.read(MODULESTREAMNAME_SizeOfStreamNameUnicode)
            section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x001C:
            MODULEDOCSTRING_Id = section_id
            check_value('MODULEDOCSTRING_Id', 0x001C, MODULEDOCSTRING_Id)
            MODULEDOCSTRING_SizeOfDocString = struct.unpack("<L", dir_stream.read(4))[0]
            MODULEDOCSTRING_DocString = dir_stream.read(MODULEDOCSTRING_SizeOfDocString)
            MODULEDOCSTRING_Reserved = struct.unpack("<H", dir_stream.read(2))[0]
            check_value('MODULEDOCSTRING_Reserved', 0x0048, MODULEDOCSTRING_Reserved)
            MODULEDOCSTRING_SizeOfDocStringUnicode = struct.unpack("<L", dir_stream.read(4))[0]
            MODULEDOCSTRING_DocStringUnicode = dir_stream.read(MODULEDOCSTRING_SizeOfDocStringUnicode)
            section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x0031:
            MODULEOFFSET_Id = section_id
            check_value('MODULEOFFSET_Id', 0x0031, MODULEOFFSET_Id)
            MODULEOFFSET_Size = struct.unpack("<L", dir_stream.read(4))[0]
            check_value('MODULEOFFSET_Size', 0x0004, MODULEOFFSET_Size)
            MODULEOFFSET_TextOffset = struct.unpack("<L", dir_stream.read(4))[0]
            section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x001E:
            MODULEHELPCONTEXT_Id = section_id
            check_value('MODULEHELPCONTEXT_Id', 0x001E, MODULEHELPCONTEXT_Id)
            MODULEHELPCONTEXT_Size = struct.unpack("<L", dir_stream.read(4))[0]
            check_value('MODULEHELPCONTEXT_Size', 0x0004, MODULEHELPCONTEXT_Size)
            MODULEHELPCONTEXT_HelpContext = struct.unpack("<L", dir_stream.read(4))[0]
            section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x002C:
            MODULECOOKIE_Id = section_id
            check_value('MODULECOOKIE_Id', 0x002C, MODULECOOKIE_Id)
            MODULECOOKIE_Size = struct.unpack("<L", dir_stream.read(4))[0]
            check_value('MODULECOOKIE_Size', 0x0002, MODULECOOKIE_Size)
            MODULECOOKIE_Cookie = struct.unpack("<H", dir_stream.read(2))[0]
            section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x0021 or section_id == 0x0022:
            MODULETYPE_Id = section_id
            MODULETYPE_Reserved = struct.unpack("<L", dir_stream.read(4))[0]
            section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x0025:
            MODULEREADONLY_Id = section_id
            check_value('MODULEREADONLY_Id', 0x0025, MODULEREADONLY_Id)
            MODULEREADONLY_Reserved = struct.unpack("<L", dir_stream.read(4))[0]
            check_value('MODULEREADONLY_Reserved', 0x0000, MODULEREADONLY_Reserved)
            section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x0028:
            MODULEPRIVATE_Id = section_id
            check_value('MODULEPRIVATE_Id', 0x0028, MODULEPRIVATE_Id)
            MODULEPRIVATE_Reserved = struct.unpack("<L", dir_stream.read(4))[0]
            check_value('MODULEPRIVATE_Reserved', 0x0000, MODULEPRIVATE_Reserved)
            section_id = struct.unpack("<H", dir_stream.read(2))[0]
        if section_id == 0x002B:  # TERMINATOR
            MODULE_Reserved = struct.unpack("<L", dir_stream.read(4))[0]
            check_value('MODULE_Reserved', 0x0000, MODULE_Reserved)
            section_id = None
        if section_id != None:
            log.warning('unknown or invalid module section id {0:04X}'.format(section_id))

        log.debug('Project CodePage = %d' % PROJECTCODEPAGE_CodePage)
        vba_codec = 'cp%d' % PROJECTCODEPAGE_CodePage
        log.debug("ModuleName = {0}".format(MODULENAME_ModuleName))
        log.debug("StreamName = {0}".format(repr(MODULESTREAMNAME_StreamName)))
        streamname_unicode = MODULESTREAMNAME_StreamName.decode(vba_codec)
        log.debug("StreamName.decode('%s') = %s" % (vba_codec, repr(streamname_unicode)))
        log.debug("StreamNameUnicode = {0}".format(repr(MODULESTREAMNAME_StreamNameUnicode)))
        log.debug("TextOffset = {0}".format(MODULEOFFSET_TextOffset))

        code_path = vba_root + u'VBA/' + streamname_unicode
        #TODO: test if stream exists
        log.debug('opening VBA code stream %s' % repr(code_path))
        code_data = ole.openstream(code_path).read()
        log.debug("length of code_data = {0}".format(len(code_data)))
        log.debug("offset of code_data = {0}".format(MODULEOFFSET_TextOffset))
        code_data = code_data[MODULEOFFSET_TextOffset:]
        if len(code_data) > 0:
            code_data = decompress_stream(code_data)
            # case-insensitive search in the code_modules dict to find the file extension:
            filext = code_modules.get(MODULENAME_ModuleName.lower(), 'bin')
            filename = '{0}.{1}'.format(MODULENAME_ModuleName, filext)
            #TODO: also yield the codepage so that callers can decode it properly
            yield (code_path, filename, code_data)
            # print '-'*79
            # print filename
            # print ''
            # print code_data
            # print ''
            log.debug('extracted file {0}'.format(filename))
        else:
            log.warning("module stream {0} has code data length 0".format(MODULESTREAMNAME_StreamName))
    return


def vba_collapse_long_lines(vba_code):
    """
    Parse a VBA module code to detect continuation line characters (underscore) and
    collapse split lines. Continuation line characters are replaced by spaces.

    :param vba_code: str, VBA module code
    :return: str, VBA module code with long lines collapsed
    """
    # TODO: use a regex instead, to allow whitespaces after the underscore?
    vba_code = vba_code.replace(' _\r\n', ' ')
    vba_code = vba_code.replace(' _\r', ' ')
    vba_code = vba_code.replace(' _\n', ' ')
    return vba_code


def filter_vba(vba_code):
    """
    Filter VBA source code to remove the first lines starting with "Attribute VB_",
    which are automatically added by MS Office and not displayed in the VBA Editor.
    This should only be used when displaying source code for human analysis.

    Note: lines are not filtered if they contain a colon, because it could be
    used to hide malicious instructions.

    :param vba_code: str, VBA source code
    :return: str, filtered VBA source code
    """
    vba_lines = vba_code.splitlines()
    start = 0
    for line in vba_lines:
        if line.startswith("Attribute VB_") and not ':' in line:
            start += 1
        else:
            break
    #TODO: also remove empty lines?
    vba = '\n'.join(vba_lines[start:])
    return vba


def detect_autoexec(vba_code, obfuscation=None):
    """
    Detect if the VBA code contains keywords corresponding to macros running
    automatically when triggered by specific actions (e.g. when a document is
    opened or closed).

    :param vba_code: str, VBA source code
    :param obfuscation: None or str, name of obfuscation to be added to description
    :return: list of str tuples (keyword, description)
    """
    #TODO: merge code with detect_suspicious
    # case-insensitive search
    #vba_code = vba_code.lower()
    results = []
    obf_text = ''
    if obfuscation:
        obf_text = ' (obfuscation: %s)' % obfuscation
    for description, keywords in AUTOEXEC_KEYWORDS.items():
        for keyword in keywords:
            #TODO: if keyword is already a compiled regex, use it as-is
            # search using regex to detect word boundaries:
            if re.search(r'(?i)\b' + keyword + r'\b', vba_code):
                #if keyword.lower() in vba_code:
                results.append((keyword, description + obf_text))
    return results


def detect_suspicious(vba_code, obfuscation=None):
    """
    Detect if the VBA code contains suspicious keywords corresponding to
    potential malware behaviour.

    :param vba_code: str, VBA source code
    :param obfuscation: None or str, name of obfuscation to be added to description
    :return: list of str tuples (keyword, description)
    """
    # case-insensitive search
    #vba_code = vba_code.lower()
    results = []
    obf_text = ''
    if obfuscation:
        obf_text = ' (obfuscation: %s)' % obfuscation
    for description, keywords in SUSPICIOUS_KEYWORDS.items():
        for keyword in keywords:
            # search using regex to detect word boundaries:
            if re.search(r'(?i)\b' + keyword + r'\b', vba_code):
                #if keyword.lower() in vba_code:
                results.append((keyword, description + obf_text))
    return results


def detect_patterns(vba_code, obfuscation=None):
    """
    Detect if the VBA code contains specific patterns such as IP addresses,
    URLs, e-mail addresses, executable file names, etc.

    :param vba_code: str, VBA source code
    :return: list of str tuples (pattern type, value)
    """
    results = []
    found = set()
    obf_text = ''
    if obfuscation:
        obf_text = ' (obfuscation: %s)' % obfuscation
    for pattern_type, pattern_re in RE_PATTERNS:
        for match in pattern_re.finditer(vba_code):
            value = match.group()
            if value not in found:
                results.append((pattern_type + obf_text, value))
                found.add(value)
    return results


def detect_hex_strings(vba_code):
    """
    Detect if the VBA code contains strings encoded in hexadecimal.

    :param vba_code: str, VBA source code
    :return: list of str tuples (encoded string, decoded string)
    """
    results = []
    found = set()
    for match in re_hex_string.finditer(vba_code):
        value = match.group()
        if value not in found:
            decoded = binascii.unhexlify(value)
            results.append((value, decoded))
            found.add(value)
    return results


def detect_base64_strings(vba_code):
    """
    Detect if the VBA code contains strings encoded in base64.

    :param vba_code: str, VBA source code
    :return: list of str tuples (encoded string, decoded string)
    """
    #TODO: avoid matching simple hex strings as base64?
    results = []
    found = set()
    for match in re_base64_string.finditer(vba_code):
        # extract the base64 string without quotes:
        value = match.group().strip('"')
        # check it is not just a hex string:
        if not re_nothex_check.search(value):
            continue
        # only keep new values and not in the whitelist:
        if value not in found and value.lower() not in BASE64_WHITELIST:
            try:
                decoded = base64.b64decode(value)
                results.append((value, decoded))
                found.add(value)
            except KeyboardInterrupt:
                # do not ignore exceptions when the user presses Ctrl+C/Pause:
                raise
            except:
                # if an exception occurs, it is likely not a base64-encoded string
                pass
    return results


def detect_dridex_strings(vba_code):
    """
    Detect if the VBA code contains strings obfuscated with a specific algorithm found in Dridex samples.

    :param vba_code: str, VBA source code
    :return: list of str tuples (encoded string, decoded string)
    """
    from thirdparty.DridexUrlDecoder.DridexUrlDecoder import DridexUrlDecode

    results = []
    found = set()
    for match in re_dridex_string.finditer(vba_code):
        value = match.group()[1:-1]
        # check it is not just a hex string:
        if not re_nothex_check.search(value):
            continue
        if value not in found:
            try:
                decoded = DridexUrlDecode(value)
                results.append((value, decoded))
                found.add(value)
            except KeyboardInterrupt:
                # do not ignore exceptions when the user presses Ctrl+C/Pause:
                raise
            except:
                # if an exception occurs, it is likely not a dridex-encoded string
                pass
    return results


def detect_vba_strings(vba_code):
    """
    Detect if the VBA code contains strings obfuscated with VBA expressions
    using keywords such as Chr, Asc, Val, StrReverse, etc.

    :param vba_code: str, VBA source code
    :return: list of str tuples (encoded string, decoded string)
    """
    # TODO: handle exceptions
    results = []
    found = set()
    # IMPORTANT: to extract the actual VBA expressions found in the code,
    #            we must expand tabs to have the same string as pyparsing.
    #            Otherwise, start and end offsets are incorrect.
    vba_code = vba_code.expandtabs()
    for tokens, start, end in vba_expr_str.scanString(vba_code):
        encoded = vba_code[start:end]
        decoded = tokens[0]
        if isinstance(decoded, VbaExpressionString):
            # This is a VBA expression, not a simple string
            # print 'VBA EXPRESSION: encoded=%r => decoded=%r' % (encoded, decoded)
            # remove parentheses and quotes from original string:
            # if encoded.startswith('(') and encoded.endswith(')'):
            #     encoded = encoded[1:-1]
            # if encoded.startswith('"') and encoded.endswith('"'):
            #     encoded = encoded[1:-1]
            # avoid duplicates and simple strings:
            if encoded not in found and decoded != encoded:
                results.append((encoded, decoded))
                found.add(encoded)
        # else:
            # print 'VBA STRING: encoded=%r => decoded=%r' % (encoded, decoded)
    return results


def json2ascii(json_obj, encoding='utf8', errors='replace'):
    """ ensure there is no unicode in json and all strings are safe to decode

    works recursively, decodes and re-encodes every string to/from unicode
    to ensure there will be no trouble in loading the dumped json output
    """
    if json_obj is None:
        pass
    elif isinstance(json_obj, (bool, int, float)):
        pass
    elif isinstance(json_obj, str):
        dencoded = json_obj.decode(encoding, errors).encode(encoding, errors)
        if dencoded != str:
            logging.info('json2ascii: replaced: {0} (len {1})'
                         .format(json_obj, len(json_obj)))
            logging.info('json2ascii:     with: {0} (len {1})'
                         .format(dencoded, len(dencoded)))
        return dencoded
    elif isinstance(json_obj, unicode):
        logging.info('json2ascii: replaced: {0}'
                     .format(json_obj.encode(encoding, errors)))
        # cannot put original into logger
        # print 'original: ' json_obj
        return json_obj.encode(encoding, errors)
    elif isinstance(json_obj, dict):
        for key in json_obj:
            json_obj[key] = json2ascii(json_obj[key])
    elif isinstance(json_obj, (list,tuple)):
        for item in json_obj:
            item = json2ascii(item)
    else:
        logging.debug('unexpected type in json2ascii: {0} -- leave as is'
                      .format(type(json_obj)))
    return json_obj


class VBA_Scanner(object):
    """
    Class to scan the source code of a VBA module to find obfuscated strings,
    suspicious keywords, IOCs, auto-executable macros, etc.
    """

    def __init__(self, vba_code):
        """
        VBA_Scanner constructor

        :param vba_code: str, VBA source code to be analyzed
        """
        # join long lines ending with " _":
        self.code = vba_collapse_long_lines(vba_code)
        self.code_hex = ''
        self.code_hex_rev = ''
        self.code_rev_hex = ''
        self.code_base64 = ''
        self.code_dridex = ''
        self.code_vba = ''
        self.strReverse = None
        # results = None before scanning, then a list of tuples after scanning
        self.results = None
        self.autoexec_keywords = None
        self.suspicious_keywords = None
        self.iocs = None
        self.hex_strings = None
        self.base64_strings = None
        self.dridex_strings = None
        self.vba_strings = None


    def scan(self, include_decoded_strings=False, deobfuscate=False):
        """
        Analyze the provided VBA code to detect suspicious keywords,
        auto-executable macros, IOC patterns, obfuscation patterns
        such as hex-encoded strings.

        :param include_decoded_strings: bool, if True, all encoded strings will be included with their decoded content.
        :param deobfuscate: bool, if True attempt to deobfuscate VBA expressions (slow)
        :return: list of tuples (type, keyword, description)
        (type = 'AutoExec', 'Suspicious', 'IOC', 'Hex String', 'Base64 String' or 'Dridex String')
        """
        # First, detect and extract hex-encoded strings:
        self.hex_strings = detect_hex_strings(self.code)
        # detect if the code contains StrReverse:
        self.strReverse = False
        if 'strreverse' in self.code.lower(): self.strReverse = True
        # Then append the decoded strings to the VBA code, to detect obfuscated IOCs and keywords:
        for encoded, decoded in self.hex_strings:
            self.code_hex += '\n' + decoded
            # if the code contains "StrReverse", also append the hex strings in reverse order:
            if self.strReverse:
                # StrReverse after hex decoding:
                self.code_hex_rev += '\n' + decoded[::-1]
                # StrReverse before hex decoding:
                self.code_rev_hex += '\n' + binascii.unhexlify(encoded[::-1])
                #example: https://malwr.com/analysis/NmFlMGI4YTY1YzYyNDkwNTg1ZTBiZmY5OGI3YjlhYzU/
        #TODO: also append the full code reversed if StrReverse? (risk of false positives?)
        # Detect Base64-encoded strings
        self.base64_strings = detect_base64_strings(self.code)
        for encoded, decoded in self.base64_strings:
            self.code_base64 += '\n' + decoded
        # Detect Dridex-encoded strings
        self.dridex_strings = detect_dridex_strings(self.code)
        for encoded, decoded in self.dridex_strings:
            self.code_dridex += '\n' + decoded
        # Detect obfuscated strings in VBA expressions
        if deobfuscate:
            self.vba_strings = detect_vba_strings(self.code)
        else:
            self.vba_strings = []
        for encoded, decoded in self.vba_strings:
            self.code_vba += '\n' + decoded
        results = []
        self.autoexec_keywords = []
        self.suspicious_keywords = []
        self.iocs = []

        for code, obfuscation in (
                (self.code, None),
                (self.code_hex, 'Hex'),
                (self.code_hex_rev, 'Hex+StrReverse'),
                (self.code_rev_hex, 'StrReverse+Hex'),
                (self.code_base64, 'Base64'),
                (self.code_dridex, 'Dridex'),
                (self.code_vba, 'VBA expression'),
        ):
            self.autoexec_keywords += detect_autoexec(code, obfuscation)
            self.suspicious_keywords += detect_suspicious(code, obfuscation)
            self.iocs += detect_patterns(code, obfuscation)

        # If hex-encoded strings were discovered, add an item to suspicious keywords:
        if self.hex_strings:
            self.suspicious_keywords.append(('Hex Strings',
                                             'Hex-encoded strings were detected, may be used to obfuscate strings (option --decode to see all)'))
        if self.base64_strings:
            self.suspicious_keywords.append(('Base64 Strings',
                                             'Base64-encoded strings were detected, may be used to obfuscate strings (option --decode to see all)'))
        if self.dridex_strings:
            self.suspicious_keywords.append(('Dridex Strings',
                                             'Dridex-encoded strings were detected, may be used to obfuscate strings (option --decode to see all)'))
        if self.vba_strings:
            self.suspicious_keywords.append(('VBA obfuscated Strings',
                                             'VBA string expressions were detected, may be used to obfuscate strings (option --decode to see all)'))
        # use a set to avoid duplicate keywords
        keyword_set = set()
        for keyword, description in self.autoexec_keywords:
            if keyword not in keyword_set:
                results.append(('AutoExec', keyword, description))
                keyword_set.add(keyword)
        keyword_set = set()
        for keyword, description in self.suspicious_keywords:
            if keyword not in keyword_set:
                results.append(('Suspicious', keyword, description))
                keyword_set.add(keyword)
        keyword_set = set()
        for pattern_type, value in self.iocs:
            if value not in keyword_set:
                results.append(('IOC', value, pattern_type))
                keyword_set.add(value)

        # include decoded strings only if they are printable or if --decode option:
        for encoded, decoded in self.hex_strings:
            if include_decoded_strings or is_printable(decoded):
                results.append(('Hex String', decoded, encoded))
        for encoded, decoded in self.base64_strings:
            if include_decoded_strings or is_printable(decoded):
                results.append(('Base64 String', decoded, encoded))
        for encoded, decoded in self.dridex_strings:
            if include_decoded_strings or is_printable(decoded):
                results.append(('Dridex string', decoded, encoded))
        for encoded, decoded in self.vba_strings:
            if include_decoded_strings or is_printable(decoded):
                results.append(('VBA string', decoded, encoded))
        self.results = results
        return results

    def scan_summary(self):
        """
        Analyze the provided VBA code to detect suspicious keywords,
        auto-executable macros, IOC patterns, obfuscation patterns
        such as hex-encoded strings.

        :return: tuple with the number of items found for each category:
            (autoexec, suspicious, IOCs, hex, base64, dridex, vba)
        """
        # avoid scanning the same code twice:
        if self.results is None:
            self.scan()
        return (len(self.autoexec_keywords), len(self.suspicious_keywords),
                len(self.iocs), len(self.hex_strings), len(self.base64_strings),
                len(self.dridex_strings), len(self.vba_strings))


def scan_vba(vba_code, include_decoded_strings, deobfuscate=False):
    """
    Analyze the provided VBA code to detect suspicious keywords,
    auto-executable macros, IOC patterns, obfuscation patterns
    such as hex-encoded strings.
    (shortcut for VBA_Scanner(vba_code).scan())

    :param vba_code: str, VBA source code to be analyzed
    :param include_decoded_strings: bool, if True all encoded strings will be included with their decoded content.
    :param deobfuscate: bool, if True attempt to deobfuscate VBA expressions (slow)
    :return: list of tuples (type, keyword, description)
    (type = 'AutoExec', 'Suspicious', 'IOC', 'Hex String', 'Base64 String' or 'Dridex String')
    """
    return VBA_Scanner(vba_code).scan(include_decoded_strings, deobfuscate)


#=== CLASSES =================================================================

class VBA_Parser(object):
    """
    Class to parse MS Office files, to detect VBA macros and extract VBA source code
    Supported file formats:
    - Word 97-2003 (.doc, .dot)
    - Word 2007+ (.docm, .dotm)
    - Word 2003 XML (.xml)
    - Word MHT - Single File Web Page / MHTML (.mht)
    - Excel 97-2003 (.xls)
    - Excel 2007+ (.xlsm, .xlsb)
    - PowerPoint 2007+ (.pptm, .ppsm)
    """

    def __init__(self, filename, data=None, container=None):
        """
        Constructor for VBA_Parser

        :param filename: filename or path of file to parse, or file-like object

        :param data: None or bytes str, if None the file will be read from disk (or from the file-like object).
        If data is provided as a bytes string, it will be parsed as the content of the file in memory,
        and not read from disk. Note: files must be read in binary mode, i.e. open(f, 'rb').

        :param container: str, path and filename of container if the file is within
        a zip archive, None otherwise.
        """
        #TODO: filename should only be a string, data should be used for the file-like object
        #TODO: filename should be mandatory, optional data is a string or file-like object
        #TODO: also support olefile and zipfile as input
        if data is None:
            # open file from disk:
            _file = filename
        else:
            # file already read in memory, make it a file-like object for zipfile:
            _file = cStringIO.StringIO(data)
        #self.file = _file
        self.ole_file = None
        self.ole_subfiles = []
        self.filename = filename
        self.container = container
        self.type = None
        self.vba_projects = None
        self.vba_forms = None
        self.contains_macros = None # will be set to True or False by detect_macros
        self.vba_code_all_modules = None # to store the source code of all modules
        # list of tuples for each module: (subfilename, stream_path, vba_filename, vba_code)
        self.modules = None
        # Analysis results: list of tuples (type, keyword, description) - See VBA_Scanner
        self.analysis_results = None
        # statistics for the scan summary and flags
        self.nb_macros = 0
        self.nb_autoexec = 0
        self.nb_suspicious = 0
        self.nb_iocs = 0
        self.nb_hexstrings = 0
        self.nb_base64strings = 0
        self.nb_dridexstrings = 0
        self.nb_vbastrings = 0

        # if filename is None:
        #     if isinstance(_file, basestring):
        #         if len(_file) < olefile.MINIMAL_OLEFILE_SIZE:
        #             self.filename = _file
        #         else:
        #             self.filename = '<file in bytes string>'
        #     else:
        #         self.filename = '<file-like object>'
        if olefile.isOleFile(_file):
            # This looks like an OLE file
            self.open_ole(_file)
        if self.type is None and zipfile.is_zipfile(_file):
            # Zip file, which may be an OpenXML document
            self.open_openxml(_file)
        if self.type is None:
            # read file from disk, check if it is a Word 2003 XML file (WordProcessingML), Excel 2003 XML,
            # or a plain text file containing VBA code
            if data is None:
                data = open(filename, 'rb').read()
            # check if it is a Word 2003 XML file (WordProcessingML): must contain the namespace
            if 'http://schemas.microsoft.com/office/word/2003/wordml' in data:
                self.open_word2003xml(data)
            # store a lowercase version for the next tests:
            data_lowercase = data.lower()
            # check if it is a MHT file (MIME HTML, Word or Excel saved as "Single File Web Page"):
            # According to my tests, these files usually start with "MIME-Version: 1.0" on the 1st line
            # BUT Word accepts a blank line or other MIME headers inserted before,
            # and even whitespaces in between "MIME", "-", "Version" and ":". The version number is ignored.
            # And the line is case insensitive.
            # so we'll just check the presence of mime, version and multipart anywhere:
            if self.type is None and 'mime' in data_lowercase and 'version' in data_lowercase \
                and 'multipart' in data_lowercase:
                self.open_mht(data)
        #TODO: handle exceptions
        #TODO: Excel 2003 XML
            # Check if this is a plain text VBA or VBScript file:
            # To avoid scanning binary files, we simply check for some control chars:
            if self.type is None and '\x00' not in data:
                self.open_text(data)
        if self.type is None:
            # At this stage, could not match a known format:
            msg = '%s is not a supported file type, cannot extract VBA Macros.' % self.filename
            log.error(msg)
            raise TypeError(msg)

    def open_ole(self, _file):
        """
        Open an OLE file
        :param _file: filename or file contents in a file object
        :return: nothing
        """
        log.info('Opening OLE file %s' % self.filename)
        try:
            # Open and parse the OLE file, using unicode for path names:
            self.ole_file = olefile.OleFileIO(_file, path_encoding=None)
            # TODO: raise TypeError if this is a Powerpoint 97 file, since VBA macros cannot be detected yet
            # set type only if parsing succeeds
            self.type = TYPE_OLE
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:
            # TODO: handle OLE parsing exceptions
            log.exception('Failed OLE parsing for file %r' % self.filename)
            pass


    def open_openxml(self, _file):
        """
        Open an OpenXML file
        :param _file: filename or file contents in a file object
        :return: nothing
        """
        # This looks like a zip file, need to look for vbaProject.bin inside
        # It can be any OLE file inside the archive
        #...because vbaProject.bin can be renamed:
        # see http://www.decalage.info/files/JCV07_Lagadec_OpenDocument_OpenXML_v4_decalage.pdf#page=18
        log.info('Opening ZIP/OpenXML file %s' % self.filename)
        try:
            z = zipfile.ZipFile(_file)
            #TODO: check if this is actually an OpenXML file
            #TODO: if the zip file is encrypted, suggest to use the -z option, or try '-z infected' automatically
            # check each file within the zip if it is an OLE file, by reading its magic:
            for subfile in z.namelist():
                magic = z.open(subfile).read(len(olefile.MAGIC))
                if magic == olefile.MAGIC:
                    log.debug('Opening OLE file %s within zip' % subfile)
                    ole_data = z.open(subfile).read()
                    try:
                        self.ole_subfiles.append(VBA_Parser(filename=subfile, data=ole_data))
                    except KeyboardInterrupt:
                        # do not ignore exceptions when the user presses Ctrl+C/Pause:
                        raise
                    except:
                        log.debug('%s is not a valid OLE file' % subfile)
                        continue
            z.close()
            # set type only if parsing succeeds
            self.type = TYPE_OpenXML
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:
            # TODO: handle parsing exceptions
            log.exception('Failed Zip/OpenXML parsing for file %r' % self.filename)
            pass

    def open_word2003xml(self, data):
        """
        Open a Word 2003 XML file
        :param data: file contents in a string or bytes
        :return: nothing
        """
        log.info('Opening Word 2003 XML file %s' % self.filename)
        try:
            # parse the XML content
            # TODO: handle XML parsing exceptions
            et = ET.fromstring(data)
            # find all the binData elements:
            for bindata in et.getiterator(TAG_BINDATA):
                # the binData content is an OLE container for the VBA project, compressed
                # using the ActiveMime/MSO format (zlib-compressed), and Base64 encoded.
                # get the filename:
                fname = bindata.get(ATTR_NAME, 'noname.mso')
                # decode the base64 activemime
                mso_data = binascii.a2b_base64(bindata.text)
                if is_mso_file(mso_data):
                    # decompress the zlib data stored in the MSO file, which is the OLE container:
                    # TODO: handle different offsets => separate function
                    ole_data = mso_file_extract(mso_data)
                    try:
                        self.ole_subfiles.append(VBA_Parser(filename=fname, data=ole_data))
                    except KeyboardInterrupt:
                        # do not ignore exceptions when the user presses Ctrl+C/Pause:
                        raise
                    except:
                        log.error('%s does not contain a valid OLE file' % fname)
                else:
                    log.error('%s is not a valid MSO file' % fname)
            # set type only if parsing succeeds
            self.type = TYPE_Word2003_XML
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:
            # TODO: differentiate exceptions for each parsing stage
            log.exception('Failed XML parsing for file %r' % self.filename)
            pass

    def open_mht(self, data):
        """
        Open a MHTML file
        :param data: file contents in a string or bytes
        :return: nothing
        """
        log.info('Opening MHTML file %s' % self.filename)
        try:
            # parse the MIME content
            # remove any leading whitespace or newline (workaround for issue in email package)
            stripped_data = data.lstrip('\r\n\t ')
            # strip any junk from the beginning of the file
            # (issue #31 fix by Greg C - gdigreg)
            # TODO: improve keywords to avoid false positives
            mime_offset = stripped_data.find('MIME')
            content_offset = stripped_data.find('Content')
            # if "MIME" is found, and located before "Content":
            if -1 < mime_offset <= content_offset:
                stripped_data = stripped_data[mime_offset:]
            # else if "Content" is found, and before "MIME"
            # TODO: can it work without "MIME" at all?
            elif content_offset > -1:
                stripped_data = stripped_data[content_offset:]
            # TODO: quick and dirty fix: insert a standard line with MIME-Version header?
            mhtml = email.message_from_string(stripped_data)
            # find all the attached files:
            for part in mhtml.walk():
                content_type = part.get_content_type()  # always returns a value
                fname = part.get_filename(None)  # returns None if it fails
                # TODO: get content-location if no filename
                log.debug('MHTML part: filename=%r, content-type=%r' % (fname, content_type))
                part_data = part.get_payload(decode=True)
                # VBA macros are stored in a binary file named "editdata.mso".
                # the data content is an OLE container for the VBA project, compressed
                # using the ActiveMime/MSO format (zlib-compressed), and Base64 encoded.
                # decompress the zlib data starting at offset 0x32, which is the OLE container:
                # check ActiveMime header:
                if isinstance(part_data, str) and is_mso_file(part_data):
                    log.debug('Found ActiveMime header, decompressing MSO container')
                    try:
                        ole_data = mso_file_extract(part_data)
                        try:
                            # TODO: check if it is actually an OLE file
                            # TODO: get the MSO filename from content_location?
                            self.ole_subfiles.append(VBA_Parser(filename=fname, data=ole_data))
                        except KeyboardInterrupt:
                            # do not ignore exceptions when the user presses Ctrl+C/Pause:
                            raise
                        except:
                            log.debug('%s does not contain a valid OLE file' % fname)
                    except KeyboardInterrupt:
                        # do not ignore exceptions when the user presses Ctrl+C/Pause:
                        raise
                    except:
                        log.exception('Failed decompressing an MSO container in %r - %s'
                                      % (fname, MSG_OLEVBA_ISSUES))
                        # TODO: bug here - need to split in smaller functions/classes?
                else:
                    try:
                        log.debug('type(part_data) = %s' % type(part_data))
                        log.debug('part_data[0:20] = %r' % part_data[0:20])
                    except KeyboardInterrupt:
                        # do not ignore exceptions when the user presses Ctrl+C/Pause:
                        raise
                    except:
                        pass
            # set type only if parsing succeeds
            self.type = TYPE_MHTML
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:
            log.exception('Failed MIME parsing for file %r - %s'
                              % (self.filename, MSG_OLEVBA_ISSUES))
            pass


    def open_text(self, data):
        """
        Open a text file containing VBA or VBScript source code
        :param data: file contents in a string or bytes
        :return: nothing
        """
        log.info('Opening text file %s' % self.filename)
        try:
            # directly store the source code:
            self.vba_code_all_modules = data
            self.contains_macros = True
            # set type only if parsing succeeds
            self.type = TYPE_TEXT
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:
            log.exception('Failed text parsing for file %r - %s'
                              % (self.filename, MSG_OLEVBA_ISSUES))
            pass


    def find_vba_projects(self):
        """
        Finds all the VBA projects stored in an OLE file.

        Return None if the file is not OLE but OpenXML.
        Return a list of tuples (vba_root, project_path, dir_path) for each VBA project.
        vba_root is the path of the root OLE storage containing the VBA project,
        including a trailing slash unless it is the root of the OLE file.
        project_path is the path of the OLE stream named "PROJECT" within the VBA project.
        dir_path is the path of the OLE stream named "VBA/dir" within the VBA project.

        If this function returns an empty list for one of the supported formats
        (i.e. Word, Excel, Powerpoint except Powerpoint 97-2003), then the
        file does not contain VBA macros.

        :return: None if OpenXML file, list of tuples (vba_root, project_path, dir_path)
        for each VBA project found if OLE file
        """
        log.debug('VBA_Parser.find_vba_projects')
        # if the file is not OLE but OpenXML, return None:
        if self.ole_file is None:
            return None

        # if this method has already been called, return previous result:
        if self.vba_projects is not None:
            return self.vba_projects

        # Find the VBA project root (different in MS Word, Excel, etc):
        # - Word 97-2003: Macros
        # - Excel 97-2003: _VBA_PROJECT_CUR
        # - PowerPoint 97-2003: not supported yet (different file structure)
        # - Word 2007+: word/vbaProject.bin in zip archive, then the VBA project is the root of vbaProject.bin.
        # - Excel 2007+: xl/vbaProject.bin in zip archive, then same as Word
        # - PowerPoint 2007+: ppt/vbaProject.bin in zip archive, then same as Word
        # - Visio 2007: not supported yet (different file structure)

        # According to MS-OVBA section 2.2.1:
        # - the VBA project root storage MUST contain a VBA storage and a PROJECT stream
        # - The root/VBA storage MUST contain a _VBA_PROJECT stream and a dir stream
        # - all names are case-insensitive

        # start with an empty list:
        self.vba_projects = []
        # Look for any storage containing those storage/streams:
        ole = self.ole_file
        for storage in ole.listdir(streams=False, storages=True):
            log.debug('Checking storage %r' % storage)
            # Look for a storage ending with "VBA":
            if storage[-1].upper() == 'VBA':
                log.debug('Found VBA storage: %s' % ('/'.join(storage)))
                vba_root = '/'.join(storage[:-1])
                # Add a trailing slash to vba_root, unless it is the root of the OLE file:
                # (used later to append all the child streams/storages)
                if vba_root != '':
                    vba_root += '/'
                log.debug('Checking vba_root="%s"' % vba_root)

                def check_vba_stream(ole, vba_root, stream_path):
                    full_path = vba_root + stream_path
                    if ole.exists(full_path) and ole.get_type(full_path) == olefile.STGTY_STREAM:
                        log.debug('Found %s stream: %s' % (stream_path, full_path))
                        return full_path
                    else:
                        log.debug('Missing %s stream, this is not a valid VBA project structure' % stream_path)
                        return False

                # Check if the VBA root storage also contains a PROJECT stream:
                project_path = check_vba_stream(ole, vba_root, 'PROJECT')
                if not project_path: continue
                # Check if the VBA root storage also contains a VBA/_VBA_PROJECT stream:
                vba_project_path = check_vba_stream(ole, vba_root, 'VBA/_VBA_PROJECT')
                if not vba_project_path: continue
                # Check if the VBA root storage also contains a VBA/dir stream:
                dir_path = check_vba_stream(ole, vba_root, 'VBA/dir')
                if not dir_path: continue
                # Now we are pretty sure it is a VBA project structure
                log.debug('VBA root storage: "%s"' % vba_root)
                # append the results to the list as a tuple for later use:
                self.vba_projects.append((vba_root, project_path, dir_path))
        return self.vba_projects

    def detect_vba_macros(self):
        """
        Detect the potential presence of VBA macros in the file, by checking
        if it contains VBA projects. Both OLE and OpenXML files are supported.

        Important: for now, results are accurate only for Word, Excel and PowerPoint
        EXCEPT Powerpoint 97-2003, which has a different structure for VBA.

        Note: this method does NOT attempt to check the actual presence or validity
        of VBA macro source code, so there might be false positives.
        It may also detect VBA macros in files embedded within the main file,
        for example an Excel workbook with macros embedded into a Word
        document without macros may be detected, without distinction.

        :return: bool, True if at least one VBA project has been found, False otherwise
        """
        #TODO: return None or raise exception if format not supported like PPT 97-2003
        #TODO: return the number of VBA projects found instead of True/False?
        # if this method was already called, return the previous result:
        if self.contains_macros is not None:
            return self.contains_macros
        # if OpenXML, check all the OLE subfiles:
        if self.ole_file is None:
            for ole_subfile in self.ole_subfiles:
                if ole_subfile.detect_vba_macros():
                    self.contains_macros = True
                    return True
            # otherwise, no macro found:
            self.contains_macros = False
            return False
        # otherwise it's an OLE file, find VBA projects:
        vba_projects = self.find_vba_projects()
        if len(vba_projects) == 0:
            self.contains_macros = False
        else:
            self.contains_macros = True
        return self.contains_macros

    def extract_macros(self):
        """
        Extract and decompress source code for each VBA macro found in the file

        Iterator: yields (filename, stream_path, vba_filename, vba_code) for each VBA macro found
        If the file is OLE, filename is the path of the file.
        If the file is OpenXML, filename is the path of the OLE subfile containing VBA macros
        within the zip archive, e.g. word/vbaProject.bin.
        """
        if self.ole_file is None:
            # This may be either an OpenXML or a text file:
            if self.type == TYPE_TEXT:
                # This is a text file, yield the full code:
                yield (self.filename, '', self.filename, self.vba_code_all_modules)
            else:
                # OpenXML: recursively yield results from each OLE subfile:
                for ole_subfile in self.ole_subfiles:
                    for results in ole_subfile.extract_macros():
                        yield results
        else:
            # This is an OLE file:
            self.find_vba_projects()
            for vba_root, project_path, dir_path in self.vba_projects:
                # extract all VBA macros from that VBA root storage:
                for stream_path, vba_filename, vba_code in _extract_vba(self.ole_file, vba_root, project_path,
                                                                        dir_path):
                    yield (self.filename, stream_path, vba_filename, vba_code)


    def extract_all_macros(self):
        """
        Extract and decompress source code for each VBA macro found in the file
        by calling extract_macros(), store the results as a list of tuples
        (filename, stream_path, vba_filename, vba_code) in self.modules.
        See extract_macros for details.
        """
        if self.modules is None:
            self.modules = []
            for (subfilename, stream_path, vba_filename, vba_code) in self.extract_macros():
                self.modules.append((subfilename, stream_path, vba_filename, vba_code))
        self.nb_macros = len(self.modules)
        return self.modules



    def analyze_macros(self, show_decoded_strings=False, deobfuscate=False):
        """
        runs extract_macros and analyze the source code of all VBA macros
        found in the file.
        """
        if self.detect_vba_macros():
            # if the analysis was already done, avoid doing it twice:
            if self.analysis_results is not None:
                return self.analysis_results
            # variable to merge source code from all modules:
            if self.vba_code_all_modules is None:
                self.vba_code_all_modules = ''
                for (subfilename, stream_path, vba_filename, vba_code) in self.extract_all_macros():
                    #TODO: filter code? (each module)
                    self.vba_code_all_modules += vba_code + '\n'
                for (subfilename, form_path, form_string) in self.extract_form_strings():
                    self.vba_code_all_modules += form_string + '\n'
            # Analyze the whole code at once:
            scanner = VBA_Scanner(self.vba_code_all_modules)
            self.analysis_results = scanner.scan(show_decoded_strings, deobfuscate)
            autoexec, suspicious, iocs, hexstrings, base64strings, dridex, vbastrings = scanner.scan_summary()
            self.nb_autoexec += autoexec
            self.nb_suspicious += suspicious
            self.nb_iocs += iocs
            self.nb_hexstrings += hexstrings
            self.nb_base64strings += base64strings
            self.nb_dridexstrings += dridex
            self.nb_vbastrings += vbastrings

        return self.analysis_results


    def reveal(self):
        # we only want printable strings:
        analysis = self.analyze_macros(show_decoded_strings=False)
        # to avoid replacing short strings contained into longer strings, we sort the analysis results
        # based on the length of the encoded string, in reverse order:
        analysis = sorted(analysis, key=lambda type_decoded_encoded: len(type_decoded_encoded[2]), reverse=True)
        # normally now self.vba_code_all_modules contains source code from all modules
        deobf_code = self.vba_code_all_modules
        for kw_type, decoded, encoded in analysis:
            if kw_type == 'VBA string':
                #print '%3d occurences: %r => %r' % (deobf_code.count(encoded), encoded, decoded)
                # need to add double quotes around the decoded strings
                # after escaping double-quotes as double-double-quotes for VBA:
                decoded = decoded.replace('"', '""')
                deobf_code = deobf_code.replace(encoded, '"%s"' % decoded)
        return deobf_code
        #TODO: repasser l'analyse plusieurs fois si des chaines hex ou base64 sont revelees


    def find_vba_forms(self):
        """
        Finds all the VBA forms stored in an OLE file.

        Return None if the file is not OLE but OpenXML.
        Return a list of tuples (vba_root, project_path, dir_path) for each VBA project.
        vba_root is the path of the root OLE storage containing the VBA project,
        including a trailing slash unless it is the root of the OLE file.
        project_path is the path of the OLE stream named "PROJECT" within the VBA project.
        dir_path is the path of the OLE stream named "VBA/dir" within the VBA project.

        If this function returns an empty list for one of the supported formats
        (i.e. Word, Excel, Powerpoint except Powerpoint 97-2003), then the
        file does not contain VBA macros.

        :return: None if OpenXML file, list of tuples (vba_root, project_path, dir_path)
        for each VBA project found if OLE file
        """
        log.debug('VBA_Parser.find_vba_forms')
        # if the file is not OLE but OpenXML, return None:
        if self.ole_file is None:
            return None

        # if this method has already been called, return previous result:
        # if self.vba_projects is not None:
        #     return self.vba_projects

        # According to MS-OFORMS section 2.1.2 Control Streams:
        # - A parent control, that is, a control that can contain embedded controls,
        #   MUST be persisted as a storage that contains multiple streams.
        # - All parent controls MUST contain a FormControl. The FormControl
        #   properties are persisted to a stream (1) as specified in section 2.1.1.2.
        #   The name of this stream (1) MUST be "f".
        # - Embedded controls that cannot themselves contain other embedded
        #   controls are persisted sequentially as FormEmbeddedActiveXControls
        #   to a stream (1) contained in the same storage as the parent control.
        #   The name of this stream (1) MUST be "o".
        # - all names are case-insensitive

        # start with an empty list:
        self.vba_forms = []
        # Look for any storage containing those storage/streams:
        ole = self.ole_file
        for storage in ole.listdir(streams=False, storages=True):
            log.debug('Checking storage %r' % storage)
            # Look for two streams named 'o' and 'f':
            o_stream = storage + ['o']
            f_stream = storage + ['f']
            log.debug('Checking if streams %r and %r exist' % (f_stream, o_stream))
            if ole.exists(o_stream) and ole.get_type(o_stream) == olefile.STGTY_STREAM \
            and ole.exists(f_stream) and ole.get_type(f_stream) == olefile.STGTY_STREAM:
                form_path = '/'.join(storage)
                log.debug('Found VBA Form: %r' % form_path)
                self.vba_forms.append(storage)
        return self.vba_forms

    def extract_form_strings(self):
        """
        Extract printable strings from each VBA Form found in the file

        Iterator: yields (filename, stream_path, vba_filename, vba_code) for each VBA macro found
        If the file is OLE, filename is the path of the file.
        If the file is OpenXML, filename is the path of the OLE subfile containing VBA macros
        within the zip archive, e.g. word/vbaProject.bin.
        """
        if self.ole_file is None:
            # This may be either an OpenXML or a text file:
            if self.type == TYPE_TEXT:
                # This is a text file, return no results:
                return
            else:
                # OpenXML: recursively yield results from each OLE subfile:
                for ole_subfile in self.ole_subfiles:
                    for results in ole_subfile.extract_form_strings():
                        yield results
        else:
            # This is an OLE file:
            self.find_vba_forms()
            ole = self.ole_file
            for form_storage in self.vba_forms:
                o_stream = form_storage + ['o']
                log.debug('Opening form object stream %r' % '/'.join(o_stream))
                form_data = ole.openstream(o_stream).read()
                # Extract printable strings from the form object stream "o":
                for m in re_printable_string.finditer(form_data):
                    log.debug('Printable string found in form: %r' % m.group())
                    yield (self.filename, '/'.join(o_stream), m.group())


    def close(self):
        """
        Close all the open files. This method must be called after usage, if
        the application is opening many files.
        """
        if self.ole_file is None:
            if self.ole_subfiles is not None:
                for ole_subfile in self.ole_subfiles:
                    ole_subfile.close()
        else:
            self.ole_file.close()



class VBA_Parser_CLI(VBA_Parser):
    """
    VBA parser and analyzer, adding methods for the command line interface
    of olevba. (see VBA_Parser)
    """

    def __init__(self, filename, data=None, container=None):
        """
        Constructor for VBA_Parser_CLI.
        Calls __init__ from VBA_Parser, but handles the TypeError exception
        when the file type is not supported.

        :param filename: filename or path of file to parse, or file-like object

        :param data: None or bytes str, if None the file will be read from disk (or from the file-like object).
        If data is provided as a bytes string, it will be parsed as the content of the file in memory,
        and not read from disk. Note: files must be read in binary mode, i.e. open(f, 'rb').

        :param container: str, path and filename of container if the file is within
        a zip archive, None otherwise.
        """
        try:
            VBA_Parser.__init__(self, filename, data=data, container=container)
        except TypeError:
            # in that case, self.type=None
            pass


    def print_analysis(self, show_decoded_strings=False, deobfuscate=False):
        """
        Analyze the provided VBA code, and print the results in a table

        :param vba_code: str, VBA source code to be analyzed
        :param show_decoded_strings: bool, if True hex-encoded strings will be displayed with their decoded content.
        :param deobfuscate: bool, if True attempt to deobfuscate VBA expressions (slow)
        :return: None
        """
        # print a waiting message only if the output is not redirected to a file:
        if sys.stdout.isatty():
            print 'Analysis...\r',
            sys.stdout.flush()
        results = self.analyze_macros(show_decoded_strings, deobfuscate)
        if results:
            t = prettytable.PrettyTable(('Type', 'Keyword', 'Description'))
            t.align = 'l'
            t.max_width['Type'] = 10
            t.max_width['Keyword'] = 20
            t.max_width['Description'] = 39
            for kw_type, keyword, description in results:
                # handle non printable strings:
                if not is_printable(keyword):
                    keyword = repr(keyword)
                if not is_printable(description):
                    description = repr(description)
                t.add_row((kw_type, keyword, description))
            print t
        else:
            print 'No suspicious keyword or IOC found.'

    def print_analysis_json(self, show_decoded_strings=False):
        """
        Analyze the provided VBA code, and return the results in json format

        :param vba_code: str, VBA source code to be analyzed
        :param show_decoded_strings: bool, if True hex-encoded strings will be displayed with their decoded content.
        :return: dict
        """
        # print a waiting message only if the output is not redirected to a file:
        if sys.stdout.isatty():
            print 'Analysis...\r',
            sys.stdout.flush()
        return [dict(type=kw_type, keyword=keyword, description=description)
                for kw_type, keyword, description in self.analyze_macros(show_decoded_strings)]

    def process_file(self, show_decoded_strings=False,
                     display_code=True, global_analysis=True, hide_attributes=True,
                     vba_code_only=False, show_deobfuscated_code=False,
                     deobfuscate=False):
        """
        Process a single file

        :param filename: str, path and filename of file on disk, or within the container.
        :param data: bytes, content of the file if it is in a container, None if it is a file on disk.
        :param show_decoded_strings: bool, if True hex-encoded strings will be displayed with their decoded content.
        :param display_code: bool, if False VBA source code is not displayed (default True)
        :param global_analysis: bool, if True all modules are merged for a single analysis (default),
                                otherwise each module is analyzed separately (old behaviour)
        :param hide_attributes: bool, if True the first lines starting with "Attribute VB" are hidden (default)
        :param deobfuscate: bool, if True attempt to deobfuscate VBA expressions (slow)
        """
        #TODO: replace print by writing to a provided output file (sys.stdout by default)
        # fix conflicting parameters:
        if vba_code_only and not display_code:
            display_code = True
        if self.container:
            display_filename = '%s in %s' % (self.filename, self.container)
        else:
            display_filename = self.filename
        print '=' * 79
        print 'FILE:', display_filename
        try:
            #TODO: handle olefile errors, when an OLE file is malformed
            print 'Type:', self.type
            if self.detect_vba_macros():
                #print 'Contains VBA Macros:'
                for (subfilename, stream_path, vba_filename, vba_code) in self.extract_all_macros():
                    if hide_attributes:
                        # hide attribute lines:
                        vba_code_filtered = filter_vba(vba_code)
                    else:
                        vba_code_filtered = vba_code
                    print '-' * 79
                    print 'VBA MACRO %s ' % vba_filename
                    print 'in file: %s - OLE stream: %s' % (subfilename, repr(stream_path))
                    if display_code:
                        print '- ' * 39
                        # detect empty macros:
                        if vba_code_filtered.strip() == '':
                            print '(empty macro)'
                        else:
                            print vba_code_filtered
                    if not global_analysis and not vba_code_only:
                        #TODO: remove this option
                        raise NotImplementedError
                        print '- ' * 39
                        print 'ANALYSIS:'
                        # analyse each module's code, filtered to avoid false positives:
                        self.print_analysis(show_decoded_strings, deobfuscate)
                for (subfilename, stream_path, form_string) in self.extract_form_strings():
                    print '-' * 79
                    print 'VBA FORM STRING IN %r - OLE stream: %r' % (subfilename, stream_path)
                    print '- ' * 39
                    print form_string
                if global_analysis and not vba_code_only:
                    # analyse the code from all modules at once:
                    self.print_analysis(show_decoded_strings, deobfuscate)
                if show_deobfuscated_code:
                    print 'MACRO SOURCE CODE WITH DEOBFUSCATED VBA STRINGS (EXPERIMENTAL):\n\n'
                    print self.reveal()
            else:
                print 'No VBA macros found.'
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:  #TypeError:
            #raise
            #TODO: print more info if debug mode
            #print sys.exc_value
            # display the exception with full stack trace for debugging, but do not stop:
            traceback.print_exc()
        print ''


    def process_file_json(self, show_decoded_strings=False,
                          display_code=True, global_analysis=True, hide_attributes=True,
                          vba_code_only=False, show_deobfuscated_code=False):
        """
        Process a single file

        every "show" or "print" here is to be translated as "add to json"

        :param filename: str, path and filename of file on disk, or within the container.
        :param data: bytes, content of the file if it is in a container, None if it is a file on disk.
        :param show_decoded_strings: bool, if True hex-encoded strings will be displayed with their decoded content.
        :param display_code: bool, if False VBA source code is not displayed (default True)
        :param global_analysis: bool, if True all modules are merged for a single analysis (default),
                                otherwise each module is analyzed separately (old behaviour)
        :param hide_attributes: bool, if True the first lines starting with "Attribute VB" are hidden (default)
        """
        #TODO: fix conflicting parameters (?)

        if vba_code_only and not display_code:
            display_code = True

        result = {}

        if self.container:
            result['container'] = self.container
        else:
            result['container'] = None
        result['file'] = self.filename
        result['json_conversion_successful'] = False
        result['analysis'] = None
        result['code_deobfuscated'] = None

        try:
            #TODO: handle olefile errors, when an OLE file is malformed
            result['type'] = self.type
            macros = []
            if self.detect_vba_macros():
                for (subfilename, stream_path, vba_filename, vba_code) in self.extract_all_macros():
                    curr_macro = {}
                    if hide_attributes:
                        # hide attribute lines:
                        vba_code_filtered = filter_vba(vba_code)
                    else:
                        vba_code_filtered = vba_code

                    curr_macro['vba_filename'] = vba_filename
                    curr_macro['subfilename'] = subfilename
                    curr_macro['ole_stream'] = stream_path
                    if display_code:
                        curr_macro['code'] = vba_code_filtered.strip()
                    if not global_analysis and not vba_code_only:
                        # analyse each module's code, filtered to avoid false positives:
                        #TODO: remove this option
                        curr_macro['analysis'] = self.print_analysis_json(show_decoded_strings)
                    macros.append(curr_macro)
                if global_analysis and not vba_code_only:
                    # analyse the code from all modules at once:
                    result['analysis'] = self.print_analysis_json(show_decoded_strings)
                if show_deobfuscated_code:
                    result['code_deobfuscated'] = self.reveal()
            result['macros'] = macros
            result['json_conversion_successful'] = True
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:  #TypeError:
            #raise
            #TODO: print more info if debug mode
            #print sys.exc_value
            # display the exception with full stack trace for debugging, but do not stop:
            traceback.print_exc()

        return result


    def process_file_triage(self, show_decoded_strings=False, deobfuscate=False):
        """
        Process a file in triage mode, showing only summary results on one line.
        """
        #TODO: replace print by writing to a provided output file (sys.stdout by default)
        message = ''
        try:
            if self.type is not None:
                #TODO: handle olefile errors, when an OLE file is malformed
                if self.detect_vba_macros():
                    # print a waiting message only if the output is not redirected to a file:
                    if sys.stdout.isatty():
                        print 'Analysis...\r',
                        sys.stdout.flush()
                    self.analyze_macros(show_decoded_strings=show_decoded_strings,
                                        deobfuscate=deobfuscate)
                flags = TYPE2TAG[self.type]
                macros = autoexec = suspicious = iocs = hexstrings = base64obf = dridex = vba_obf = '-'
                if self.contains_macros: macros = 'M'
                if self.nb_autoexec: autoexec = 'A'
                if self.nb_suspicious: suspicious = 'S'
                if self.nb_iocs: iocs = 'I'
                if self.nb_hexstrings: hexstrings = 'H'
                if self.nb_base64strings: base64obf = 'B'
                if self.nb_dridexstrings: dridex = 'D'
                if self.nb_vbastrings: vba_obf = 'V'
                flags += '%s%s%s%s%s%s%s%s' % (macros, autoexec, suspicious, iocs, hexstrings,
                                             base64obf, dridex, vba_obf)
                # old table display:
                # macros = autoexec = suspicious = iocs = hexstrings = 'no'
                # if nb_macros: macros = 'YES:%d' % nb_macros
                # if nb_autoexec: autoexec = 'YES:%d' % nb_autoexec
                # if nb_suspicious: suspicious = 'YES:%d' % nb_suspicious
                # if nb_iocs: iocs = 'YES:%d' % nb_iocs
                # if nb_hexstrings: hexstrings = 'YES:%d' % nb_hexstrings
                # # 2nd line = info
                # print '%-8s %-7s %-7s %-7s %-7s %-7s' % (self.type, macros, autoexec, suspicious, iocs, hexstrings)
            else:
                # self.type==None
                # file type not OLE nor OpenXML
                flags = '?'
                message = 'File format not supported'
        except KeyboardInterrupt:
            # do not ignore exceptions when the user presses Ctrl+C/Pause:
            raise
        except:
            # another error occurred
            #raise
            #TODO: print more info if debug mode
            #TODO: distinguish real errors from incorrect file types
            flags = '!ERROR'
            message = sys.exc_value
        line = '%-12s %s' % (flags, self.filename)
        if message:
            line += ' - %s' % message
        print line

        # t = prettytable.PrettyTable(('filename', 'type', 'macros', 'autoexec', 'suspicious', 'ioc', 'hexstrings'),
        #     header=False, border=False)
        # t.align = 'l'
        # t.max_width['filename'] = 30
        # t.max_width['type'] = 10
        # t.max_width['macros'] = 6
        # t.max_width['autoexec'] = 6
        # t.max_width['suspicious'] = 6
        # t.max_width['ioc'] = 6
        # t.max_width['hexstrings'] = 6
        # t.add_row((filename, ftype, macros, autoexec, suspicious, iocs, hexstrings))
        # print t


#=== MAIN =====================================================================

def main():
    """
    Main function, called when olevba is run from the command line
    """
    global log
    DEFAULT_LOG_LEVEL = "warning" # Default log level
    LOG_LEVELS = {
        'debug':    logging.DEBUG,
        'info':     logging.INFO,
        'warning':  logging.WARNING,
        'error':    logging.ERROR,
        'critical': logging.CRITICAL
        }

    usage = 'usage: %prog [options] <filename> [filename2 ...]'
    parser = optparse.OptionParser(usage=usage)
    # parser.add_option('-o', '--outfile', dest='outfile',
    #     help='output file')
    # parser.add_option('-c', '--csv', dest='csv',
    #     help='export results to a CSV file')
    parser.add_option("-r", action="store_true", dest="recursive",
                      help='find files recursively in subdirectories.')
    parser.add_option("-z", "--zip", dest='zip_password', type='str', default=None,
                      help='if the file is a zip archive, open all files from it, using the provided password (requires Python 2.6+)')
    parser.add_option("-f", "--zipfname", dest='zip_fname', type='str', default='*',
                      help='if the file is a zip archive, file(s) to be opened within the zip. Wildcards * and ? are supported. (default:*)')
    # output mode; could make this even simpler with add_option(type='choice') but that would make
    # cmd line interface incompatible...
    modes = optparse.OptionGroup(parser, title='Output mode (mutually exclusive)')
    modes.add_option("-t", '--triage', action="store_const", dest="output_mode",
                     const='triage', default='unspecified',
                     help='triage mode, display results as a summary table (default for multiple files)')
    modes.add_option("-d", '--detailed', action="store_const", dest="output_mode",
                     const='detailed', default='unspecified',
                     help='detailed mode, display full results (default for single file)')
    modes.add_option("-j", '--json', action="store_const", dest="output_mode",
                     const='json', default='unspecified',
                     help='json mode, detailed in json format (never default)')
    parser.add_option_group(modes)
    parser.add_option("-a", '--analysis', action="store_false", dest="display_code", default=True,
                      help='display only analysis results, not the macro source code')
    parser.add_option("-c", '--code', action="store_true", dest="vba_code_only", default=False,
                      help='display only VBA source code, do not analyze it')
    parser.add_option("--decode", action="store_true", dest="show_decoded_strings",
                      help='display all the obfuscated strings with their decoded content (Hex, Base64, StrReverse, Dridex, VBA).')
    parser.add_option("--attr", action="store_false", dest="hide_attributes", default=True,
                      help='display the attribute lines at the beginning of VBA source code')
    parser.add_option("--reveal", action="store_true", dest="show_deobfuscated_code",
                      help='display the macro source code after replacing all the obfuscated strings by their decoded content.')
    parser.add_option('-l', '--loglevel', dest="loglevel", action="store", default=DEFAULT_LOG_LEVEL,
                            help="logging level debug/info/warning/error/critical (default=%default)")
    parser.add_option('--deobf', dest="deobfuscate", action="store_true", default=False,
                            help="Attempt to deobfuscate VBA expressions (slow)")

    (options, args) = parser.parse_args()

    # Print help if no arguments are passed
    if len(args) == 0:
        print __doc__
        parser.print_help()
        sys.exit()

    # provide info about tool and its version
    if options.output_mode == 'json':
        json_results = [dict(script_name='olevba', version=__version__,
                             url='http://decalage.info/python/oletools',
                             type='MetaInformation'), ]
    else:
        print 'olevba %s - http://decalage.info/python/oletools' % __version__

    logging.basicConfig(level=LOG_LEVELS[options.loglevel], format='%(levelname)-8s %(message)s')
    # enable logging in the modules:
    log.setLevel(logging.NOTSET)

    # Old display with number of items detected:
    # print '%-8s %-7s %-7s %-7s %-7s %-7s' % ('Type', 'Macros', 'AutoEx', 'Susp.', 'IOCs', 'HexStr')
    # print '%-8s %-7s %-7s %-7s %-7s %-7s' % ('-'*8, '-'*7, '-'*7, '-'*7, '-'*7, '-'*7)

    # with the option --reveal, make sure --deobf is also enabled:
    if options.show_deobfuscated_code and not options.deobfuscate:
        options.deobfuscate = True

    # Column headers (do not know how many files there will be yet, so if no output_mode
    # was specified, we will print triage for first file --> need these headers)
    if options.output_mode in ('triage', 'unspecified'):
        print '%-12s %-65s' % ('Flags', 'Filename')
        print '%-12s %-65s' % ('-' * 11, '-' * 65)

    previous_container = None
    count = 0
    container = filename = data = None
    vba_parser = None
    for container, filename, data in xglob.iter_files(args, recursive=options.recursive,
                                                      zip_password=options.zip_password, zip_fname=options.zip_fname):
        # ignore directory names stored in zip files:
        if container and filename.endswith('/'):
            continue
        # Open the file
        vba_parser = VBA_Parser_CLI(filename, data=data, container=container)
        if options.output_mode == 'detailed':
            # fully detailed output
            vba_parser.process_file(show_decoded_strings=options.show_decoded_strings,
                         display_code=options.display_code, global_analysis=True, #options.global_analysis,
                         hide_attributes=options.hide_attributes, vba_code_only=options.vba_code_only,
                         show_deobfuscated_code=options.show_deobfuscated_code,
                         deobfuscate=options.deobfuscate)
        elif options.output_mode in ('triage', 'unspecified'):
            # print container name when it changes:
            if container != previous_container:
                if container is not None:
                    print '\nFiles in %s:' % container
                previous_container = container
            # summarized output for triage:
            vba_parser.process_file_triage(show_decoded_strings=options.show_decoded_strings,
                                           deobfuscate=options.deobfuscate)
        elif options.output_mode == 'json':
            json_results.append(
                vba_parser.process_file_json(show_decoded_strings=options.show_decoded_strings,
                         display_code=options.display_code, global_analysis=True, #options.global_analysis,
                         hide_attributes=options.hide_attributes, vba_code_only=options.vba_code_only,
                         show_deobfuscated_code=options.show_deobfuscated_code))
        else:  # (should be impossible)
            raise ValueError('unexpected output mode: "{0}"!'.format(options.output_mode))
        count += 1
    if options.output_mode == 'triage':
        print '\n(Flags: OpX=OpenXML, XML=Word2003XML, MHT=MHTML, TXT=Text, M=Macros, ' \
              'A=Auto-executable, S=Suspicious keywords, I=IOCs, H=Hex strings, ' \
              'B=Base64 strings, D=Dridex strings, V=VBA strings, ?=Unknown)\n'

    if count == 1 and options.output_mode == 'unspecified':
        # if options -t, -d and -j were not specified and it's a single file, print details:
        vba_parser.process_file(show_decoded_strings=options.show_decoded_strings,
                         display_code=options.display_code, global_analysis=True, #options.global_analysis,
                         hide_attributes=options.hide_attributes, vba_code_only=options.vba_code_only,
                         show_deobfuscated_code=options.show_deobfuscated_code,
                         deobfuscate=options.deobfuscate)

    if options.output_mode == 'json':
        json_options = dict(check_circular=False, indent=4, ensure_ascii=False)

        # json.dump[s] cannot deal with unicode objects that are not properly
        # encoded --> encode in own function:
        json_results = json2ascii(json_results)
        #print_json(json_results)

        # if False:  # options.outfile: # (option currently commented out)
        #     with open(outfile, 'w') as write_handle:
        #         json.dump(write_handle, **json_options)
        # else:
        print json.dumps(json_results, **json_options)


if __name__ == '__main__':
    main()

# This was coded while listening to "Dust" from I Love You But I've Chosen Darkness

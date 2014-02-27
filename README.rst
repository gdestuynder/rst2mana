========
rst2mana
========


Introduction
------------

rst2mana is a Python script which grabs RST (ReStructuredText) pages from a GIT repository and sends them to Confluence as an HTML macro.
In general, this is meant to be used as a GIT hook (post-commit).
The script will grab the RST file, convert it to HTML, then send it to Confluence via XML-RPC, using storePage()'s confluence function.
Oh, and why Mana? This is the name of the Confluence instance at Mozilla.

By default, the RST files are stored in ./docs/ and you can use any directory structure you like - it will be replicated in confluence.

Use rst2mana.py -d for debugging messages.

Safety measures
---------------

* rst2mana will refuse to send new pages if the major version of Confluence changes for a higher version.
* rst2mana will refuse to send a new page if a page already exists and doesn't have a specific label associated.
* rst2mana will refuse to send a new page if the RST syntax check fails at the WARNING level while converting the page (INFO error will be ignored).
* rst2mana will refuse to overwrite a page if it has already written the same page during the same rst2mana run. That's because Confluence does not allow duplicate page names, even if they're under different "directories". In fact, Confluence has a flat view per space.

Requirements
------------

* Python with xmlrpclib, docutils and pygments libraries.
* Confluence wiki - with XMLRPC enabled.

Configuration
-------------

* cp config.py.inc config.py
* edit config.py to your liking
* populate ./docs/ or the path you have setup with rst documents
* ./rst2mana
* profit!

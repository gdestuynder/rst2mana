#!/usr/bin/env python
# -*- coding: utf8 -*-
# Safety: Will fail to update pages if confluence major version is higher than this.
CONFLUENCE_MAJOR_COMPAT=5
# Safety: Only pages that do not exist, or pages with this label will be updated.
LABEL="from-git"

# Your confluence/LDAP login/pass
USER=""
PASS=""

URL="https://"+USER+":"+PASS+"@mana.mozilla.org/wiki/rpc/xmlrpc"

# The space to modify. Be careful here.
# User spaces are prefixed with a '~'. For example, my space is:
# '~gdestuynder@mozilla.com'
SPACE=''
# This is the space's homepage. It's needed to create new page/directories that will be listed in your homepage by default.
# Generally Confluence default is "Home" or "<full username>’s Home" (note that this is not a standard quote character).
HOMEPAGE='Home'

# Leave './' for current directory.
DOCS_PATH="./docs/"

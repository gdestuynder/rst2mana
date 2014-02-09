#!/usr/bin/env python2
# vim: set ts=4 sw=4 noexpandtab:
# -*- coding: <encoding name> -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
# Author: gdestuynder@mozilla.com
#
# Confluence API:
# https://developer.atlassian.com/display/CONFDEV/Remote+Confluence+Methods

import os
import sys
import getopt
import copy
from config import *
try:
	import xmlrpclib
	import pygments
	import docutils
	from docutils.core import publish_parts
except ImportError:
	print("Missing required module: %s" % (e))

class ConfluenceRPC:
	def __init__(self, user, passwd, space, label, homepage, url):
		self.server = xmlrpclib.ServerProxy(url)
		self.connection = self.server.confluence2
		self.token = self.connection.login(user, passwd)
		self.label = label
		self.space = space
		self.serverinfo = self.connection.getServerInfo(self.token)
		self.debug("Connected, server info: "+self.serverinfo.__str__())
		self.debug("Using space: \'%s\' and matching label: \'%s\'" % (self.space, self.label))
		self.default_page = {'content': '', 'title': '', 'space': self.space}
		self.sanity_checks()
		self.homepage = self.getPage(homepage)

	def sanity_checks(self):
		if CONFLUENCE_MAJOR_COMPAT > self.serverinfo['majorVersion']:
			fatal("Confluence version compatibility not tested")
		if (self.connection.getSpaceStatus(self.token, self.space) != "CURRENT"):
			fatal("Space %s isn't current" % self.space)

	def createPage(self, rootdir, filename):
		pagename = filename[:-4]
# Fixup rootdir to look like a page name so that we can retrieve it from Confluence.
# E.g. ./blah/bleh would be "bleh" in Confluence, and that's the parent of the page we want to create, and we need to retrieve that
# so that the page we create has the same parent in GIT and in Confluence.
		upper_rootdir = os.path.dirname(rootdir+"/").split('/')[-1]
		if upper_rootdir.startswith("./"):
			upper_rootdir = upper_rootdir[2:]
		elif upper_rootdir[0] == '/':
			upper_rootdir = upper_rootdir[1:]

		parentpage = self.getPage(upper_rootdir)
		if parentpage == None:
			fatal("Can't find parent page for %s (parent should be %s as expanded from %s). That really isn't supposed to happen. Sorry." % (pagename, upper_rootdir, rootdir))

		self.debug("Attempting to create page: %s (from  %s)" % (pagename, os.path.join(rootdir, filename)))
		with open(os.path.join(rootdir, filename)) as p:
			html = self.rst2html(p.read())
		content = self.getMacroHTML(html)
		self.storePage(pagename, content, parentid=parentpage['id'])

	def createDirectory(self, directory):
		self.debug("Attempting to create \"directory\": %s" % directory)
# This is a "Show all children pages" macro.
		content = '<p><ac:structured-macro ac:name="children"><ac:parameter ac:name="all">true</ac:parameter></ac:structured-macro></p>'
		self.storePage(directory, content)

	def storePage(self, pagename, content, parentid=None):
		page = self.getPage(pagename)
		if page == None:
			page = self.default_page
			page['title'] = pagename

# If page doesn't exist yet (no id), then create it add add the label
# Else check if we're allowed to update it (i.e. has the label)
		if not page.has_key('id'):
			page = self.createPageAndLabel(page)
		else:
			if not self.validateLabel(page):
				return

		new_page = copy.copy(page)
		new_page['content'] = content
		if not self.comparePages(page, new_page):
			self.msg("Creating/updating page %s" % new_page['title'])
			if parentid != None:
				new_page['parentId'] = parentid
			self.connection.storePage(self.token, new_page)
		del(page)

	def comparePages(self, p1, p2):
		"""Returns True if pages are identical, else False. It's 'just' a CRC32 as this is compared for caching purposes only."""
		if (hash(p1['content']) == hash(p2['content'])):
			self.debug("Pages '%s' and '%s' identical, no update needed" % (p1['title'], p2['title']))
			return True
		return False

	def rst2html(self, data):
		defaults={'file_insertion_enabled': 0,
					'raw_enabled': 0,
					'halt_level': 2,
				}
		try:
			return publish_parts(data, writer_name='html', settings_overrides=defaults)['html_body']
		except docutils.utils.SystemMessage:
			fatal("Parsing ReStructuredText failed, invalid syntax.")

	def getMacroHTML(self, html):
		"""Creates a confluence HTML macro"""
		return '<ac:structured-macro ac:name="html"><ac:plain-text-body><![CDATA['+html+']]></ac:plain-text-body></ac:structured-macro>'

	def validateLabel(self, page):
		for label in self.connection.getLabelsById(self.token, page['id']):
			if label['name'] == self.label:
				return True
		self.debug("No label found for page %s, skipping" % page['title'])
		return False

	def createPageAndLabel(self, page):
		self.debug("Attempting to create new page and label: %s" % page['title'])
		page['parentId'] = self.homepage['id']
		self.connection.storePage(self.token, page)
		real_page = self.getPage(page['title'])
		self.connection.addLabelByName(self.token, self.label, real_page['id'])
		return real_page

	def getPage(self, pagename):
		try:
			return self.connection.getPage(self.token, self.space, pagename)
		except xmlrpclib.Fault, f:
			self.debug("Page couldn't be retrieved, I'll assume it doesn't exist: %s" % f)
			return None
		
	def logout(self):
		self.connection.logout(self.token)
		self.debug("Logged out.")

	def debug(self, buf):
		if DEBUG:
			print("++ %s" % buf)

	def fatal(self, buf):
		sys.stderr.write("Fatal error has occured: %s\n" % buf)
		self.logout()

	def msg(self, buf):
		print("RST2MANA: %s" % buf)

def debug(buf):
	if DEBUG:
		print("+ %s" % buf)

def fatal(buf):
	sys.stderr.write("Fatal error has occured: %s\n" % buf)
	sys.exit(1)
	
def usage():
	print("""USAGE:	%s [-d]
	-h			this help message.
	-d, --debug		enable debug messages.

This program converts ReStructuredText documents to HTML and upload them to Confluence. 
It is generally run from a Git post-commit hook.""" % sys.argv[0])
	sys.exit(2)

def main(argv):
	global DEBUG
	DEBUG=False

	try:
		opts, args = getopt.getopt(argv, "h:d", ["debug"])
	except getopt.GetoptError:
		usage()

	for opt, arg, in opts:
		if opt == '-h':
			usage()
		elif opt in ("-d", "--debug"):
			DEBUG=True

	try:
		os.chdir(DOCS_PATH)
	except OSError:
		fatal("Directory not found %s", DOCS_PATH)

	c = ConfluenceRPC(USER, PASS, SPACE, LABEL, HOMEPAGE, URL)

	pages_updated = []

	for root, dirs, files in os.walk(os.curdir):
		files = [f for f in files if not (f[0] == '.' or f[-4:] != '.rst')]
		dirs[:] = [d for d in dirs if not d[0] == '.']
# Create all "directories" in the wiki
		for d in dirs:
			if (d != ''):
				if d in pages_updated:
					fatal("Page %s already exists. Please a different directory name. Confluence requires unique page names!" % f)
				else:
					c.createDirectory(d)
					pages_updated += [d]
# Create all pages inside directories
		for f in files:
			if f in pages_updated:
				fatal("Page %s already exists. Please use a different name. Confluence requires unique page names!" % f)
			else:
				c.createPage(root, f)
				pages_updated += [f]

if __name__ == '__main__':
	main(sys.argv[1:])

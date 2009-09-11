#
# YamlFSSource.py - New-style YAML/Markdown file-system data source
# Copyright (C) 2009 Tony Garnock-Jones <tonyg@kcbbs.gen.nz>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import Gyre
import os
import string
import yaml
import markdown2
import re

def escape_md(str):
    return (str
            # To avoid markdown <em> and <strong>:
            .replace('*', markdown2.g_escape_table['*'])
            .replace('_', markdown2.g_escape_table['_']))

class ExtendedMarkdown(markdown2.Markdown):
    wikiish_link = re.compile(r'\[\[([^]|]+)(\|([^]|]+))?\]\]')
    def __init__(self, mode):
        if mode == 'script':
            self.link_base = Gyre.config.script_url
        elif mode == 'snapshot':
            self.link_base = Gyre.config.snapshot_url
        else:
            raise Exception("Unsupported gyre mode", mode)
        self.link_base = escape_md(self.link_base + '/_STORY_')
        markdown2.Markdown.__init__(self, extras = ["footnotes", "link-patterns"])

    def _do_link_patterns(self, text):
        replacements = []
        for match in self.wikiish_link.finditer(text):
            replacements.append((match.span(), match.group(1), match.group(3)))
        replacements.reverse()
        for (start, end), href, label in replacements:
            href = escape_md(href)
            if label is None: label = href
            escaped_href = href.replace('"', '&quot;')  # b/c of attr quote
            text = text[:start] + \
                   ('<a href="%s.html">%s</a>' % \
                    (os.path.join(self.link_base, escaped_href), label)) + \
                   text[end:]
        return text

class YamlFSSource:
    def __init__(self, contentdir):
        self.contentdir = contentdir
        self.template_headers_cache = {}

    def _load_file(self, filepath):
        f = open(filepath)
        loader = yaml.Loader(f)
        headers = loader.get_data()
        body = loader.prefix(1000000000).strip('\0').strip() # yuck
        f.close()
        return (headers, body)

    def _template_headers(self, dirname):
        if dirname not in self.template_headers_cache:
            filepath = os.path.join(dirname, '__template__')
            try:
                self.template_headers_cache[dirname] = self._load_file(filepath)[0]
            except IOError:
                self.template_headers_cache[dirname] = {}
        return self.template_headers_cache[dirname]

    def _visit_story(self, query, dirname, name):
        filepath = os.path.join(dirname, name + '.' + Gyre.config.file_extension)
        try:
            s = os.stat(filepath)
        except OSError:
            return

        story = Gyre.Entity()
        story.mtime = s.st_mtime

        (headers, body) = self._load_file(filepath)
        for (key, val) in self._template_headers(dirname).items(): setattr(story, key.lower(), val)
        for (key, val) in headers.items(): setattr(story, key.lower(), val)
        body = ExtendedMarkdown(query.mode).convert(body)

        story.mtime = int(story.mtime)
        categorystr = dirname[len(self.contentdir) + 1:]
        if categorystr:
            story.category = string.split(categorystr, '/')
        else:
            story.category = []
        story.body = body

        uid = list(story.category)
        uid.append(name)
        story.id = string.join(uid, '/')

        Gyre.config.store.update(story)

    def _visit(self, query, dirname, names):
        for name in names:
            if name.endswith('.' + Gyre.config.file_extension):
                choplen = len(Gyre.config.file_extension) + 1
                self._visit_story(query, dirname, name[:-choplen])

    def updateForQuery(self, query):
        category = os.path.join(self.contentdir, *query.category)
        os.path.walk(category, self._visit, query)

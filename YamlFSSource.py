#
# YamlFSSource.py - New-style YAML file-system data source
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

    def _canonical_dirname(self, dirname):
        if dirname.startswith(self.contentdir):
            dirname = dirname[len(self.contentdir):]
        if dirname and dirname[0] == '/':
            dirname = dirname[1:]
        return dirname

    def _template_headers(self, uncanonicalized_dirname):
        dirname = self._canonical_dirname(uncanonicalized_dirname)
        if dirname not in self.template_headers_cache:
            filepath = os.path.join(uncanonicalized_dirname, '__template__')
            if dirname:
                parent = self._template_headers(os.path.dirname(uncanonicalized_dirname))
            else:
                parent = Gyre.config.protostory
            try:
                p = self._load_file(filepath)[0]
            except IOError:
                p = {}
            self.template_headers_cache[dirname] = Gyre.Entity(_parent = parent, _props = p)
        return self.template_headers_cache[dirname]

    def _visit_story(self, dirname, name):
        filepath = os.path.join(dirname, name + '.' + Gyre.config.file_extension)
        try:
            s = os.stat(filepath)
        except OSError:
            return

        story = Gyre.Entity(self._template_headers(dirname))
        story.mtime = s.st_mtime

        (headers, body) = self._load_file(filepath)
        for (key, val) in headers.items(): setattr(story, key.lower(), val)

        story.mtime = int(story.mtime)
        categorystr = dirname[len(self.contentdir) + 1:]
        if categorystr:
            story.category = string.split(categorystr, '/')
        else:
            story.category = []
        story.body = body

        if not story.id:
            uid = list(story.category)
            uid.append(name)
            story.id = string.join(uid, '/')

        Gyre.config.store.update(story)

    def updateStore(self):
        def visit(arg, dirname, names):
            for name in names:
                if name.endswith('.' + Gyre.config.file_extension):
                    choplen = len(Gyre.config.file_extension) + 1
                    self._visit_story(dirname, name[:-choplen])
        os.path.walk(self.contentdir, visit, None)

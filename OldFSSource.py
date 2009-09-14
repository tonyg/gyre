#
# OldFSSource.py - Old-style basic file-system data source
# Copyright (C) 2004 - 2009 Tony Garnock-Jones <tonyg@kcbbs.gen.nz>
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
import rfc822

class OldFSSource:
    def __init__(self, contentdir):
        self.contentdir = contentdir

    def _visit_story(self, dirname, name):
        filepath = os.path.join(dirname, name + '.' + Gyre.config.file_extension)
        try:
            s = os.stat(filepath)
        except OSError:
            return

        story = Gyre.Entity(Gyre.config.protostory)
        story.mtime = s.st_mtime

        f = open(filepath)
        headers = rfc822.Message(f)
        for (key, val) in headers.items(): setattr(story, key.lower(), val)
        body = f.read()
        f.close()

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

    def updateStore(self):
        def visit(arg, dirname, names):
            for name in names:
                if name.endswith('.' + Gyre.config.file_extension):
                    choplen = len(Gyre.config.file_extension) + 1
                    self._visit_story(dirname, name[:-choplen])
        os.path.walk(self.contentdir, visit, None)

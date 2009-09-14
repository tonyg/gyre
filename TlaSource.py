#
# TlaSource.py - A source of stories backed by a GNU Arch changelog
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
import time
import cgi
import string
import rfc822

class TlaSource:
    def __init__(self, tlapath, category):
        self.tlapath = tlapath
        self.category = category
        pass

    def updateStore(self):
        patchnames = map(string.strip, os.popen(self.tlapath + ' logs').readlines())
        stories = []
        for patch in patchnames:
            p = os.popen(self.tlapath + ' cat-log ' + patch)
            msg = rfc822.Message(p)
            full_tla_version = msg['Archive'] + '/' + msg['Revision']
            body = p.read().strip()
            body = cgi.escape(body)
            body = body.replace('\n\n', '\n\n<p> ')
            if not body:
                body = '(no detail message)'

            story = Gyre.Entity()
            story.mtime = int(time.mktime(time.strptime(msg['Standard-date'],
                                                        '%Y-%m-%d %H:%M:%S GMT')))
            story.subject = cgi.escape(msg['Summary'])
            story.body = body
            story.category = self.category
            story.id = msg['Revision']

            for header in ['Archive', 'Revision', 'Creator']:
                setattr(story, header.lower(), msg[header])
            story.full_tla_version = full_tla_version
            story.full_tla_version_span = \
                '<span class="tla-version">' + full_tla_version + '</span>'

            stories.append(story)

        for story in stories:
            Gyre.config.store.update(story)

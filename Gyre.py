#
# Gyre.py - Core of CMS
# Copyright (C) 2004 Tony Garnock-Jones <tonyg@kcbbs.gen.nz>
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

import sys
import os
import string
import time
import re
import traceback
import cgi
import cgitb; cgitb.enable()

import plugins

def maybe_wrap_dict(x):
    if isinstance(x, dict):
        return Entity(defaultprops = x)
    else:
        return x

class Entity:
    def __init__(self, parent=None, defaultprops=None):
        self.__dict__['_parent'] = parent
        self.__dict__['_props'] = defaultprops or {}
    def __getattr__(self, name):
        if name.startswith('_'): raise AttributeError, name
        if self._props.has_key(name): return maybe_wrap_dict(self._props[name])
        if self._parent is None: return ''
        return self._parent.__getattr__(name)
    def __setattr__(self, key, val):
        self._props[key] = val
    def DICT(self):
        if self._parent is None: x = {}
        else: x = self._parent.DICT()
        x.update(self._props)
        return x

class Store:
    def __init__(self):
        self.stories = {}
        self.category_root = ({}, [])
        self.pluginModules = []
        self.flavours = {}

        self.missing_flavour = Entity()
        self.missing_flavour.story = ''
        self.missing_flavour.headers = 'Content-type: text/plain\r\n'
        self.missing_flavour.document = 'Unknown flavour'

    def _load_plugins(self):
        self.pluginModules = []
        for filename in os.listdir(plugins.__path__[0]):
            if filename.startswith('_') or filename.startswith('.') or not filename.endswith('.py'):
                continue
            modname = filename[:-3]     # remove .py
            mod = __import__('plugins.' + modname)
            if hasattr(mod, modname):
                mod = getattr(mod, modname)
                if hasattr(mod, 'plugin_order'):
                    order = mod.plugin_order
                else:
                    order = 0
                self.pluginModules.append((order, mod))
        self.pluginModules.sort(lambda (a, aa), (b, bb): a - b)

    def getPlugins(self, name):
        result = []
        for (order, mod) in self.pluginModules:
            if hasattr(mod, name):
                result.append(getattr(mod, name))
        return result

    def _load_flavours(self):
        self.flavours = {}
        for flavourdir in config.flavourdirs:
            for filename in os.listdir(flavourdir):
                if filename.startswith('.'): continue
                filepath = os.path.join(flavourdir, filename)
                (flavourprop, flavourname) = string.split(filename, '.')
                if not self.flavours.has_key(flavourname):
                    self.flavours[flavourname] = Entity()
                f = open(filepath)
                setattr(self.flavours[flavourname], flavourprop, f.read())
                f.close()

    def load(self):
        self._load_plugins()
        self._load_flavours()
        pass

    def save(self):
        pass

    def getFlavour(self, flavour):
        if self.flavours.has_key(flavour):
            return self.flavours[flavour]
        else:
            return self.missing_flavour

    def getCategories(self):
        acc = [[]]
        def collect(prefix, idx):
            for (cat, (newidx, storyids)) in idx.items():
                newprefix = prefix + [cat]
                acc.append(newprefix)
                collect(newprefix, newidx)
        collect([], self.category_root[0])
        return acc

    def getStoryIds(self):
        return self.stories.keys()

    def getStoryCount(self):
        return len(self.stories)

    def prepareForQuery(self, query):
        if query.storyid:
            return
        else:
            (idx, stories) = self.category_root
            for cat in query.category:
                if not idx.has_key(cat):
                    return
                (idx, stories) = idx[cat]
            idx.clear()
            del stories[0:]

    def update(self, story):
        for processor in self.getPlugins('preprocess'): story = processor(story)
        self.stories[story.id] = story
        (idx, stories) = self.category_root
        for cat in story.category:
            if not idx.has_key(cat):
                idx[cat] = ({}, [])
            (idx, stories) = idx[cat]
        stories.append(story.id)

    def getStory(self, id):
        if self.stories.has_key(id): return self.stories[id]
        raise KeyError, ('No such story', id)

    def accumulate_tree(self, acc, outer_idx):
        for (idx, stories) in outer_idx.values():
            self.accumulate_tree(acc, idx)
            acc.extend(stories)

    def query(self, query):
        if query.storyid:
            return [query.storyid]
        acc = []
        (idx, stories) = self.category_root
        for cat in query.category:
            if idx.has_key(cat):
                (idx, stories) = idx[cat]
            else:
                (idx, stories) = ({}, [])
                break
        acc.extend(stories)
        self.accumulate_tree(acc, idx)
        return acc

config = Entity()
config.version = '0.0.1'
config.language = 'en'
config.flavourdirs = ['flavours']
config.file_extension = 'txt'
config.default_flavour = 'html'
config.store = Store()
config.sources = []
config.snapshot_flavours = ['html', 'rss', 'atom']
config.verbose_snapshot = 1
if os.environ.has_key('SCRIPT_NAME'):
    config.base_url = os.path.dirname(os.environ['SCRIPT_NAME'])
else:
    config.base_url = 'file://' + os.getcwd()

config.protostory = Entity()
config.protostory.renderers = ['renderstory', 'markdown']

def add_source(source):
    config.sources.append(source)

exprre = re.compile('<\?((\?[^>]|[^?])+)\?>')
def template(tmpl, env):
    if isinstance(env, Entity): env = env.DICT()
    acc = []
    while 1:
        m = exprre.search(tmpl)
        if not m:
            acc.append(tmpl)
            break
        acc.append(tmpl[:m.start()])
        try:
            acc.append(unicode(eval(m.group(1), sys.modules, env)))
        except:
            acc.append(cgi.escape('<Exception:\r\n' +
                                  string.join(traceback.format_exception(*sys.exc_info()), '') +
                                  '\r\n>'))
        tmpl = tmpl[m.end():]
    return string.join(acc, '')

def renderStories(query, url):
    storyids = config.store.query(query)
    for filter in config.store.getPlugins('filterQueryIds'): filter(query, storyids)

    docenvt = Entity()
    docenvt.flavourname = query.flavour
    docenvt.flavour = config.store.getFlavour(query.flavour)
    docenvt.query = query
    docenvt.stories = map(config.store.getStory, storyids)
    docenvt.config = config
    docenvt.url = url

    def cmp_story(sa, sb):
        if (sa.float == 'yes') ^ (sb.float == 'yes'):
            if sa.float == 'yes': return -1
            return 1
        else:
            return sb.mtime - sa.mtime
    docenvt.stories.sort(cmp_story)
    docenvt.story_count = len(docenvt.stories)
    if docenvt.stories:
        docenvt.mtime = docenvt.stories[0].mtime
    else:
        docenvt.mtime = 0
    docenvt.mtime3339 = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(docenvt.mtime))
    for filter in config.store.getPlugins('filterQueryStories'): filter(query, docenvt.stories)

    content_entries = []
    for story in docenvt.stories:
        storyenvt = Entity(docenvt)
        storyenvt.story = story
        for prerender_story in config.store.getPlugins('prerender_story'):
            content_entries.extend(prerender_story(query, docenvt, story, storyenvt))
        entry = template(docenvt.flavour.story, storyenvt)
        content_entries.append(entry)
    docenvt.contents = string.join(content_entries, '')

    for prerender_document in config.store.getPlugins('prerender_document'):
        prerender_document(query, docenvt)

    return (template(docenvt.flavour.headers, docenvt),
            template(docenvt.flavour.document, docenvt))

def query_for(**kw):
    query = Entity()
    query.dialect = 'gyre-plain'
    for (k, v) in kw.items(): setattr(query, k, v)
    return query

def snapshotRender(query):
    if query.storyid:
        path = os.path.join(config.snapshot_dir, '_STORY_', query.storyid + '.' + query.flavour)
    else:
        if query.skip:
            pfx = 'index-skip' + str(query.skip) + '.'
        else:
            pfx = 'index.'
        path = os.path.join(*([config.snapshot_dir] + query.category + [pfx + query.flavour]))
    try:
        os.makedirs(os.path.dirname(path), 0755)
    except:
        pass
    (headers, document) = renderStories(query, config.snapshot_url)
    if config.verbose_snapshot:
        print 'Writing %s...' % path
    f = open(path, 'w', 0644)
    f.write(document.encode('utf-8'))
    f.close()

def snapshot_main():
    top_query = query_for(category = [], mode = 'snapshot')
    config.store.load()
    config.store.prepareForQuery(top_query)
    for source in config.sources: source.updateForQuery(top_query)
    for flavour in config.snapshot_flavours:
        for category in config.store.getCategories():
            if config.num_entries:
                for skip in range(0, config.store.getStoryCount(), config.num_entries):
                    snapshotRender(query_for(flavour = flavour, category = category,
                                             mode = 'snapshot', skip = skip))
            else:
                snapshotRender(query_for(flavour = flavour, category = category,
                                         mode = 'snapshot'))
        for storyid in config.store.getStoryIds():
            snapshotRender(query_for(flavour = flavour, storyid = storyid, mode = 'snapshot'))
    config.store.save()

def cgi_main():
    path = string.split(os.environ.get('PATH_INFO', ''), '/')
    category = []
    flavour = config.default_flavour
    for elt in path:
        if not elt or elt.startswith('.') or elt.find('\0') != -1 or elt.find('\\') != -1:
            continue
        category.append(elt)
    if category and category[0] == '_STORY_':
        pos = category[-1].rfind('.')
        if pos != -1:
            flavour = category[-1][pos + 1:]
            category[-1] = category[-1][:pos]
        query = query_for(flavour = flavour, storyid = string.join(category[1:], '/'), mode = 'script')
    else:
        if category and category[-1].startswith('index.'):
            flavour = category[-1][6:]
            category.pop()
        query = query_for(flavour = flavour, category = category, mode = 'script')

    for (k, v) in cgi.parse_qs(os.environ.get('QUERY_STRING', '')).items(): setattr(query, k, v[0])
    config.store.load()
    config.store.prepareForQuery(query)
    for source in config.sources: source.updateForQuery(query)
    (headers, document) = renderStories(query, config.script_url)
    sys.stdout.write(headers)
    sys.stdout.write('\r\n')
    sys.stdout.write(document.encode('utf-8'))
    config.store.save()

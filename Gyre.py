#
# Gyre.py - Core of CMS
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

import sys
import os
import string
import time
import re
import traceback
import yaml
import cgi
import cgitb; cgitb.enable()

class Absent:
    def __init__(self, name):
        self.name = name
    def __nonzero__(self):
        return False
    def __str__(self):
        return ''
    def __repr__(self):
        return 'Absent(%s)' % (self.name,)

class Entity:
    def __init__(self, _parent=None, _props=None, **kw):
        self.__dict__['_parent'] = _parent
        self.__dict__['_props'] = _props or {}
        self.__dict__['_props'].update(kw)
    def __getattr__(self, name):
        if name.startswith('_'): raise AttributeError, name
        if self._props.has_key(name):
            v = self._props[name]
            return Entity(_props = v) if isinstance(v, dict) else v
        if self._parent is None: return Absent(name)
        return getattr(self._parent, name)
    def __setattr__(self, key, val):
        self._props[key] = val
    def DICT(self):
        if self._parent is None: x = {}
        elif isinstance(self._parent, Entity): x = self._parent.DICT()
        elif isinstance(self._parent, dict): x = dict(self._parent)
        else: x = dict(self._parent.__dict__)
        x.update(self._props)
        return x

class Store:
    def __init__(self):
        self.stories = {}
        self.templates = {}
        self.sources = []
        self.indices = []
        self.preprocessors = []

    def _load_templates(self):
        self.templates = {}
        for templatedir in config.templatedirs:
            for filename in os.listdir(templatedir):
                if filename.startswith('.'): continue
                filepath = os.path.join(templatedir, filename)
                f = open(filepath)
                self.templates[filename] = f.read()
                f.close()

    def load(self):
        self._load_templates()
        for source in self.sources: source.updateStore()

    def save(self):
        pass

    def addSource(self, source):
        self.sources.append(source)

    def addIndex(self, index):
        self.indices.append(index)

    def addPreprocessor(self, processor):
        self.preprocessors.append(processor)

    def getTemplate(self, view, variant, flavour):
        filename = '%s_%s.%s' % (view, variant, flavour)
        if self.templates.has_key(filename): return self.templates[filename]
        raise KeyError, ('No such template', filename)

    def getStoryIds(self):
        return self.stories.keys()

    def getStoryCount(self):
        return len(self.stories)

    def update(self, story):
        for processor in self.preprocessors: story = processor(story)
        self.stories[story.id] = story
        for index in self.indices: index.update(story)

    def getStory(self, id):
        if self.stories.has_key(id): return self.stories[id]
        raise KeyError, ('No such story', id)

class CategoryIndex:
    def __init__(self):
        self.root = ({}, [])
        config.store.addIndex(self)

    def update(self, story):
        (idx, stories) = self.root
        for cat in story.category:
            if not idx.has_key(cat):
                idx[cat] = ({}, [])
            (idx, stories) = idx[cat]
        stories.append(story.id)

    def allCategories(self):
        acc = [[]]
        def collect(prefix, idx):
            for (cat, (newidx, storyids)) in idx.items():
                newprefix = prefix + [cat]
                acc.append(newprefix)
                collect(newprefix, newidx)
        collect([], self.root[0])
        return acc

    def storiesInCategory(self, category):
        acc = set()
        (idx, stories) = self.root
        for cat in category:
            if idx.has_key(cat):
                (idx, stories) = idx[cat]
            else:
                (idx, stories) = ({}, [])
                break
        acc.update(stories)

        def accumulate_tree(acc, outer_idx):
            for (idx, stories) in outer_idx.values():
                accumulate_tree(acc, idx)
                acc.update(stories)
        accumulate_tree(acc, idx)
        return acc

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

storystack = {} # used to break (certain) infinite recursions
def renderStory(flavour, variant, story, context, avoidLoops = True):
    if avoidLoops:
        storystack_key = (variant, story.id)
        if storystack_key in storystack:
            return ''
        storystack[storystack_key] = 1
    try:
        return template(config.store.getTemplate(story.view, variant, flavour),
                        Entity(config.renderenvt,
                               variant = variant,
                               story = story,
                               context = context))
    finally:
        if avoidLoops:
            del storystack[storystack_key]

def renderStories(flavour, variant, stories, context):
    fragments = []
    stories = [config.store.getStory(storyid) for storyid in stories]
    stories.sort(key = lambda s: s.mtime, reverse = True)
    for story in stories: fragments.append(renderStory(flavour, variant, story, context))
    return string.join(fragments, '')

def set_variable(entity, variablename, val):
    setattr(entity, variablename, val)
    return ''

def installPlugin(modname, *args, **kwargs):
    mod = __import__('plugins.' + modname)
    if hasattr(mod, modname):
        mod = getattr(mod, modname)
        mod.install(config, *args, **kwargs)

config = Entity()
config.version = '0.0.2'
config.language = 'en'
config.templatedirs = ['templates']
config.file_extension = 'txt'
config.store = Store()
config.categoryIndex = CategoryIndex()
config.snapshot_flavours = ['html', 'rss', 'atom']
config.verbose_snapshot = 1
config.legacy_story_links = 0
if os.environ.has_key('SCRIPT_NAME'):
    config.base_url = os.path.dirname(os.environ['SCRIPT_NAME'])
else:
    config.base_url = 'file://' + os.getcwd()

config.defaultstory = Entity(view = 'categoryindex')

config.protostory = Entity()
config.protostory.view = 'story'

config.protocontext = Entity()
config.protocontext.flavour = 'html'

config.renderenvt = Entity()
config.renderenvt.config = config
config.renderenvt.Entity = Entity
config.renderenvt.template = template
config.renderenvt.renderStory = renderStory
config.renderenvt.renderStories = renderStories
config.renderenvt.timefmt = lambda fmt, t: time.strftime(fmt, time.localtime(t))
config.renderenvt.timefmt_utc = lambda fmt, t: time.strftime(fmt, time.gmtime(t))
config.renderenvt.time3339 = lambda t: time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t))
config.renderenvt.set_variable = set_variable

def cgi_render(story, context):
    sys.stdout.write(renderStory(context.flavour, 'page_headers', story, context).encode('ascii'))
    sys.stdout.write('\r\n')
    sys.stdout.write(renderStory(context.flavour, 'page_body', story, context).encode('utf-8'))

def cgi_main():
    config.renderenvt.url = config.script_url
    config.store.load()

    category = []
    for elt in string.split(os.environ.get('PATH_INFO', ''), '/'):
        if not elt or elt.startswith('.') or elt.find('\0') != -1 or elt.find('\\') != -1:
            continue
        category.append(elt)
    if config.legacy_story_links and category and category[0] == '_STORY_': category.pop(0)

    context = Entity(config.protocontext, mode = 'script', category = category)
    for (k, v) in cgi.parse_qs(os.environ.get('QUERY_STRING', '')).items():
        setattr(context, k, yaml.safe_load(v[0]))

    story = None
    if category:
        pos = category[-1].rfind('.')
        if pos != -1:
            context.flavour = category[-1][pos + 1:]
            category[-1] = category[-1][:pos]
            try:
                story = config.store.getStory(string.join(category, '/'))
            except KeyError:
                pass
            category.pop()

    if not story:
        story = config.defaultstory

    cgi_render(story, context)
    config.store.save()

def snapshotRender(path, flavour, story, context):
    try:
        os.makedirs(os.path.dirname(path), 0755)
    except:
        pass
    if config.verbose_snapshot:
        print 'Writing %s...' % path
    document = renderStory(flavour, 'page_body', story, context)
    if document:
        f = open(path, 'w', 0644)
        f.write(document.encode('utf-8'))
        f.close()

def snapshot_main():
    config.renderenvt.url = config.snapshot_url
    config.store.load()
    for flavour in config.snapshot_flavours:
        context = Entity(config.protocontext,
                         flavour = flavour,
                         mode = 'snapshot')
        for category in config.categoryIndex.allCategories():
            if context.num_entries:
                for skip in range(0, config.store.getStoryCount(), context.num_entries):
                    pfx = ('index-skip' + str(skip)) if skip else 'index'
                    path = os.path.join(*([config.snapshot_dir] + category + [pfx + '.' + flavour]))
                    snapshotRender(path, flavour, config.defaultstory, Entity(context,
                                                                              category = category,
                                                                              skip = skip))
            else:
                snapshotRender(flavour, config.defaultstory, context)
        for storyid in config.store.getStoryIds():
            path = os.path.join(config.snapshot_dir, storyid + '.' + flavour)
            snapshotRender(path, flavour, config.store.getStory(storyid), context)
    config.store.save()

def sitemap_main():
    config.renderenvt.url = config.script_url
    config.store.load()
    context = Entity(config.protocontext, mode = 'sitemap', category = [])
    story = Entity(view = 'sitemap')
    cgi_render(story, context)
    config.store.save()

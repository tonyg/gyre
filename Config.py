import sys
from Gyre import *

config.blog_title = 'Gyre'

config.static_url = config.base_url + '/static'
config.script_url = config.base_url + '/gyre.cgi'

config.snapshot_dir = 'snapshot'
config.snapshot_url = config.base_url + '/' + config.snapshot_dir

config.protocontext.num_entries = 10

import YamlFSSource
config.store.addSource(YamlFSSource.YamlFSSource('content'))

installPlugin('emacstimestamp')
installPlugin('markdown')
installPlugin('dateline')
installPlugin('synopsis')
installPlugin('paging')

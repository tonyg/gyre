import sys
from Gyre import *

config.blog_title = 'Gyre'

config.static_url = config.base_url + '/static'
config.script_url = config.base_url + '/gyre.cgi'

config.snapshot_dir = 'snapshot'
config.snapshot_url = config.base_url + '/' + config.snapshot_dir
config.num_entries = 10

import YamlFSSource
add_source(YamlFSSource.YamlFSSource('content'))

# import OldFSSource
# add_source(OldFSSource.OldFSSource('content'))

# import TlaSource
# add_source(TlaSource.TlaSource('/usr/local/bin/tla', ['changelog']))

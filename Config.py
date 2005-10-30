import sys
from Gyre import *

config.blog_title = 'Gyre'

config.static_url = config.base_url + '/static'
config.script_url = config.base_url + '/gyre.cgi'

config.snapshot_url = ''
config.snapshot_dir = 'snapshot'
config.num_entries = 10

add_source(FSSource('content'))

# import TlaSource
# add_source(TlaSource.TlaSource('/usr/local/bin/tla', ['changelog']))

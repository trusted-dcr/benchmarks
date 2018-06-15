import argparse
import json
import subprocess
import os
import shutil

START_PORT = 50500
DETACHED_PROCESS = 0x00000008

def hex128(i):
  return format(i, '#018x')

parser = argparse.ArgumentParser(description='Run benchmarks on the trusted DCR system.')
parser.add_argument('graph_file',
  metavar='file',
  type=argparse.FileType('r'),
  help='a TDCR config file describing the DCR graph to use')
parser.add_argument('--peers',
  dest='num_peers',
  type=int,
  required=True,
  help='total amount of peers')

args = parser.parse_args()
conf = json.load(args.graph_file)
conf['peers'] = []

num_events = len(conf['workflow']['events'])
num_relations = reduce((lambda a, b: a + b),
  map((lambda event:
      len(event['conditionRelations']) +
      len(event['excludeRelations']) +
      len(event['includeRelations']) +
      len(event['milestoneRelations']) +
      len(event['responseRelations'])),
    conf['workflow']['events']))
num_peers = args.num_peers;

print 'NUM EVENTS:....%i' % num_events
print 'NUM RELAITONS..%i' % num_relations
print 'NUM PEERS:.....%i' % num_peers

# setup peers in config
for pi in range(num_peers):
  ei = pi/(num_peers/num_events)
  event = conf['workflow']['events'][ei]
  peer = {
    'addr': '127.0.0.1:{0}'.format(START_PORT + pi),
    'event': conf['workflow']['events'][ei]['uid'],
    'uid': { 'hex': hex128(pi + 1) },
  }

  conf['peers'].append(peer)

print 'Writing temp config files..'
if not os.path.exists('temp'):
  os.mkdir('temp')
os.chdir('temp')
for pi in range(num_peers):
  peer = conf['peers'][pi]
  conf['self'] = peer['uid']
  with open("{0}.json".format(peer['uid']['hex']), "w") as pconf_file:
    json.dump(conf, pconf_file)
os.chdir("..")

print 'Starting enclaves..'
os.chdir('../tdcr')
FNULL = open(os.devnull, 'w')
for pi in range(num_peers):
  peer = conf['peers'][pi]
  subprocess.Popen(
    [
      'tdcr.bat',
      'start',
      '-c',
      '..\\benchmarks\\temp\\{0}.json'.format(peer['uid']['hex']),
      '-p',
      str(START_PORT + pi)
    ],
    stdout=FNULL,
    stderr=subprocess.STDOUT)
os.chdir('../benchmarks')
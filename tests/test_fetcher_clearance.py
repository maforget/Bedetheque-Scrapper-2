''' Fetcher: the saved Cloudflare clearance (clearance.json). '''
import json
import os
import time

from testlib import check, finish
from fetcherlib import cookie, load_fetcher, temp_data_dir

temp_data_dir()
m = load_fetcher()
path = m._clearance_file()
UA = 'Mozilla/5.0 Test Edg/158.0'


def write(data):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh)


def read():
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


print('--- nothing saved')
check('no file: no clearance', m._load_clearance(), (None, None))
write({'garbage': True})
check('unknown content: no clearance', m._load_clearance(), (None, None))
with open(path, 'w') as fh:
    fh.write('{not json')
check('broken file: no clearance', m._load_clearance(), (None, None))

print('--- round trip, only the cookie fields that are needed')
c = cookie('cf_clearance', 'abc', expires=time.time() + 3600)
c['httpOnly'] = True
c['sameSite'] = 'None'
m._save_clearance(UA, c)
data = read()
check('file holds the User-Agent and one cookie', sorted(data), ['cookie', 'user_agent'])
check('cookie fields kept', sorted(data['cookie']),
      ['domain', 'expires', 'name', 'path', 'secure', 'value'])
ua, loaded = m._load_clearance()
check('loaded User-Agent', ua, UA)
check('loaded cookie', (loaded['name'], loaded['value']), ('cf_clearance', 'abc'))
check('no temp file left behind (S5)', os.path.exists(path + '.tmp'), False)

print('--- what is not loaded')
m._save_clearance(UA, cookie('cf_clearance', expires=time.time() - 10))
check('expired clearance ignored', m._load_clearance(), (None, None))
m._save_clearance(UA, cookie('cf_clearance', expires=-1))
check('session cookie (no expiry) loaded', m._load_clearance()[1]['name'], 'cf_clearance')
write({'user_agent': UA, 'cookie': cookie('csrf_cookie_bel')})
check('a cookie other than cf_clearance is refused', m._load_clearance(), (None, None))
write({'user_agent': '', 'cookie': cookie('cf_clearance')})
check('clearance without User-Agent ignored', m._load_clearance(), (None, None))

print('--- older format with every bedetheque cookie (review point 3)')
write({'user_agent': UA, 'cookies': [cookie('csrf_cookie_bel'), cookie('bdg_bedetheque_cookie'),
                                     cookie('cf_clearance', 'old')]})
ua, loaded = m._load_clearance()
check('clearance taken from the old list', (ua, loaded['value']), (UA, 'old'))
rewritten = read()
check('file rewritten with only cf_clearance', (sorted(rewritten), rewritten['cookie']['name']),
      (['cookie', 'user_agent'], 'cf_clearance'))
write({'user_agent': UA, 'cookies': [cookie('csrf_cookie_bel')]})
check('old list without cf_clearance: nothing loaded', m._load_clearance(), (None, None))

print('--- atomic write (S5)')
m._save_clearance(UA, cookie('cf_clearance', 'good'))
original = open(path, encoding='utf-8').read()
real_replace = m.os.replace
m.os.replace = lambda a, b: (_ for _ in ()).throw(OSError('disk full'))
m._save_clearance(UA, cookie('cf_clearance', 'new'))
m.os.replace = real_replace
check('a failed write leaves the saved clearance intact',
      open(path, encoding='utf-8').read(), original)
check('...and no temp file', os.path.exists(path + '.tmp'), False)

print('--- only cf_clearance is restored on start (B2)')
m._save_clearance(UA, cookie('cf_clearance', 'restored', expires=time.time() + 3600))
d = m.Daemon()
check('jar after start', [(x.name, x.value) for x in d._jar], [('cf_clearance', 'restored')])
check('opener sends the saved User-Agent', dict(d._opener.addheaders)['User-Agent'], UA)

print('--- adopting from the browser saves only cf_clearance')
d._adopt('Mozilla/5.0 New', cookie('cf_clearance', 'fresh'))
check('saved after adopt', (read()['user_agent'], read()['cookie']['value']),
      ('Mozilla/5.0 New', 'fresh'))
check('jar holds the fresh clearance',
      [(x.name, x.value) for x in d._jar if x.name == 'cf_clearance'], [('cf_clearance', 'fresh')])

finish()

#!/usr/bin/python3

import json
import subprocess
import sys
from datetime import datetime as DT
import semantic_version as SV
import logging
from subprocess import PIPE

logging.basicConfig(level=logging.WARNING)

expired_packages = {}

try:
    number_of_years = int(sys.argv[2])
except IndexError:
    number_of_years = 3

with open(sys.argv[1], 'r') as read_file:
    d = json.load(read_file)

for name, version in d['dependencies'].items():
    logging.debug('======================================================================')
    logging.debug(f'name: {name}')
    logging.debug(f'asking version: {version}')
    if version.startswith('git+ssh://git@stash.inside:7999/'):
        continue
    process = subprocess.run(['npm', 'view', name, '--json', 'time'], stdout=PIPE, stderr=PIPE)
    #    From Python3.7 we can use this instead
    #    process = subprocess.run(['npm', 'view', name, '--json', 'time'], capture_output=True)
    release_dates = json.loads(process.stdout.decode('utf8').strip())
    versions = []
    for value in release_dates:
        try:
            versions.append(SV.Version(value))
        except ValueError:
            continue
    s = SV.NpmSpec(version)
    installed_version = s.select(versions)
    logging.debug(f'actual version: {installed_version}')

    str_release_date = release_dates.get(str(installed_version))
    logging.debug(f'release date: {str_release_date}')
    if str_release_date is None:
        continue
    date_obj = DT.strptime(str_release_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    date_expired = date_obj + (DT(date_obj.year + number_of_years, 1, 1, 0, 0) - DT(date_obj.year, 1, 1, 0, 0))
    str_expired_date = DT.strftime(date_expired, '%Y-%m-%dT%H:%M:%S.%fZ')
    logging.debug(f'Expire date: {str_expired_date}')
    if date_expired < DT.now():
        logging.debug('EXPIRED!!!')
        expired_packages[name] = {
            'specified_version': version,
            'installed_version': str(installed_version),
            'release_date': str_release_date
        }
    else:
        logging.debug('OK')
logging.debug('======================================================================')
print(json.dumps(expired_packages, sort_keys=True, indent=4))
print()

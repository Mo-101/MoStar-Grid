#!/usr/bin/env python3
import json, re, os

log_path = '/home/idona/MoStar/_apps/grid/back/services/mindgraph/mo-neo4j/logs/debug.log'
conf_path = '/home/idona/MoStar/_apps/grid/back/services/mindgraph/mo-neo4j/conf/neo4j.conf'

if not os.path.exists(log_path):
    print('debug.log not found')
    exit(1)

# Find the last line containing DBMS provided settings
lines = []
with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'DBMS provided settings' in line:
            lines.append(line)

if not lines:
    print('No DBMS config dump found')
    exit(1)

last_msg = None
for line in reversed(lines):
    try:
        record = json.loads(line)
        msg = record.get('message', '')
        if 'DBMS provided settings' in msg:
            last_msg = msg
            break
    except Exception:
        continue

if not last_msg:
    print('Could not parse DBMS config dump')
    exit(1)

# Extract key=value pairs and multi-line jvm options
raw_parts = [p.strip() for p in re.split(r'\\n|\n', last_msg)]

pairs = []
i = 0
while i < len(raw_parts):
    part = raw_parts[i]
    if not part or part in ['DBMS provided settings', 'Directories in use']:
        i += 1
        continue
    if part.startswith(('db.', 'server.', 'dbms.', 'internal.')) and '=' in part:
        key, value = part.split('=', 1)
        # Collect continuation lines for server.jvm.additional (values starting with -)
        if key == 'server.jvm.additional':
            continuation = [value]
            i += 1
            while i < len(raw_parts):
                nxt = raw_parts[i]
                if nxt and (nxt.startswith('-') or ' ' not in nxt) and not nxt.startswith(('db.', 'server.', 'dbms.', 'internal.')):
                    continuation.append(nxt)
                    i += 1
                else:
                    break
            pairs.append((key, ' '.join(continuation)))
            continue
        else:
            pairs.append((key, value))
    i += 1

# Deduplicate by key, preserving first occurrence
seen = set()
unique = []
for key, value in pairs:
    if key not in seen:
        seen.add(key)
        unique.append(f'{key}={value}')

os.makedirs(os.path.dirname(conf_path), exist_ok=True)
with open(conf_path, 'w', encoding='utf-8') as f:
    f.write('# Recovered from debug.log DBMS provided settings\n')
    for p in unique:
        f.write(p + '\n')

print(f'Wrote {len(unique)} settings to {conf_path}')

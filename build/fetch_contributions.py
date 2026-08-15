"""Scrape the public GitHub contributions calendar into contrib.json.

Run before build.py to refresh the telemetry panels:
    python3 build/fetch_contributions.py jvittor
"""
import json, os, re, sys, urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else 'jvittor'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', 'contrib.json')

req = urllib.request.Request(
    f'https://github.com/users/{USER}/contributions',
    headers={'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'})
html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')

# each cell carries a date + level; the count lives in its matching <tool-tip>
cells = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"\s+id="([^"]+)"\s+data-level="(\d)"', html)
tips = dict(re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', html))

days = []
for date, cid, level in cells:
    txt = tips.get(cid, '')
    m = re.match(r'(\d+)\s+contribution', txt)
    days.append({'date': date, 'level': int(level), 'count': int(m.group(1)) if m else 0})

# GitHub emits the calendar weekday-major (every Sunday, then every Monday...).
# Sort to true chronological order so week N is DAYS[N*7:(N+1)*7].
days.sort(key=lambda d: d['date'])

data = {
    'user': USER,
    'days': days,
    'total': sum(d['count'] for d in days),
    'best': max((d['count'] for d in days), default=0),
    'active_days': sum(1 for d in days if d['count'] > 0),
    'range': [days[0]['date'], days[-1]['date']] if days else [None, None],
}
json.dump(data, open(OUT, 'w'), indent=1)
print(f"{USER}: {data['total']} contributions over {len(days)} days "
      f"({data['active_days']} active, best {data['best']}) {data['range'][0]} -> {data['range'][1]}")

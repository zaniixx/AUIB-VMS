"""
Scan the repository for redundant files:
- duplicate basenames (same filename in multiple locations)
- identical files (by SHA256 hash)
- overlaps between Backend/static and Frontend/static

Outputs a concise report to stdout.
"""
import os
import hashlib
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', '.venv3'}

basename_map = defaultdict(list)
hash_map = defaultdict(list)
backend_static = os.path.join(ROOT, 'Backend', 'static')
frontend_static = os.path.join(ROOT, 'Frontend', 'static')

for dirpath, dirnames, filenames in os.walk(ROOT):
    # simple ignore
    parts = set(dirpath.split(os.sep))
    if parts & ignore_dirs:
        continue
    for fname in filenames:
        # skip large binaries maybe
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'rb') as f:
                data = f.read()
        except Exception:
            continue
        h = hashlib.sha256(data).hexdigest()
        basename_map[fname].append(fpath)
        hash_map[h].append(fpath)

# prepare reports
duplicate_basenames = {b:p for b,p in basename_map.items() if len(p)>1}
identical_files = [paths for paths in hash_map.values() if len(paths)>1]

# overlaps Backend vs Frontend static by basename and by identical content
backend_files = {}
frontend_files = {}
for dirroot, d in [(backend_static, backend_files), (frontend_static, frontend_files)]:
    if os.path.isdir(dirroot):
        for dirpath, dirnames, filenames in os.walk(dirroot):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, 'rb') as f:
                        data = f.read()
                except Exception:
                    continue
                d.setdefault(fname, []).append((fpath, hashlib.sha256(data).hexdigest()))

# basename overlaps
static_basename_overlaps = {}
for fname in set(list(backend_files.keys()) + list(frontend_files.keys())):
    a = backend_files.get(fname, [])
    b = frontend_files.get(fname, [])
    if a and b:
        static_basename_overlaps[fname] = {'backend': [p for p,_ in a], 'frontend': [p for p,_ in b]}

# identical overlaps between static dirs (by hash)
static_identical_overlaps = []
for fname, a in backend_files.items():
    for path_a, hash_a in a:
        for fname_b, b in frontend_files.items():
            for path_b, hash_b in b:
                if hash_a == hash_b:
                    static_identical_overlaps.append((path_a, path_b))

# print report
print('\n=== Duplicate basenames (same filename in multiple locations) ===\n')
if duplicate_basenames:
    for b, paths in sorted(duplicate_basenames.items()):
        print(f"- {b} ({len(paths)} locations)")
        for p in sorted(paths):
            print(f"    {p}")
else:
    print('None found')

print('\n=== Identical files (exact same content) ===\n')
if identical_files:
    for group in identical_files:
        print(f"- group of {len(group)} identical files:")
        for p in sorted(group):
            print(f"    {p}")
else:
    print('None found')

print('\n=== Static Backend <-> Frontend basename overlaps ===\n')
if static_basename_overlaps:
    for b,p in static_basename_overlaps.items():
        print(f"- {b}")
        for side in ('backend','frontend'):
            for path in p[side]:
                print(f"    {side}: {path}")
else:
    print('None found or one of the static dirs missing')

print('\n=== Static Backend <-> Frontend identical file pairs ===\n')
if static_identical_overlaps:
    for a,b in sorted(static_identical_overlaps):
        print(f"- {a}\n    ==\n    {b}\n")
else:
    print('None found')

print('\nReport root:', ROOT)

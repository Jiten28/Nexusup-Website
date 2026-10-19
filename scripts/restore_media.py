#!/usr/bin/env python3
"""Opt-in local restoration of dated raster uploads. Dry run by default. Never runs PHP."""
import argparse, hashlib, json, re, stat, zipfile
from pathlib import Path, PurePosixPath
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('archive',type=Path)
p.add_argument('--destination',type=Path,default=Path(__file__).resolve().parents[1]/'media')
p.add_argument('--apply',action='store_true',help='Copy missing media after validation; never overwrite conflicts')
a=p.parse_args();dest=a.destination.resolve();allowed={'.png','.jpg','.jpeg','.webp','.gif','.avif'}
plan=[];skipped=0;conflicts=[];total=0
with zipfile.ZipFile(a.archive) as z:
    seen=set()
    for info in z.infolist():
        path=PurePosixPath(info.filename)
        if path.is_absolute() or '..' in path.parts or stat.S_ISLNK(info.external_attr>>16):
            raise SystemExit('Unsafe archive path; aborted: '+info.filename)
        marker='/wp-content/uploads/'
        if marker not in info.filename or info.is_dir():continue
        name=info.filename.split(marker,1)[1]
        if not re.match(r'^20\d{2}/(?:0[1-9]|1[0-2])/',name) or PurePosixPath(name).suffix.lower() not in allowed:
            skipped+=1;continue
        if name in seen:raise SystemExit('Duplicate archive path: '+name)
        seen.add(name)
        if info.flag_bits&1 or info.file_size>50_000_000:raise SystemExit('Encrypted/oversized member: '+name)
        total+=info.file_size
        if total>2_000_000_000:raise SystemExit('Extraction exceeds 2 GB safety cap')
        target=(dest/name).resolve()
        if not target.is_relative_to(dest):raise SystemExit('Unsafe destination')
        data=z.read(info) # validates CRC, including on dry run
        digest=hashlib.sha256(data).hexdigest()
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
            conflicts.append(name)
        plan.append((info.filename,name,digest,not target.exists()))
    print(json.dumps({'mode':'apply' if a.apply else 'dry-run','eligible':len(plan),'bytes':total,'excluded_non_dated_or_non_raster':skipped,'missing':sum(x[3] for x in plan),'conflicts':conflicts},indent=2))
    if conflicts:raise SystemExit('Conflicts found. Nothing copied; resolve manually in an isolated staging folder.')
    if a.apply:
        dest.mkdir(parents=True,exist_ok=True)
        for archive_name,name,digest,missing in plan:
            if missing:
                target=dest/name;target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as out:out.write(z.read(archive_name))
        manifest=[{'path':n,'sha256':h} for _,n,h,_ in plan]
        (dest/'restored-media-manifest.json').write_text(json.dumps(manifest,indent=2))
        print('Local raster uploads copied. No database records or metadata migrated.')

#!/usr/bin/env python3
"""Render Rahul's neofetch-style profile with public GitHub statistics.

python3 update_profile.py
python3 update_profile.py --data-dir /path/to/offline/api/snapshots
"""
import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent
LOGIN='rahulrameshm0'

def fetch(path):
    headers={'User-Agent':'rahul-profile-readme','Accept':'application/vnd.github+json'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
    for attempt in range(3):
        try:
            with urlopen(Request('https://api.github.com'+path,headers=headers),timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt==2:
                raise
            time.sleep(2**attempt)

def load_data(data_dir):
    if data_dir:
        directory=Path(data_dir)
        return json.loads((directory/'profile.json').read_text()),json.loads((directory/'repos.json').read_text())
    profile=fetch(f'/users/{LOGIN}')
    repos=[]
    page=1
    while True:
        batch=fetch(f'/users/{LOGIN}/repos?type=owner&per_page=100&page={page}')
        repos.extend(batch)
        if len(batch)<100:
            break
        page+=1
    return profile,repos

def uptime(created):
    start=datetime.fromisoformat(created.replace('Z','+00:00'))
    now=datetime.now(timezone.utc)
    years=now.year-start.year
    months=now.month-start.month
    days=now.day-start.day
    if days<0:
        import calendar
        previous_month=now.month-1 or 12
        previous_year=now.year-(now.month==1)
        days+=calendar.monthrange(previous_year,previous_month)[1]
        months-=1
    if months<0:
        months+=12
        years-=1
    return f'{years} years, {months} months, {days} days'

def render(profile,repos,mobile=False):
    width,height=(820,1360) if mobile else (1200,700)
    startx=24 if mobile else 402
    right=width-24
    shift=650 if mobile else 0
    chars=71
    fs=18 if mobile else 17.5
    cell=fs*.6
    ink='#cee8ed';accent='#e9ad99';dots='#506273'
    bits=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
          '<title id="title">Rahul Ramesh — GitHub terminal profile</title>',
          '<desc id="desc">A background-free ASCII portrait beside dotted-leader rows listing Rahul’s profile, programming stack, learning interests, contact links and public GitHub stats.</desc>',
          '<style>text{font-family:Menlo,Consolas,"Liberation Mono",monospace;font-variant-ligatures:none}</style>',
          f'<rect width="{width}" height="{height}" fill="#101b2b"/>']
    def text(x,y,value,color=ink,size=fs,weight=600,extra=''):
        bits.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" {extra}>{escape(str(value))}</text>')
    portrait=json.loads((ROOT/'portrait.json').read_text())
    px=237 if mobile else 20
    for i,row in enumerate(portrait):
        text(px,34+i*8.5,row,ink,9,500,'xml:space="preserve" aria-hidden="true"')
    def heading(y,label):
        y+=shift
        text(startx,y,label,ink,fs,700)
        linex=startx+(len(label)+1)*cell
        bits.append(f'<path d="M{linex:.1f} {y-5} H{right}" stroke="{ink}" stroke-width="1.3"/>')
    def row(y,label,value):
        y+=shift
        value=str(value)
        count=max(2,chars-len(label)-len(value)-2)
        # Fixed-width spans align labels left and values right, like neofetch.
        dot_text=' '+'.'*count+' '
        text(startx,y,label,accent)
        text(startx+len(label)*cell,y,dot_text,dots,fs,400,'xml:space="preserve"')
        text(right,y,value,ink,fs,600,'text-anchor="end"')
    heading(39,'rahul@github')
    for y,label,value in [
        (69,'Name:','Rahul Ramesh'),
        (96,'GitHub.Uptime:',uptime(profile['created_at'])),
        (123,'Host:','Novoxedtech'),
        (150,'Kernel:','Software Engineer'),
        (177,'Location:','Calicut, Kerala, India'),
        (231,'Languages.Programming:','Python, JavaScript, SQL'),
        (258,'Languages.Markup:','HTML, CSS'),
        (285,'Frameworks:','Django, FastAPI, React'),
        (339,'Building:','Web apps, REST APIs, automation'),
        (366,'Learning:','Async Python, system design, DSA'),
    ]:
        row(y,label,value)
    heading(420,'Contact')
    for y,label,value in [
        (450,'Email.Personal:','rahulrameshm98@gmail.com'),
        (477,'Portfolio:','rahul-u763.onrender.com'),
        (504,'LinkedIn:','rahul-ramesh-86a564325'),
        (531,'GitHub:','rahulrameshm0'),
    ]:
        row(y,label,value)
    heading(585,'GitHub Stats')
    public=[r for r in repos if not r.get('private') and r['owner']['login'].lower()==LOGIN.lower()]
    original=[r for r in public if not r['fork']]
    stars=sum(r['stargazers_count'] for r in original)
    python=sum(r.get('language')=='Python' for r in original)
    languages=len({r['language'] for r in original if r.get('language')})
    def statpair(y,left_label,left_value,right_label,right_value):
        y+=shift
        half=startx+int((right-startx)*.58)
        text(startx,y,left_label,accent)
        text(half-19,y,left_value,ink,fs,600,'text-anchor="end"')
        text(half,y,'|',dots,fs,400)
        text(half+24,y,right_label,accent)
        text(right,y,right_value,ink,fs,600,'text-anchor="end"')
    statpair(615,'Repos:',f'{profile["public_repos"]} (Original: {len(original)})','Stars:',stars)
    statpair(642,'Python Repos:',python,'Followers:',profile['followers'])
    since=datetime.fromisoformat(profile['created_at'].replace('Z','+00:00')).strftime('%b %Y')
    statpair(669,'On GitHub:',since,'Languages:',languages)
    bits.append('</svg>')
    return '\n'.join(bits)+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir')
    args=parser.parse_args()
    profile,repos=load_data(args.data_dir)
    if profile['login'].lower()!=LOGIN.lower():
        raise ValueError('Unexpected user')
    for filename,mobile in [('profile.svg',False),('profile-mobile.svg',True)]:
        (ROOT/filename).write_text(render(profile,repos,mobile),encoding='utf-8')
    print('Rendered neofetch-style profile')

if __name__=='__main__':
    main()

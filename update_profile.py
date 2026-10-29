#!/usr/bin/env python3
"""Render self-contained GitHub profile SVGs from public GitHub data.

Run with --data-dir to use saved profile.json and repos.json snapshots offline.
Uses only the Python standard library; no external image or stats service.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
LOGIN = 'rahulrameshm0'
COLORS = {'ink':'#dbe4ef','dim':'#8b9bad','green':'#a5d6a7','cyan':'#91d7e3','peach':'#f5b98c','violet':'#c5b4f4'}

def fetch(path):
    headers = {'User-Agent': 'rahul-profile-readme', 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GH_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    for attempt in range(3):
        try:
            with urlopen(Request('https://api.github.com'+path, headers=headers), timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def load_data(data_dir):
    if data_dir:
        directory = Path(data_dir)
        return json.loads((directory/'profile.json').read_text()), json.loads((directory/'repos.json').read_text())
    profile = fetch(f'/users/{LOGIN}')
    repos = []
    page = 1
    while True:
        batch = fetch(f'/users/{LOGIN}/repos?type=owner&per_page=100&page={page}')
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return profile, repos

def render(profile, repos, mobile=False, dark=True):
    colors = COLORS if dark else {"ink":"#273449","dim":"#56677b","green":"#397244","cyan":"#166477","peach":"#985421","violet":"#7450a2"}
    rule_color = "#273342" if dark else "#ccd4df"
    width, height = (640, 1390) if mobile else (1080, 780)
    bits = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            '<title id="title">Rahul Ramesh — terminal profile</title>',
            '<desc id="desc">ASCII portrait of Rahul Ramesh, software engineer in Calicut, Kerala. Python, Django, FastAPI, React and SQL. Public GitHub stats follow below.</desc>',
            '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;font-variant-ligatures:none}.portrait{font-family:Menlo,Consolas,"Liberation Mono",monospace}</style>',
            f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="16" fill="#0c1119" stroke="#2b3645"/>',
            f'<path d="M17 1 H{width-17} Q{width-1} 1 {width-1} 17 V48 H1 V17 Q1 1 17 1" fill="#171f2b"/>']
    def text(x,y,value,color='ink',size=16,extra=''):
        bits.append(f'<text x="{x}" y="{y}" fill="{colors.get(color,color)}" font-size="{size}" {extra}>{escape(str(value))}</text>')
    def line(y,x=30,end=None):
        bits.append(f'<path d="M{x} {y} H{end or width-30}" stroke="{rule_color}" stroke-dasharray="3 5"/>')
    for x,color in [(25,'#f17c73'),(45,'#edc56f'),(65,'#89c59a')]:
        bits.append(f'<circle cx="{x}" cy="25" r="5" fill="{color}"/>')
    text(92,30,'rahul@github: ~', 'dim',13)
    text(width-134,30,'profile / v1', 'dim',12)
    text(30,88,'❯', 'green',20)
    text(55,88,'whoami', 'ink',18)
    text(149,88,'--about --stats', 'dim',16)
    rows = json.loads((ROOT/'portrait.json').read_text())
    px,py = (137,122) if mobile else (33,152)
    scale = 1.22 if mobile else 1
    bits.append(f'<g transform="translate({px} {py}) scale({scale})" aria-hidden="true">')
    for n,row in enumerate(rows):
        spans=''
        for chars,color in row:
            if not dark:
                color='#'+''.join(f'{int(int(color[i:i+2],16)*.62):02x}' for i in (1,3,5))
            spans+=f'<tspan fill="{color}">{escape(chars)}</tspan>'
        bits.append(f'<text class="portrait" x="0" y="{n*5.8}" font-size="8" xml:space="preserve">{spans}</text>')
    bits.append('</g>')
    text(164 if mobile else 66,565 if mobile else 530,'[ portrait rendered in ASCII ]','dim',12)
    if not mobile:
        bits.append(f'<path d="M337 122 V584" stroke="{rule_color}"/>')
    x = 30 if mobile else 366
    y = 620 if mobile else 141
    text(x,y,'rahul@rahulrameshm0', 'violet',22)
    text(x,y+31,'Rahul Ramesh', 'ink',19)
    text(x,y+57,'Software Engineer', 'green',16)
    line(y+75,x)
    fields = [
        ('Location','Calicut, Kerala, India'),
        ('Focus','Backend + full-stack applications'),
        ('Languages','Python, JavaScript, SQL'),
        ('Backend','Django, FastAPI, REST APIs'),
        ('Databases','PostgreSQL, MySQL'),
        ('Frontend','React, Tailwind CSS, Bootstrap'),
        ('Tools','Git, Docker, Render, Vercel'),
        ('Learning','Async Python, system design, DSA'),
    ]
    yy=y+107
    for label,value in fields:
        text(x,yy,label,'peach',16)
        text(x+(133 if mobile else 151),yy,value,'ink',14 if mobile else 15)
        yy+=29
    line(yy-8,x)
    text(x,yy+18,'Contact','cyan',16)
    text(x,yy+48,'Email','peach',15)
    text(x+105,yy+48,'rahulrameshm98@gmail.com','ink',14)
    text(x,yy+76,'Links','peach',15)
    text(x+105,yy+76,'Portfolio / LinkedIn / GitHub','ink',14)
    text(x,yy+107,'Open to backend & full-stack opportunities','green',13 if mobile else 14)
    sy=1158 if mobile else 627
    line(sy-26)
    text(30,sy,'❯', 'green',20)
    text(55,sy,'github --public-stats', 'ink',17)
    owned=[r for r in repos if not r.get('private') and r['owner']['login'].lower()==LOGIN.lower()]
    original=[r for r in owned if not r['fork']]
    langs=Counter(r['language'] for r in original if r.get('language'))
    stats=[('PUBLIC REPOS',profile['public_repos']),('PYTHON REPOS',langs['Python']),('FOLLOWERS',profile['followers']),('STARS EARNED',sum(r['stargazers_count'] for r in original))]
    for index,(label,value) in enumerate(stats):
        sx=30+index*((width-60)/4)
        text(sx,sy+48,f'{value:02d}','cyan',29 if mobile else 32)
        text(sx,sy+73,label,'dim',10 if mobile else 12)
    line(sy+96)
    started=datetime.fromisoformat(profile['created_at'].replace('Z','+00:00')).strftime('%b %Y')
    updated=datetime.now(timezone.utc).strftime('%Y-%m-%d')
    text(30,sy+123,f'On GitHub since {started}', 'dim',11 if mobile else 12)
    text(width-202,sy+123,f'Updated {updated} UTC','dim',11 if mobile else 12)
    text(30,height-17,'> build. learn. repeat_', 'green',12)
    bits.append('</svg>')
    return '\n'.join(bits)+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',help='Directory containing offline public API snapshots')
    args=parser.parse_args()
    profile,repos=load_data(args.data_dir)
    if profile['login'].lower()!=LOGIN.lower():
        raise ValueError('Unexpected GitHub user')
    for name,mobile,dark in [('terminal.svg',False,True),('terminal-mobile.svg',True,True)]:
        result=render(profile,repos,mobile,dark)
        (ROOT/name).write_text(result,encoding='utf-8')
    print(f'Rendered profile for {profile["login"]} ({profile["public_repos"]} public repositories)')

if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Render Rahul's neofetch-style profile (ASCII portrait + live GitHub stats).

python3 update_profile.py                       # live data (set GH_TOKEN for full stats)
python3 update_profile.py --data-dir /path/to/offline/api/snapshots
"""
import argparse
import calendar
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent
LOGIN='rahulrameshm0'
OUTPUTS=[('neofetch.svg',False),('neofetch-mobile.svg',True)]

def request(path,body=None):
    headers={'User-Agent':'rahul-profile-readme','Accept':'application/vnd.github+json'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
    data=json.dumps(body).encode() if body is not None else None
    for attempt in range(3):
        try:
            with urlopen(Request('https://api.github.com'+path,data=data,headers=headers),timeout=30) as response:
                return response.status,(json.load(response) if response.status!=204 else None)
        except Exception:
            if attempt==2:
                raise
            time.sleep(2**attempt)

def fetch(path):
    return request(path)[1]

def lines_of_code(repos):
    """Sum additions/deletions by LOGIN; GitHub answers 202 while it computes stats."""
    added=deleted=0
    pending=[r['full_name'] for r in repos]
    for _ in range(6):
        retry=[]
        for name in pending:
            status,stats=request(f'/repos/{name}/stats/contributors')
            if status==202:
                retry.append(name)
                continue
            for author in stats or []:
                if (author.get('author') or {}).get('login','').lower()==LOGIN.lower():
                    added+=sum(w['a'] for w in author['weeks'])
                    deleted+=sum(w['d'] for w in author['weeks'])
        if not retry:
            break
        pending=retry
        time.sleep(5)
    return added,deleted

def load_data(data_dir):
    if data_dir:
        directory=Path(data_dir)
        return json.loads((directory/'profile.json').read_text()),json.loads((directory/'repos.json').read_text()),json.loads((directory/'extra.json').read_text())
    profile=fetch(f'/users/{LOGIN}')
    repos=[]
    page=1
    while True:
        batch=fetch(f'/users/{LOGIN}/repos?type=owner&per_page=100&page={page}')
        repos.extend(batch)
        if len(batch)<100:
            break
        page+=1
    extra={'commits':fetch(f'/search/commits?q=author:{LOGIN}&per_page=1')['total_count']}
    if os.environ.get('GH_TOKEN'):
        query='{user(login:"%s"){repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,REPOSITORY]){totalCount}}}'%LOGIN
        extra['contributed']=request('/graphql',{'query':query})[1]['data']['user']['repositoriesContributedTo']['totalCount']
    extra['added'],extra['deleted']=lines_of_code([r for r in repos if not r['fork']])
    return profile,repos,extra

def uptime(created):
    start=datetime.fromisoformat(created.replace('Z','+00:00'))
    now=datetime.now(timezone.utc)
    years=now.year-start.year
    months=now.month-start.month
    days=now.day-start.day
    if days<0:
        previous_month=now.month-1 or 12
        previous_year=now.year-(now.month==1)
        days+=calendar.monthrange(previous_year,previous_month)[1]
        months-=1
    if months<0:
        months+=12
        years-=1
    return f'{years} years, {months} months, {days} days'

def ascii_portrait():
    """(char, tone) cells generated from the avatar photo by tools/make_portrait.py."""
    return json.loads((ROOT/'portrait.json').read_text())['cells']

def render(profile,repos,extra,mobile=False):
    width,height=(820,1290) if mobile else (1200,630)
    startx=24 if mobile else 624
    right=width-24
    shift=650 if mobile else 0
    fs=17 if mobile else 14.6
    cell=fs*.6
    chars=int((right-startx)/cell)
    bg='#161b22';ink='#c9d1d9';key='#ffa657';dots='#616e7f';plus='#3fb950';minus='#f85149'
    bits=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
          '<title id="title">Rahul Ramesh — GitHub neofetch profile</title>',
          '<desc id="desc">A square ASCII-art portrait (made from the GitHub avatar) beside neofetch-style rows listing Rahul’s system, languages, hobbies, contact links and live GitHub stats.</desc>',
          '<style>text{font-family:Menlo,Consolas,"DejaVu Sans Mono","Liberation Mono",monospace;font-variant-ligatures:none;white-space:pre}</style>',
          f'<rect width="{width}" height="{height}" rx="12" fill="{bg}"/>']
    def text(x,y,value,color=ink,size=fs,weight=400,extra_attr=''):
        bits.append(f'<text x="{x:.1f}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" xml:space="preserve" {extra_attr}>{escape(str(value))}</text>')
    portrait=ascii_portrait()
    # Square block: cols*0.6*psize == rows*lead.
    psize,lead=(14.9,20) if mobile else (14.3,19.2)
    px=(width-len(portrait[0])*psize*.6)/2 if mobile else 22
    for i,line in enumerate(portrait):
        runs=[]
        for char,tone in line:
            # Brighter tones get lighter ink; the shading is what draws the face.
            # Tones are bucketed so neighbouring digits share one <tspan>.
            color=None if char==' ' else '#'+''.join(f'{round(a+(b-a)*(.7+.3*(round(tone*24)/24))):02x}' for a,b in [(22,230),(27,237),(34,243)])
            if runs and runs[-1][0]==color:
                runs[-1][1]+=char
            else:
                runs.append([color,char])
        spans=[text_run if color is None else f'<tspan fill="{color}">{text_run}</tspan>' for color,text_run in runs]
        bits.append(f'<text x="{px:.1f}" y="{34+i*lead:.1f}" font-size="{psize}" font-weight="400" xml:space="preserve" aria-hidden="true">{"".join(spans)}</text>')
    y=40+shift
    def heading(label):
        nonlocal y
        text(startx,y,label,ink,fs,700)
        bits.append(f'<path d="M{startx+(len(label)+1)*cell:.1f} {y-5} H{right}" stroke="{dots}" stroke-width="1.2"/>')
        y+=28
    def row(label,value):
        nonlocal y
        value=str(value)
        count=max(2,chars-len(label)-len(value)-2)
        text(startx,y,label,key,fs,600)
        text(startx+len(label)*cell,y,' '+'.'*count+' ',dots)
        text(right,y,value,ink,fs,400,'text-anchor="end"')
        y+=28
    def gap():
        nonlocal y
        y+=16
    original=[r for r in repos if not r['fork'] and r['owner']['login'].lower()==LOGIN.lower()]
    stars=sum(r['stargazers_count'] for r in original)
    heading('rahul@ramesh')
    row('OS:','macOS, Android')
    row('Uptime:',uptime(profile['created_at']))
    row('Host:','Novoxedtech')
    row('Kernel:','Software Engineer')
    row('IDE:','VS Code, PyCharm')
    gap()
    row('Languages.Programming:','Python, JavaScript, TypeScript, SQL')
    row('Languages.Computer:','HTML, CSS, JSON, Markdown, YAML')
    row('Languages.Real:','English, Malayalam')
    gap()
    row('Hobbies.Software:','Web scraping, automation, REST APIs')
    row('Hobbies.Learning:','Async Python, system design, DSA')
    gap()
    heading('Contact')
    row('Email.Personal:','rahulrameshm98@gmail.com')
    row('Portfolio:','rahul-u763.onrender.com')
    row('LinkedIn:','rahul-ramesh-86a564325')
    gap()
    heading('GitHub Stats')
    def statpair(left_label,left_value,right_label,right_value):
        nonlocal y
        half=startx+int((right-startx)*.6)
        text(startx,y,left_label,key,fs,600)
        text(half-16,y,left_value,ink,fs,400,'text-anchor="end"')
        text(half,y,'|',dots)
        text(half+18,y,right_label,key,fs,600)
        text(right,y,right_value,ink,fs,400,'text-anchor="end"')
        y+=28
    contributed=f' {{Contributed: {extra["contributed"]}}}' if 'contributed' in extra else ''
    statpair('Repos:',f'{profile["public_repos"]}{contributed}','Stars:',f'{stars:,}')
    statpair('Commits:',f'{extra["commits"]:,}','Followers:',f'{profile["followers"]:,}')
    added,deleted=extra['added'],extra['deleted']
    text(startx,y,'Lines of Code on GitHub:',key,fs,600)
    # Right-aligned "( +++ , --- )" tail, built from the end so the total sits before it.
    tail=[(' )',ink),(f'{deleted:,}--',minus),(', ',ink),(f'{added:,}++',plus),('( ',ink),(f'{added-deleted:,} ',ink)]
    x=right
    for value,color in tail:
        text(x,y,value,color,fs,400,'text-anchor="end"')
        x-=len(value)*cell
    bits.append('</svg>')
    return '\n'.join(bits)+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir')
    args=parser.parse_args()
    profile,repos,extra=load_data(args.data_dir)
    if profile['login'].lower()!=LOGIN.lower():
        raise ValueError('Unexpected user')
    for filename,mobile in OUTPUTS:
        (ROOT/filename).write_text(render(profile,repos,extra,mobile),encoding='utf-8')
    print(f'Rendered neofetch-style profile: {extra}')

if __name__=='__main__':
    main()

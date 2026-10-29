import json,sys,math
# usage: make_portrait.py pixels.json cols rows x0 y0 x1 y1 k gamma ramp_gamma [ascii|binary|letters] > portrait.json (char+tone per cell)
d=json.load(open(sys.argv[1])); n=d['size']; G=d['gray']; M=d['mask']
cols,rows=int(sys.argv[2]),int(sys.argv[3]); x0,y0,x1,y1=map(int,sys.argv[4:8]); k=float(sys.argv[8]); gam=float(sys.argv[9])
cw,ch=(x1-x0)/cols,(y1-y0)/rows
cov=[[0]*cols for _ in range(rows)]; val=[[0]*cols for _ in range(rows)]
for r in range(rows):
    for c in range(cols):
        s=cnt=tot=0
        for y in range(int(y0+r*ch),int(y0+(r+1)*ch)):
            for x in range(int(x0+c*cw),int(x0+(c+1)*cw)):
                tot+=1
                if M[y*n+x]>128: s+=G[y*n+x]; cnt+=1
        cov[r][c]=cnt/max(1,tot); val[r][c]=s/cnt if cnt else 0
lit=sorted(val[r][c] for r in range(rows) for c in range(cols) if cov[r][c]>=.5)
import bisect
eq=lambda v: bisect.bisect_left(lit,v)/len(lit)
t=[[eq(val[r][c]) if cov[r][c]>=.5 else None for c in range(cols)] for r in range(rows)]
def blur(r,c,R=2):
    v=[t[y][x] for y in range(max(0,r-R),min(rows,r+R+1)) for x in range(max(0,c-R),min(cols,c+R+1)) if t[y][x] is not None]
    return sum(v)/len(v)
t2=[[None if t[r][c] is None else min(1,max(0,t[r][c]+k*(t[r][c]-blur(r,c))))**gam for c in range(cols)] for r in range(rows)]
ramp=" .:-=+*#%@"
mode=sys.argv[11] if len(sys.argv)>11 else 'ascii'
binary=mode=='binary'
if mode=='letters':
    # Glyphs ordered light→heavy, like the reference video's portrait.
    ramp=" .'`,:;!|~^*=[]jilrnwkpgmhHM%N@"
out=[]
for r in range(rows):
    line=[]
    for c in range(cols):
        v=t2[r][c]
        if v is None: line.append([' ',0]); continue
        if binary:
            # Every subject cell is a digit; tone (colour) carries the shading, bright cells lean to 0.
            line.append([' ' if v<.08 else '0' if v>.5 else '1',round(v,3)]); continue
        # silhouette edge: neighbour outside the subject
        nb=lambda y,x: 0<=y<rows and 0<=x<cols and t2[y][x] is not None
        L,R_,U,D=nb(r,c-1),nb(r,c+1),nb(r-1,c),nb(r+1,c)
        if mode=='letters': ch=ramp[min(len(ramp)-1,int(v**float(sys.argv[10])*len(ramp)))]
        elif not U and (L and R_): ch='_' 
        elif not L and not R_: ch='|'
        elif not L: ch='/' if not U else ('\\' if not D else '|')
        elif not R_: ch='\\' if not U else ('/' if not D else '|')
        else: ch=ramp[min(len(ramp)-1,int(v**float(sys.argv[10])*len(ramp)))]
        line.append([ch,round(v,3)])
    out.append(line)
json.dump({'cols':cols,'rows':rows,'cells':out},sys.stdout)

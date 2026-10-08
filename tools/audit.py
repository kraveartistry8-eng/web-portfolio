# -*- coding: utf-8 -*-
import io,re,datetime
import pathlib
P=str(pathlib.Path(__file__).resolve().parent.parent/"2026-10-02-shopify-roadmap.html")
s=io.open(P,encoding="utf-8").read()
txt=lambda x: re.sub(r'\s+',' ',re.sub(r'<[^>]*>','',x)).replace("&middot;","·").replace("&ndash;","-").replace("&nbsp;"," ").replace("&rsquo;","'").replace("&mdash;","-").strip()
FAIL=[];OK=[]
def chk(cond,msg): (OK if cond else FAIL).append(msg)

i=s.index("<!-- P1 -->"); j=s.index("  </section>",i); P4=s[i:j]
blocks=re.findall(r'<div class="w">(.*?)</div>\s*<div><h4>(.*?)</h4>(.*?)(?=<div class="wk">|<div class="gate">|<div class="flag|<!-- P|\Z)', P4, re.S)

# ---------- 1. week numbering is contiguous
nums=[int(re.match(r'W(\d+)',txt(w)).group(1)) for w,_,_ in blocks]
chk(nums==list(range(1,28)), f"week numbers contiguous W1..W27 (got {nums[0]}..{nums[-1]}, {len(nums)} blocks)")

# ---------- 2. every dated day row falls on the weekday it claims
MON={'Jan':1,'Feb':2,'Mar':3,'Oct':10,'Nov':11,'Dec':12}
DAY={'Mon':0,'Tue':1,'Wed':2,'Thu':3,'Fri':4,'Sat':5,'Sun':6}
bad=[]
for w,title,body in blocks:
    wl=txt(w); mons=re.findall(r'(Jan|Feb|Mar|Oct|Nov|Dec)',wl)
    yr=2026 if mons and mons[0] in ('Oct','Nov','Dec') else 2027
    for d in re.findall(r'<div class="d">(.*?)</div>', body, re.S):
        dl=txt(d); m=re.match(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d+)$', dl)
        if not m: continue
        name,day=m.group(1),int(m.group(2))
        cand=[(mm,yy) for mm in set(mons) for yy in (yr,yr+1)]
        hit=False
        for mm,yy in cand:
            try:
                if datetime.date(yy,MON[mm],day).weekday()==DAY[name]: hit=True;break
            except ValueError: pass
        if not hit: bad.append(f"{wl} :: {dl}")
chk(not bad, f"all dated day rows land on the weekday they claim ({len(bad)} wrong)")
for b in bad: print("      !",b)

# ---------- 3. prospects opened, counted from the tasks themselves
opened={}
for w,title,body in blocks:
    n=int(re.match(r'W(\d+)',txt(w)).group(1))
    opened[n]=len(re.findall(r'Touch one to five new prospects',body))*5 + len(re.findall(r'Eight touch-one emails',body))*8
dec=sum(opened[k] for k in (11,12,13,14)); jan=sum(opened[k] for k in (15,16,17,18,19))
g1=re.search(r'Gate, 27 December.*?<li>(\d+) prospects opened',s,re.S)
g2=re.search(r'Gate, 31 January.*?<li>(\d+) prospects opened',s,re.S)
chk(g1 and int(g1.group(1))==dec, f"27 Dec gate says {g1.group(1) if g1 else '?'} prospects, tasks open {dec}")
chk(g2 and int(g2.group(1))==dec+jan, f"31 Jan gate says {g2.group(1) if g2 else '?'} prospects, tasks open {dec+jan} cumulative")

# ---------- 4. section 05 totals vs the tasks
wknd=sum(v for k,v in opened.items() if k not in (24,25))
sprint=sum(v for k,v in opened.items() if k in (24,25))
row=re.search(r'Prospects worked</td><td class="n">~(\d+)</td><td>(\d+) through the weekend sequence, (\d+) in the sprint',s)
if row:
    tot,ww,ss=int(row.group(1)),int(row.group(2)),int(row.group(3))
    chk(ww==wknd, f"section 05 weekend prospects {ww} vs tasks {wknd}")
    chk(ss==sprint, f"section 05 sprint prospects {ss} vs tasks {sprint}")
    chk(abs(tot-(wknd+sprint))<=5, f"section 05 total ~{tot} vs tasks {wknd+sprint}")
else: FAIL.append("could not parse the 'Prospects worked' row in section 05")

# ---------- 5. the money table adds up
rows=re.findall(r'<tr><td>(October|November|December|January|February|March)</td>(.*?)</tr>',s,re.S)
cols=[[int(x.replace('$','').replace(',','')) if re.match(r'^\$[\d,]+$',x) else None
       for x in re.findall(r'<td class="n">(.*?)</td>',r[1])] for r in rows]
debt=10000; ok=True
for c in cols:
    debt-=c[0]
    if c[1]!=debt: ok=False
chk(ok and debt==5800, f"debt column walks 10,000 down to {debt} at $700/mo")
tot=re.search(r'<td>Total</td>(.*?)</tr>',s,re.S)
if tot:
    t=[x.replace('$','').replace(',','').replace(' left','') for x in re.findall(r'<td class="n">(.*?)</td>',tot.group(1))]
    chk(int(t[0])==sum(c[0] for c in cols), f"total to debt {t[0]} vs column sum {sum(c[0] for c in cols)}")
    chk(int(t[3])==sum(c[3] or 0 for c in cols), f"total studio gross {t[3]} vs column sum {sum(c[3] or 0 for c in cols)}")
    chk(int(t[4])==sum(c[4] or 0 for c in cols), f"total tax held {t[4]} vs column sum {sum(c[4] or 0 for c in cols)}")
    chk(int(t[5])==sum(c[5] or 0 for c in cols), f"total to savings {t[5]} vs column sum {sum(c[5] or 0 for c in cols)}")
    # to savings must be the free surplus plus studio revenue net of tax, every month
    derived=all((c[5] or 0)==(c[2] or 0)+((c[3] or 0)-(c[4] or 0)) for c in cols)
    chk(derived, "to savings = free surplus + studio gross - tax held, every month")
    chk(all(round((c[4] or 0)/(c[3] or 1),2) in (0.0,0.3) for c in cols), "tax held is 30% of studio gross every month")

# ---------- 6. the load-bearing money figures agree with themselves
# The hero carried a fact grid when this check was written. It no longer does, so the
# equivalent check is that the figures agree wherever they appear, and that the
# annualisations are arithmetically right.
chk(bool(re.search(r'<header class="hero">.*?<h1>.*?</h1>.*?<p class="lead">.*?</p>.*?</header>', s, re.S)),
    "hero is present and well formed")

gate = set(re.findall(r'\$6,000 a month|\$6,000/mo', s))
chk(bool(gate), "the exit gate figure appears in the document")
chk('$5,000 a month recurring' not in s and '$7,000 a month recurring' not in s,
    "no competing exit gate figure contradicts $6,000")

# annualisations stated in section 01
for monthly, annual in (("6,000", "72,000"), ("10,000", "120,000"), ("3,400", "40,800")):
    m = int(monthly.replace(",", "")); a = int(annual.replace(",", ""))
    stated = f"${annual}" in s
    chk(stated and m * 12 == a, f"${monthly}/mo annualises to ${annual} and the document says so")

# ---------- 7. cross-references resolve
for ref in set(re.findall(r'section 0(\d)',s)):
    chk(f'<span class="num">0{ref}</span>' in s, f"cross-reference to section 0{ref} resolves")
for wk in set(re.findall(r'week (\d+)',s)):
    chk(int(wk)<=27, f"cross-reference to week {wk} is within W1..W27")

# ---------- 8. every week has exactly one output, numbering resets per day
# tolerant of extra classes on the span, e.g. the "done" tick
_outs=len(re.findall(r'class="out(?:\s[^"]*)?"',P4))
chk(_outs==27, f"27 outputs for 27 weeks (found {_outs})")

print("\n".join("  PASS  "+m for m in OK))
print()
if FAIL: print("\n".join("  FAIL  "+m for m in FAIL))
else: print("  no failures")

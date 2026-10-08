# -*- coding: utf-8 -*-
"""Does every week that the volume change touches actually carry a task for it?"""
import io,re
import pathlib
P=str(pathlib.Path(__file__).resolve().parent.parent/"2026-10-02-shopify-roadmap.html")
s=io.open(P,encoding="utf-8").read()
clean=lambda x: re.sub(r'\s+',' ',re.sub(r'<[^>]*>','',x)).replace("&middot;","·")\
    .replace("&ndash;","-").replace("&nbsp;"," ").replace("&rsquo;","'").replace("&mdash;","-").strip()
FAIL=[];OK=[]
def chk(c,m): (OK if c else FAIL).append(m)

i=s.index("<!-- P1 -->"); P4=s[i:s.index("  </section>",i)]
blocks=re.findall(r'<div class="w">(.*?)</div>\s*<div><h4>(.*?)</h4>(.*?)(?=<div class="wk">|<div class="gate">|<div class="flag|<!-- P|\Z)',P4,re.S)

week={}
for w,title,body in blocks:
    n=int(re.match(r'W(\d+)',clean(w)).group(1))
    days=re.split(r'<div class="d">(.*?)</div>',body)
    cur={}; label=None
    for k,part in enumerate(days):
        if k%2==1: label=clean(part)
        elif label is not None:
            cur[label]=[clean(li) for li in re.findall(r'<li>(.*?)</li>',part,re.S)]
    week[n]=(clean(title),cur)

def tasks(n,day=None):
    t,d=week[n]
    return sum(d.values(),[]) if day is None else d.get(day,[])

WORD={'Thirteen':13,'Sixteen':16,'sixteen':16,'thirteen':13}
# ---- 1. network announce emails on exactly six Fridays, summing to 78
send={}
for n in week:
    for t in tasks(n):
        m=re.match(r'(Thirteen|The last thirteen) announce emails',t)
        if m: send[n]=13
chk(sorted(send)== [2,3,4,5,7,8], f"announce emails on exactly W2,3,4,5,7,8 (got {sorted(send)})")
chk(sum(send.values())==78, f"announce emails total 78 (got {sum(send.values())})")
chk(6 not in send, "W6 corporate leave carries no announce emails")

# ---- 2. the running totals in the text are right
NUM={'twenty-six':26,'thirty-nine':39,'fifty-two':52,'sixty-five':65}
run=0; bad=[]
for n in [2,3,4,5,7,8]:
    run+=13
    line=[t for t in tasks(n) if 'announce emails' in t][0]
    m=re.search(r'taking you to ([a-z-]+)',line)
    if m:
        stated=NUM.get(m.group(1))
        if stated!=run: bad.append(f"W{n}: says {m.group(1)}, should be {run}")
chk(not bad, f"running totals correct through all six Fridays ({'; '.join(bad) or 'ok'})")
chk('78' in [t for t in tasks(8) if 'announce emails' in t][0], "W8 states the final 78")

# ---- 3. buyer emails alongside, on the same six Fridays
buy=[n for n in week if any('researched' in t and 'buyer' in t.lower() or 'researched emails to the buyers' in t for t in tasks(n))]
# two a week against a list of ten finishes in five weeks, so W8 correctly has none
chk(sorted(buy)==[2,3,4,5,7], f"researched buyer emails on W2,3,4,5,7 (got {sorted(buy)})")
chk(len(buy)*2==10, f"two a week over {len(buy)} weeks covers all 10 buyers (got {len(buy)*2})")
chk(any('completes all ten' in t for t in tasks(7)), "W7 says the buyer list is finished")
chk(any('88 names' in t for t in tasks(8)), "W8 states the full 88 contacted")

# ---- 4. the 120-row research, moved to October
res={}
for n in week:
    for t in tasks(n):
        m=re.search(r'List the (first|second|last) 40',t)
        if m: res[n]=m.group(1)
chk(sorted(res)==[2,3,4], f"three batches of 40 on W2,W3,W4 (got {sorted(res)})")
chk(set(res.values())=={'first','second','last'}, "the three batches are first, second and last")
named=[n for n in week if any('named contact against all 120' in t for t in tasks(n))]
chk(named==[5], f"named contacts against all 120 rows in W5 (got {named})")
chk(not any(re.search(r'List the (first|second|last) 40',t) for t in tasks(10)),
    "W10 no longer carries any list research")

# ---- 5. agency: 16 a day across W9, 48 total
ag={}
for d in ('Fri 20','Sat 21','Sun 22'):
    hits=[t for t in tasks(9,d) if 'agency emails' in t or 'agency emails,' in t]
    ag[d]=hits
chk(all(ag.values()), f"an agency send on each of Fri 20, Sat 21, Sun 22 (got { {k:len(v) for k,v in ag.items()} })")
nums=[16 for d in ag if ag[d]]
chk(sum(nums)==48, f"agency sends total 48 (got {sum(nums)})")
chk(any('48' in t for t in tasks(9)), "W9 states the full 48")
chk(any('Touch two to every agency' in t for t in tasks(10)), "W10 carries the agency follow-up")

# ---- 6. deliverability lands before the first send, not after
w2fri=tasks(2,'Fri 9')
spf=[k for k,t in enumerate(w2fri) if 'SPF, DKIM and DMARC' in t]
first=[k for k,t in enumerate(w2fri) if 'announce emails' in t]
chk(spf and first and spf[0]<first[0], "SPF/DKIM/DMARC is scheduled before the first announce email")
chk(any('CAN-SPAM' in t for t in w2fri), "the CAN-SPAM footer is built in W2, not week 9")
chk(not any('SPF, DKIM and DMARC' in t for t in tasks(9)), "the old week 9 deliverability task is gone")

# ---- 7. touch two reaches all 88 and is spread
t2=[t for t in tasks(8) if 'Touch two to all 88' in t]
chk(t2, "W8 sends touch two to all 88")
chk(t2 and ('Split it' in t2[0]), "the 88-email touch two is split across three days")

# ---- 8. nothing stale survives
chk('Five warm emails' not in s, "no 'Five warm emails' left anywhere")
chk('all 15 to 20' not in s, "no 'all 15 to 20' agency line left")
chk('Build the cold list of 120</h4>' not in s, "the old W10 heading is gone")

for m in OK: print("  PASS ",m)
print()
for m in FAIL: print("  FAIL ",m)
print("\n","no failures" if not FAIL else f"{len(FAIL)} FAILURES")

"""Refresh dated public GitHub panels. No token, private data, or Git writes."""
from collections import Counter
from datetime import date, datetime, timezone, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import json, re

ROOT=Path(__file__).resolve().parents[1]
def get(url):
    with urlopen(Request(url,headers={'User-Agent':'Kelv-Ojo-profile-public-stats'}),timeout=25) as r:
        return r.read().decode('utf-8')

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__();self.days={};self.tips={};self.tip=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='td' and a.get('data-date'):self.days[a['id']]={'date':a['data-date'],'level':int(a['data-level'])}
        if tag=='tool-tip':self.tip=a.get('for')
    def handle_endtag(self,tag):
        if tag=='tool-tip':self.tip=None
    def handle_data(self,text):
        if self.tip:self.tips[self.tip]=self.tips.get(self.tip,'')+text

def parse_calendar(text):
    cal=Calendar();cal.feed(text)
    assert len(cal.days)>350,'Incomplete calendar; keep previous snapshot'
    days=[]
    for key,day in cal.days.items():
        tip=cal.tips.get(key,'').strip()
        match=re.match(r'(No|[\d,]+) contributions? on ',tip)
        assert match, f'Unknown calendar label: {tip}'
        days.append({**day,'count':0 if match[1]=='No' else int(match[1].replace(',',''))})
    days.sort(key=lambda d:d['date'])
    headline=re.search(r'id="js-contribution-activity-description"[^>]*>(.*?)</h2>',text,re.S)
    expected=int(re.search(r'[\d,]+',re.sub('<[^>]+>','',headline[1]))[0].replace(',',''))
    assert sum(d['count'] for d in days)==expected,'Calendar does not reconcile'
    return days

def svg(width,height,body,dark=False,title='Public GitHub activity'):
    bg,ink,muted=('#0d1117','#f0f6fc','#b1bac4') if dark else ('#ffffff','#172238','#526074')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img"><title>{escape(title)}</title><rect width="100%" height="100%" rx="10" fill="{bg}"/><g font-family="sans-serif" fill="{ink}">{body}</g></svg>'

def render(snapshot):
    out=ROOT/'assets';out.mkdir(exist_ok=True)
    days=snapshot['calendar'];active={d['date']:d['count'] for d in days}
    longest=run=0
    for day in days:
        run=run+1 if day['count'] else 0;longest=max(longest,run)
    # Strict date-based streak through the capture date; no grace day is implied.
    current=0;cursor=date.fromisoformat(snapshot['as_of'])
    while active.get(cursor.isoformat(),0):current+=1;cursor-=timedelta(days=1)
    languages=Counter(snapshot['languages']);total=sum(languages.values())
    for dark in [False,True]:
        theme='dark' if dark else 'light';muted='#b1bac4' if dark else '#526074';accent='#d9bc7b' if dark else '#806029'
        body=f'<text x="28" y="34" font-size="18" font-weight="600">GitHub public calendar</text><text x="28" y="60" font-size="13" fill="{muted}">Snapshot {snapshot["as_of"]} · {days[0]["date"]} to {days[-1]["date"]}</text>'
        for x,value,label in [(28,sum(d['count'] for d in days),'Window contributions'),(312,current,'Streak through capture date'),(596,longest,'Longest streak in window')]:
            body+=f'<text x="{x}" y="116" font-size="38" fill="{accent}">{value}</text><text x="{x}" y="146" font-size="14">{label}</text>'
        (out/f'activity-summary-{theme}.svg').write_text(svg(880,174,body,dark),encoding='utf-8')
        body=f'<text x="28" y="32" font-size="18" font-weight="600">Contribution activity</text><text x="28" y="56" font-size="13" fill="{muted}">Public calendar · daily counts · snapshot {snapshot["as_of"]}</text>'
        first=date.fromisoformat(days[0]['date']);palette=['#21262d','#0e4429','#006d32','#26a641','#39d353'] if dark else ['#ebedf0','#9be9a8','#40c463','#30a14e','#216e39']
        for day in days:
            offset=(date.fromisoformat(day['date'])-first).days; x=28+(offset//7)*15; y=82+(offset%7)*15
            body+=f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{palette[day["level"]]}"><title>{day["date"]}: {day["count"]} contributions</title></rect>'
        body+=f'<text x="28" y="216" font-size="13" fill="{muted}">Counts reflect GitHub’s public calendar, not working hours or skill level.</text>'
        (out/f'contribution-graph-{theme}.svg').write_text(svg(880,240,body,dark),encoding='utf-8')
        colors=['#3572A5','#e34c26','#563d7c','#f1e05a','#C1D8ED'];body=f'<text x="28" y="34" font-size="18" font-weight="600">Repository languages</text><text x="28" y="60" font-size="13" fill="{muted}">Public non-fork repositories · code bytes · snapshot {snapshot["as_of"]}</text>';x=28
        for i,(lang,n) in enumerate(languages.most_common()):
            w=824*n/total;body+=f'<rect x="{x:.2f}" y="84" width="{w:.2f}" height="18" fill="{colors[i%len(colors)]}"/>';x+=w
        for i,(lang,n) in enumerate(languages.most_common()):
            x=28+(i%3)*280;y=138+(i//3)*34;body+=f'<circle cx="{x+5}" cy="{y-5}" r="5" fill="{colors[i%len(colors)]}"/><text x="{x+20}" y="{y}" font-size="15">{escape(lang)} {n/total:.1%}</text>'
        (out/f'languages-{theme}.svg').write_text(svg(880,212,body,dark),encoding='utf-8')

def main():
    today=datetime.now(timezone.utc).date().isoformat()
    repos=json.loads(get('https://api.github.com/users/Kelv-Ojo/repos?per_page=100'))
    assert len(repos)<100,'Add pagination before refreshing more than 100 repositories'
    counts=Counter();sources=[]
    for repo in repos:
        if repo['fork']:continue
        lang=json.loads(get(repo['languages_url']));counts.update(lang);sources.append({'repository':repo['full_name'],'languages':lang})
    snapshot={'as_of':today,'calendar_source':'https://github.com/users/Kelv-Ojo/contributions','calendar':parse_calendar(get('https://github.com/users/Kelv-Ojo/contributions')),'languages':dict(counts),'language_sources':sources}
    render(snapshot)
    (ROOT/'assets/public-stats.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
    print('Refreshed public-data snapshots; no files pushed or published.')

if __name__=='__main__':main()

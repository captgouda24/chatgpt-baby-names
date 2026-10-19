import time,urllib.request,urllib.parse,urllib.error,json,os,sys
out=sys.argv[1]
q='("unruly passenger" OR "unruly passengers") sourcecountry:US sourcelang:english'
periods=[]
for y in range(2018,2027):
  for qs,qe in (('0101','0331'),('0401','0630'),('0701','0930'),('1001','1231')):
    if y==2026 and qs>'0701': continue
    periods.append((f'{y}{qs}000000',f'{y}{qe}235959'))
for s,e in periods:
  fn=os.path.join(out,f'{s[:8]}.json')
  if os.path.exists(fn): continue
  for a in range(6):
    u='https://api.gdeltproject.org/api/v2/doc/doc?'+urllib.parse.urlencode(dict(query=q,mode='artlist',maxrecords=250,startdatetime=s,enddatetime=e,format='json',sort='hybridrel'))
    try:
      t=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'research'}),timeout=120).read().decode('utf-8-sig','ignore')
      if t.startswith('Please'): raise ValueError('rate')
      open(fn,'w',encoding='utf8').write(t); print(s, len(json.loads(t or '{}').get('articles',[])) if t.strip() else 0, flush=True); break
    except Exception as ex:
      print(s,'retry',ex,flush=True); time.sleep(45)
  time.sleep(12)

import struct,os
def valid_payload(t):
    if not t: return False
    try:
        t.decode('ascii'); return True
    except: pass
    try:
        s=t.decode('cp949')
        return sum(1 for ch in s if ch.isprintable() or ch in '\r\n\t') >= len(s)*0.95
    except: return False
def best_chain(d,maxlen=8192):
    n=len(d); best=(0,0,0,[])
    for start in range(0,32):
        for skip in (0,1,2,3,4):
            i=start; out=[]; ok=True
            while i+skip+4<=n:
                L=struct.unpack_from('<I',d,i+skip)[0]
                if not (1<=L<=maxlen) or i+skip+4+L>n: break
                t=d[i+skip+4:i+skip+4+L]
                if not valid_payload(t): break
                out.append((i+skip+4,t)); i+=skip+4+L
            if len(out)>len(best[3]): best=(len(out),start,skip,out)
    return best
for fn in ('fxstagemap.ssd.bin','fxdynmapinfo.ssd.bin','fxstock0.ini.bin','stringtable.ini.bin','csysstr.ssd.bin','csysqstr.ssd.bin','filterstr.ssd.bin','multisvr.ssd.bin','spcc.ssd.bin','fxstovi.ini.bin','csysfxmg.ssd.bin','fxdynimginfo.ssd.bin','product.ini.bin','fxstovs.ini.bin','channel2_001.ssd.bin'):
    d=open('/Users/hieu/Workspaces/taone/work/ssi/'+fn,'rb').read()
    n,start,skip,out=best_chain(d)
    cov=sum(4+len(t)+skip for _,t in out)
    print("%-26s recs=%-5d start=%-3d skip=%d cov=%.0f%%  first=%r"%(
        fn,n,start,skip,100*cov/len(d), out[0][1][:30] if out else b''))

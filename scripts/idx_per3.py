import sys
for path in sys.argv[1:]:
    d=open(path,'rb').read(); body=d[16:]; n=len(body)
    res=[]
    for P in (1,16,32,63,64,126,128,256,512,1024):
        if n<=P: continue
        z=sum(1 for i in range(n-P) if body[i]==body[i+P])
        res.append((P,z/(n-P)))
    res.sort(key=lambda x:-x[1])
    print(path.split('/')[-1], "n=%d"%n, " ".join("P%d=%.3f"%(P,f) for P,f in res[:5]))

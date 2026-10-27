import sys,collections
path=sys.argv[1]; d=open(path,'rb').read()
gram=bytes.fromhex(sys.argv[2])
offs=[i for i in range(len(d)) if d.startswith(gram,i)]
print(path.split('/')[-1],"gram",gram.hex(),"count",len(offs))
print("offsets:",[hex(o) for o in offs[:40]])
if len(offs)>1:
    diffs=[offs[i+1]-offs[i] for i in range(len(offs)-1)]
    print("diffs:",diffs[:40])
    print("offs mod 16:",[o%16 for o in offs[:20]])
    print("offs mod 63:",[o%63 for o in offs[:20]])
# expand max run around first occurrence
if offs:
    o=offs[0]
    s=o
    while s>0 and d[s-1]==d[o-1]: s-=1
    e=o
    while e<len(d) and d[e]==d[o+(e-o)%1]: e+=1
    # simpler: extend run
    e=o+1
    while e<len(d) and d[e]==d[e-1] if False else True:
        break
    print("context @%05x:"%o, d[max(0,o-24):o+40].hex(' '))

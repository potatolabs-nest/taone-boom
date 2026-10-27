import sys, struct, os
sys.path.insert(0, "/Users/hieu/Workspaces/taone/scripts")
from names_records import scan_ascii, best_korean_chain, chain
SSI="/Users/hieu/Workspaces/taone/work/ssi"
for fn in sorted(os.listdir(SSI)):
    if not fn.endswith(".bin"): continue
    d=open(os.path.join(SSI,fn),'rb').read()
    asc=scan_ascii(d)
    kr=best_korean_chain(d)
    # count how many scanned records are NON-overlapping (real record starts)
    asc_sorted=sorted(asc)
    nonover=[]; last=-1
    for p,L,pay in asc_sorted:
        if p>last: nonover.append((p,L,pay)); last=p+4+L
    cov=sum(4+L for _,L,_ in nonover)
    print("%-26s size=%-7d ascii_recs=%-6d nonoverlap=%-5d cov=%.0f%%  kr_chain=%-5d krfirst=%r"%(
        fn,len(d),len(asc),len(nonover),100*cov/len(d),len(kr),
        (kr[0][2][:24] if kr else b'')))

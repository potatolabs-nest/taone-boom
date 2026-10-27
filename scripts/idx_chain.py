import sys
d=open(sys.argv[1],'rb').read()[16:]
n=len(d)
# Model A: C[i]^C[i+1] == P[i+1]  (prev-plaintext chaining)
A=bytes(d[i]^d[i+1] for i in range(n-1))
# Model B: C[i]-C[i+1] == -P[i+1]  (prev-plaintext add chaining)
B=bytes((d[i]-d[i+1])&0xff for i in range(n-1))
# Model C: C[i-1]^C[i] == P[i]  (same as A shifted)
def printscore(x,label):
    import collections
    good=sum(1 for b in x if 32<=b<127)
    # filename-like ratio
    fn=sum(1 for b in x if chr(b).isalnum() or b in b'._-\\/')
    print("%s printable=%.3f filelike=%.3f"%(label,good/len(x),fn/len(x)))
    print("   sample:", ''.join(chr(b) if 32<=b<127 else '.' for b in x[:120]))
printscore(A,"A: C[i]^C[i+1]")
printscore(B,"B: C[i]-C[i+1]")
printscore(bytes((d[i]+d[i+1])&0xff for i in range(n-1)),"C: C[i]+C[i+1]")

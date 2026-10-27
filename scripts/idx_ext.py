import sys,os,struct,glob
exts=[b'.bmp',b'.dds',b'.ogg',b'.tga',b'.png',b'.jpg',b'.ktx',b'.ani',b'.scr',b'.wav',b'.dat',b'.txt',b'.ini',b'.avi',b'.bik',b'.tmh',b'.exe',b'.dll']
files=sys.argv[1:]
for path in files:
    d=open(path,'rb').read()
    print("=== %s len=%d hdr=%s" % (os.path.basename(path),len(d),d[:16].hex()))
    for e in exts:
        offs=[i for i in range(len(d)) if d.startswith(e,i)]
        if offs:
            diffs=[offs[i+1]-offs[i] for i in range(len(offs)-1)]
            print("   %-6s n=%3d offs=%s" % (e.decode(),len(offs),[hex(o) for o in offs[:8]]),
                  ("diffs="+str(diffs[:8]) if diffs else ""))

import json,struct,sys,base64,numpy as np
def load(path):
    b=open(path,'rb').read();assert b[:4]==b'glTF'
    off=12;J=None;BIN=None
    while off<len(b):
        ln,typ=struct.unpack_from('<II',b,off);d=b[off+8:off+8+ln];off+=8+ln
        if typ==0x4E4F534A:J=json.loads(d)
        else:BIN=d
    def acc(i):
        a=J['accessors'][i];bv=J['bufferViews'][a['bufferView']];o=bv.get('byteOffset',0)+a.get('byteOffset',0)
        ct={5126:np.float32,5123:np.uint16,5125:np.uint32,5121:np.uint8}[a['componentType']];nc={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        st=bv.get('byteStride');n=a['count']
        if st and st!=nc*np.dtype(ct).itemsize:
            raw=np.frombuffer(BIN,np.uint8,count=st*n,offset=o).reshape(n,st);return np.frombuffer(raw[:,:nc*np.dtype(ct).itemsize].tobytes(),ct).reshape(n,nc)
        return np.frombuffer(BIN,ct,count=n*nc,offset=o).reshape(n,nc)
    parent={}
    for i,nd in enumerate(J['nodes']):
        for c in nd.get('children',[]):parent[c]=i
    parts=[];blob=bytearray()
    for i,nd in enumerate(J['nodes']):
        p=parent.get(i);pn=J['nodes'][p]['name'] if p is not None else None
        rec={'name':nd['name'],'parent':pn,'t':[round(v,5) for v in nd.get('translation',[0,0,0])]}
        if 'rotation' in nd:rec['r']=nd['rotation']
        if 'mesh' in nd:
            P=[];Nn=[];U=[];I=[];base=0
            for pr in J['meshes'][nd['mesh']]['primitives']:
                at=pr['attributes'];pos=acc(at['POSITION']);nor=acc(at['NORMAL']);uv=acc(at['TEXCOORD_0']);ind=acc(pr['indices']).ravel()
                P.append(pos);Nn.append(nor);U.append(uv);I.append(ind+base);base+=len(pos)
            P=np.concatenate(P).astype(np.float32);Nn=np.concatenate(Nn).astype(np.float32);U=np.concatenate(U).astype(np.float32);I=np.concatenate(I).astype(np.uint16)
            rec['off']=len(blob);rec['nv']=len(P);rec['ni']=len(I)
            blob+=P.tobytes()+Nn.tobytes()+U.tobytes()+I.tobytes()
            while len(blob)%4:blob+=b'\0'
        parts.append(rec)
    return parts,bytes(blob)
if __name__=='__main__':
    parts,blob=load(sys.argv[1]);out={'parts':parts,'bin':base64.b64encode(blob).decode()}
    open(sys.argv[2],'w').write(json.dumps(out,separators=(',',':')))
    print(len(parts),'parts',sum(p.get('nv',0) for p in parts),'verts',sum(p.get('ni',0) for p in parts)//3,'tris',len(blob),'bytes')
    for p in parts:print(p['name'],p['parent'],p['t'],p.get('nv'),p.get('r'))

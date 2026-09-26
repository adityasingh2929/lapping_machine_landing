"""Analysis only: camera fitting and comparison assembly. Geometry lives in generate_blockout.py."""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from PIL import Image, ImageDraw
BASE=Path(__file__).resolve().parent
OUT=BASE/'reference_comparisons'
OUT.mkdir(exist_ok=True)

def initial(az,center,r=3,up=.7,roll=0,f=1500):
    a=math.radians(az); C=np.array(center)+[r*math.cos(a),r*math.sin(a),up]
    z=np.array(center)-C;z/=np.linalg.norm(z)
    x=np.cross(z,[0,0,1]);x/=np.linalg.norm(x); y=np.cross(z,x)
    R=np.array([x,y,z]);R=Rotation.from_euler('z',roll,degrees=True).as_matrix()@R
    return np.r_[Rotation.from_matrix(R).as_rotvec(),C,np.log(f)]

def project(p,xyz,w,h):
    R=Rotation.from_rotvec(p[:3]).as_matrix()
    cam=(xyz-p[3:6])@R.T
    return cam[:,:2]/cam[:,2:3]*np.exp(p[6])+[w/2,h/2]

def fit():
    data=json.loads((BASE/'reference_landmarks.json').read_text())
    if 'correction' in data:
        for k,pt in data['points'].items():
            if k.startswith('p'):pt[2]+=data['correction'].get('beam_z_translation',data['correction']['upper_z_translation'])
            if k.startswith('s') and k[-1]=='c':pt[2]+=data['correction'].get('cylinder_z_translation',data['correction']['upper_z_translation'])
            if k.startswith('s') and k[-1]=='h':pt[2]+=data['correction']['upper_z_translation']
            if k.startswith('s'):
                pt[0]*=data['correction']['station_radius_scale'];pt[1]*=data['correction']['station_radius_scale']
            if k[0] in ('q','d') and 'console' in data['correction']:
                sx,sy,dy,sz=data['correction']['console'];pt[0]*=sx;pt[1]=(pt[1]+.84)*sy-.84+dy;pt[2]*=sz
    data['points'].update(data.get('saved_point_overrides',{}))
    only=next((a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')),None)
    results=json.loads((BASE/'reference_cameras.json').read_text()) if only else {}
    for ns,view in data['views'].items():
        if only and ns not in only:continue
        n=int(ns); w,h=(1368,1824) if n<15 else (1824,1368)
        names=[k for k in view['obs'] if n>=12 or k[0] not in ('q','d')]; xyz=np.array([data['points'][k] for k in names]); uv=np.array([view['obs'][k] for k in names])
        if not len(names):continue
        # Only camera pose and focal length are fitted. All views share the identical 3D coordinates.
        center=xyz.mean(axis=0)
        best=None
        for f in ([1100,1600,2400] if n!=14 else [1300,2200]):
            r=3 if n<12 else (.38 if n==12 else (1 if n in (13,14) else .65))
            up=.55 if n<12 else (.03 if n==12 else (1.0 if n in (13,14) else .03))
            init=initial(view['az'],center,r,up,-90 if n==14 else 0,f)
            def residual(p):
                err=(project(p,xyz,w,h)-uv).ravel()
                if 'contours' in view:
                    rows=[]
                    for name,x0,x1,y0,y1 in view['contours']:
                        center=np.array(data['points'][name]);a=np.linspace(0,2*np.pi,256)
                        radius=.145 if name[-1]=='r' else .126
                        zs=[0] if name[-1]=='r' else [-.013,.013]
                        pts=np.concatenate([center+np.c_[radius*np.cos(a),radius*np.sin(a),np.full(len(a),z)] for z in zs])
                        pixels=project(p,pts,w,h)
                        rows.extend(np.array([pixels[:,0].min(),pixels[:,0].max(),pixels[:,1].min(),pixels[:,1].max()])-[x0,x1,y0,y1])
                    err=np.r_[err*.25,rows]
                # Weak optical prior resolves near-planar close-up ambiguity; not a measured focal length.
                return np.r_[err,(p[6]-np.log(1500))*2]
            lower=[-np.inf]*6+[np.log(650)];upper=[np.inf]*6+[np.log(6500)]
            if n==14:
                # Near-planar pose ambiguity: the column and console centerlines in the photograph
                # constrain lateral viewpoint. Four corners alone allowed an implausible side view.
                lower[3]=-.04;upper[3]=.04;init[3]=0
            sol=least_squares(residual,init,bounds=(lower,upper),loss='soft_l1',f_scale=15,max_nfev=1500)
            if best is None or sol.cost<best.cost:best=sol
        p=best.x; pred=project(p,xyz,w,h);err=np.linalg.norm(pred-uv,axis=1)
        R=Rotation.from_rotvec(p[:3]).as_matrix()
        results[ns]={'camera_location':p[3:6].tolist(),'world_to_cv':R.tolist(),'focal_preview_px':float(np.exp(p[6])),'preview_size':[w,h],'rms_preview_px':float(np.sqrt(np.mean(err**2))),'landmarks':[{ 'name':k,'photo':list(view['obs'][k]),'projected':pr.tolist(),'error_px':float(e)} for k,pr,e in zip(names,pred,err)]}
        print(n,round(np.exp(p[6])),round(results[ns]['rms_preview_px'],2),sorted(zip(names,err.round(1)),key=lambda a:-a[1])[:4])
        im=Image.open(BASE.parent/f'{n}.jpeg').resize((w,h));draw=ImageDraw.Draw(im)
        for name,a,b in zip(names,uv,pred):
            draw.ellipse((a[0]-5,a[1]-5,a[0]+5,a[1]+5),outline='lime',width=2)
            draw.line((*a,*b),fill='red',width=2); draw.text(tuple(b),name,fill='yellow')
        im.resize((w//2,h//2)).save(OUT/f'landmarks_{n:02d}.jpg')
    (BASE/'reference_cameras.json').write_text(json.dumps(results,indent=2))

def bundle():
    data=json.loads((BASE/'reference_landmarks.json').read_text())
    fits=json.loads((BASE/'reference_cameras.json').read_text())
    nums=[str(i) for i in list(range(1,12))+[15,16]]
    cams=[]; groups=[]
    for ns in nums:
        v=data['views'][ns];f=fits[ns];names=[k for k in v['obs'] if k[0] not in ('q','d')]
        xyz=np.array([data['points'][k] for k in names]);uv=np.array([v['obs'][k] for k in names])
        cams.extend(np.r_[Rotation.from_matrix(f['world_to_cv']).as_rotvec(),f['camera_location'],np.log(f['focal_preview_px'])])
        groups.append((names,xyz,uv,f['preview_size']))
    def residual(p):
        rows=[]
        for j,(names,xyz,uv,wh) in enumerate(groups):
            xyz=xyz.copy()
            # Shared translation of the full upper assembly, and shared triangular station radius.
            for i,k in enumerate(names):
                if k.startswith('p'):xyz[i,2]+=p[2]
                if k.startswith('s') and k[-1]=='c':xyz[i,2]+=p[3]
                if k.startswith('s') and k[-1]=='h':xyz[i,2]+=p[0]
                if k.startswith('s'):xyz[i,:2]*=p[1]
            c=p[4+7*j:4+7*j+7]
            rows.extend((project(c,xyz,*wh)-uv).ravel())
        return np.r_[rows,p[0]*20,(p[1]-1)*20]
    init=np.r_[.033,.936,.033,.033,cams]
    lo=[-.08,.8,-.08,-.08]+([-np.inf]*6+[np.log(650)])*len(nums)
    hi=[.15,1.25,.15,.15]+([np.inf]*6+[np.log(6500)])*len(nums)
    result=least_squares(residual,init,bounds=(lo,hi),loss='soft_l1',f_scale=10,max_nfev=220)
    print('SHARED_FIT head, radius, beam, cylinder:',result.x[:4],flush=True)
    (BASE/'reference_shared_fit.json').write_text(json.dumps({'head_z_translation':float(result.x[0]),'station_radius_scale':float(result.x[1]),'beam_z_translation':float(result.x[2]),'cylinder_z_translation':float(result.x[3]),'note':'Diagnostic joint fit, not automatically applied. Camera parameters independent per photo; geometry parameters shared.'},indent=2))

def console_fit():
    data=json.loads((BASE/'reference_landmarks.json').read_text());fits=json.loads((BASE/'reference_cameras.json').read_text())
    groups=[]
    for ns,v in data['views'].items():
        if int(ns)>11:continue
        names=[k for k in v['obs'] if k[0] in ('q','d')]
        if not names:continue
        f=fits[ns];c=np.r_[Rotation.from_matrix(f['world_to_cv']).as_rotvec(),f['camera_location'],np.log(f['focal_preview_px'])]
        groups.append((np.array([data['points'][k] for k in names]),np.array([v['obs'][k] for k in names]),c,f['preview_size']))
    def res(p):
        out=[]
        for xyz,uv,c,wh in groups:
            a=xyz.copy();a[:,0]*=p[0];a[:,1]=(a[:,1]+.84)*p[1]-.84+p[2];a[:,2]=a[:,2]*p[3]+p[4]
            out.extend((project(c,a,*wh)-uv).ravel())
        return np.array(out)
    sol=least_squares(res,[1,1,0,1,0],bounds=([.8,.6,-.15,.8,-.000001],[1.2,1.2,.15,1.2,.000001]),loss='soft_l1',f_scale=12)
    print('CONSOLE xscale,depthscale,yshift,zscale,zshift',sol.x,'rms',np.sqrt(np.mean(res(sol.x)**2)))
    (BASE/'reference_console_fit.json').write_text(json.dumps(dict(zip(['xscale','depthscale','yshift','zscale','zshift'],sol.x.tolist())),indent=2))

def gallery():
    fits=json.loads((BASE/'reference_cameras.json').read_text())
    notes=json.loads((BASE/'reference_review_notes.json').read_text())
    cards=[]
    for n in range(1,17):
        render=Image.open(OUT/f'REF_{n:02d}.png').convert('RGBA')
        photo=Image.open(BASE.parent/f'{n}.jpeg').convert('RGB').resize(render.size,Image.Resampling.LANCZOS)
        photo.save(OUT/f'photo_{n:02d}.jpg',quality=94)
        white=Image.new('RGBA',render.size,(232,234,237,255));white.alpha_composite(render);white.convert('RGB').save(OUT/f'model_{n:02d}.jpg',quality=95)
        layer=render.copy();layer.putalpha(layer.getchannel('A').point(lambda a:round(a*.5)))
        overlay=photo.convert('RGBA');overlay.alpha_composite(layer);overlay.convert('RGB').save(OUT/f'overlay_{n:02d}.jpg',quality=95)
        w,h=render.size
        trip=Image.new('RGB',(w*3,h+42),'#17202b');dr=ImageDraw.Draw(trip)
        for j,(im,title) in enumerate([(photo,'Original photograph'),(white,'Model'),(overlay,'50% model overlay')]):
            trip.paste(im.convert('RGB'),(j*w,42));dr.text((j*w+12,14),f'{n:02d} - {title}',fill='white')
        trip.save(OUT/f'comparison_{n:02d}.jpg',quality=94)
        trip.thumbnail((1200,800));trip.save(OUT/f'review_{n:02d}.jpg',quality=92)
        rms=fits[str(n)]['rms_preview_px']
        cards.append(f'<section id="ref{n:02d}"><h2>REF_{n:02d} · {n}.jpeg</h2><p>Camera landmark RMS: {rms:.1f} px at the recorded preview scale. This is alignment residual, not a geometry fidelity score.</p><div class="grid">'+''.join(f'<figure><a href="{file}_{n:02d}.jpg" target="_blank"><img loading="lazy" src="{file}_{n:02d}.jpg"></a><figcaption>{label}</figcaption></figure>' for file,label in [('photo','Original photograph'),('model','Same model · reference camera'),('overlay','50% model over original')])+f'</div><p><a href="comparison_{n:02d}.jpg">Full comparison</a> · <a href="../{n}.jpeg">Source link</a></p></section>')
    html='''<!doctype html><html><head><meta charset="utf-8"><title>Lapping machine · 16 reference comparisons</title><style>body{font:16px/1.5 system-ui;background:#121923;color:#e7edf4;margin:0 auto;padding:32px;max-width:1800px}h1{font-size:32px}h2{margin-top:48px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}figure{margin:0}img{width:100%;display:block}figcaption{padding:8px;background:#26313f}a{color:#8dc8ff}p{max-width:1000px}nav{position:sticky;top:0;padding:12px;background:#26313f;z-index:2}nav a{margin-right:16px}section{scroll-margin-top:70px}button{padding:10px} @media(max-width:700px){.grid{grid-template-columns:1fr}}</style></head><body><h1>Lapping machine — 16-view reference comparison</h1><p>Reference review in progress. Acceptance requires visual agreement across all sixteen photographs. Every render uses one common model; only the camera changes. Workshop background is excluded from assessment: renders have transparent backgrounds, and the overlay adds only model pixels at 50% opacity. Original framing, orientation and aspect ratio are retained. Lighting is neutral studio lighting, not a reconstruction of the workshop.</p><p><a href="../reference_discrepancy_report.md">Discrepancy report</a> · <a href="../reference_cameras.json">Camera fit and individual landmark residuals</a></p><nav>'''+''.join(f'<a href="#ref{n:02d}">{n:02d}</a>' for n in range(1,17))+'</nav>'+''.join(cards)+'</body></html>'
    # Originals are two directories above the gallery.
    html=html.replace('href="../1.jpeg"','href="../../1.jpeg"')
    for n in range(2,17):html=html.replace(f'href="../{n}.jpeg"',f'href="../../{n}.jpeg"')
    (OUT/'index.html').write_text(html,encoding='utf-8')
    html=html.replace('Reference review in progress.', 'All sixteen comparisons inspected; visible discrepancies remain. Reconstruction is not accepted as an exact match.')
    html=html.replace('<nav>', '<p><a href="render_manifest.json">Render/source manifest</a> · <a href="../reference_saved_verification.json">Reopened scene verification</a></p><nav>')
    for n in range(1,17):
        title=f'<h2>REF_{n:02d} · {n}.jpeg</h2>'
        html=html.replace(title,title+'<p><strong>Review:</strong> '+notes[str(n)]+'</p>')
    (OUT/'index.html').write_text(html,encoding='utf-8')
if __name__=='__main__':
    gallery() if '--gallery' in sys.argv else (bundle() if '--bundle' in sys.argv else (console_fit() if '--console-fit' in sys.argv else fit()))

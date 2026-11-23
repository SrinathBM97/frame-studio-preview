"""FRAME internal benchmark: no neural weights; results are *not* human gold masks.

Compares already-reviewed alpha cutouts to two locally executable traditional
background-removal baselines. Reports disagreement, not asserted segmentation accuracy.
Also audits actual v6 composition previews and refuses to certify creative quality.

Never modifies the original source pixels. Does not publish user assets to GitHub.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import binary_fill_holes, binary_propagation, binary_dilation

ASSETS = [
    ('Dot & Key serum', '74b5b1bDOTKE00000452_10.jpg', 'DotAndKey_StrawberrySerum_30ml.png'),
    ('Biodance mask set', '50847238809937361466_1.jpg', 'Biodance_RadiantVita_MaskSet.png'),
    ('COSRX Snail 96', '52c16568809416470009_01.jpg', 'COSRX_Snail96_100ml.png'),
    ('Face Shop cleanser', '0a7b3578806182550997_15.jpg', 'FaceShop_RiceWaterBright_150ml.png'),
]


def hash_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def bbox_from_mask(m):
    ys,xs=np.where(m)
    if not len(xs):return [0,0,0,0]
    return [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]


def normalize_silhouette(mask, canvas=384):
    m=np.asarray(mask)>127
    x,y,x2,y2=bbox_from_mask(m)
    if x2<=x or y2<=y:return np.zeros((canvas,canvas),dtype=np.uint8)
    crop=m[y:y2,x:x2].astype('uint8')
    target=int(canvas*.88)
    scale=min(target/crop.shape[1],target/crop.shape[0])
    h,w=max(1,int(round(crop.shape[0]*scale))),max(1,int(round(crop.shape[1]*scale)))
    r=cv2.resize(crop,(w,h),interpolation=cv2.INTER_NEAREST)
    out=np.zeros((canvas,canvas),dtype=np.uint8)
    yy=(canvas-h)//2;xx=(canvas-w)//2;out[yy:yy+h,xx:xx+w]=r
    return out


def mask_metrics(a,proxy=None):
    aa=np.asarray(a,dtype=np.uint8)
    m=aa>=128
    soft=((aa>8)&(aa<247))
    contour, _=cv2.findContours(m.astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    perim=sum(cv2.arcLength(c,True) for c in contour)
    n,labels,stats,_=cv2.connectedComponentsWithStats(m.astype('uint8'),8)
    important_components=sum(1 for j in range(1,n) if stats[j,cv2.CC_STAT_AREA] >= m.sum()*.001)
    b=bbox_from_mask(m)
    out={'alpha_foreground_pct':round(float(m.mean()*100),2),
         'partial_alpha_pct_of_foreground':round(float(soft.sum()/max(1,m.sum())*100),2),
         'alpha_transition_pixels_per_perimeter_pixel':round(float(soft.sum()/max(1,perim)),2),
         'important_components':int(important_components),'bbox':b,
         'edge_touch':bool(m[0].any() or m[-1].any() or m[:,0].any() or m[:,-1].any())}
    if proxy is not None:
        m2=normalize_silhouette(proxy)
        m1=normalize_silhouette(aa)
        inter=int(np.count_nonzero(m1&m2));union=int(np.count_nonzero(m1|m2))
        out['proxy_normalized_silhouette_iou']=round(inter/max(union,1),4)
        out['proxy_foreground_ratio']=round(np.count_nonzero(m1)/max(np.count_nonzero(m2),1),4)
    return out


def white_border_matte(rgb):
    im=np.asarray(rgb,dtype=np.uint8)
    hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV)
    # Gentle test baseline only: avoid treating light-colored product material as background.
    possible=(hsv[:,:,2]>238)&(hsv[:,:,1]<20)
    seeds=np.zeros(possible.shape,dtype=bool)
    seeds[0,:]=possible[0,:];seeds[-1,:]=possible[-1,:]
    seeds[:,0]=possible[:,0];seeds[:,-1]=possible[:,-1]
    bg=binary_propagation(seeds,mask=possible)
    fg=(~bg).astype(np.uint8)
    return (fg*255)


def graphcut_matte(rgb,max_dim=860):
    original=np.asarray(rgb.convert('RGB'),dtype=np.uint8)
    h0,w0=original.shape[:2]
    scale=min(1.0,max_dim/max(h0,w0))
    if scale<1:arr=cv2.resize(original,(int(round(w0*scale)),int(round(h0*scale))),interpolation=cv2.INTER_AREA)
    else:arr=original
    h,w=arr.shape[:2]
    gray=cv2.cvtColor(arr,cv2.COLOR_RGB2GRAY)
    hsv=cv2.cvtColor(arr,cv2.COLOR_RGB2HSV)
    # Probable material pixels: different enough from the white/near-white paper background.
    a=np.zeros((h,w),dtype=np.uint8)+cv2.GC_PR_BGD
    p=(gray<238)|(hsv[:,:,1]>16)
    a[p]=cv2.GC_PR_FGD
    border=max(3,int(min(h,w)*.015))
    a[:border,:]=cv2.GC_BGD;a[-border:,:]=cv2.GC_BGD
    a[:,:border]=cv2.GC_BGD;a[:,-border:]=cv2.GC_BGD
    # Hard seeds only in the interior, on very distinctive parts.
    sure=(gray<115)|(hsv[:,:,1]>95)
    sure[:border*2,:]=False;sure[-border*2:,:]=False
    sure[:,:border*2]=False;sure[:,-border*2:]=False
    if sure.sum()<50:
        sure[(h//2-8):(h//2+8),(w//2-8):(w//2+8)]=True
    a[sure]=cv2.GC_FGD
    bgmodel=np.zeros((1,65),np.float64);fgmodel=np.zeros((1,65),np.float64)
    try:
        cv2.grabCut(cv2.cvtColor(arr,cv2.COLOR_RGB2BGR),a,None,bgmodel,fgmodel,4,cv2.GC_INIT_WITH_MASK)
        out=np.where((a==cv2.GC_FGD)|(a==cv2.GC_PR_FGD),255,0).astype('uint8')
        if scale<1:out=cv2.resize(out,(w0,h0),interpolation=cv2.INTER_NEAREST)
        return out,'ok'
    except cv2.error as e:
        return np.zeros((h0,w0),np.uint8),f'failed: {str(e)[:140]}'


def image_tile(img,subtitle,w=320,h=322):
    # checker and gray background to reveal halos and edge artifacts
    cell=Image.new('RGB',(w,h),'#edf0f4')
    d=ImageDraw.Draw(cell)
    for y in range(0,h,26):
        for x in range(0,w,26):
            if (x//26+y//26)%2:d.rectangle((x,y,x+25,y+25),fill='#dce0e6')
    overlay=img.convert('RGBA');overlay.thumbnail((w-36,h-42),Image.Resampling.LANCZOS)
    cell.paste(overlay,((w-overlay.width)//2,8),overlay)
    d.rectangle((0,h-28,w,h),fill='#f9fafc')
    d.text((10,h-21),subtitle[:42],fill='#152238')
    return cell


def make_cutout(raw,mask):
    a=Image.fromarray(np.asarray(mask,np.uint8),'L')
    out=raw.convert('RGBA');out.putalpha(a)
    return out


def run(input_dir:Path, proof_dir:Path,out_dir:Path):
    out_dir.mkdir(parents=True,exist_ok=True)
    results={'protocol':'FRAME cutout & composition pre-release benchmark',
             'ground_truth':'none: supplied prior cutouts are comparison proxies, not manually vetted reference masks',
             'neural_models_tested':[],
             'local_baselines':['existing cutout alpha (not attributed to any model)','white-border connectivity','OpenCV GrabCut color models'],
             'assets':[],'composition':{},'release_decision':'NO_GO'}
    for title,jpeg,png in ASSETS:
        rp=input_dir/jpeg;ap=input_dir/png
        raw=Image.open(rp).convert('RGB');reviewed=Image.open(ap).convert('RGBA')
        proxy=np.asarray(reviewed.getchannel('A'))
        white=white_border_matte(raw)
        grab,status=graphcut_matte(raw)
        arr=[(reviewed,'Prior cutout (comparison proxy)'),(make_cutout(raw,white),'White border baseline'),(make_cutout(raw,grab),'GrabCut baseline')]
        record={'name':title,'source_sha256':hash_file(rp),'source_dimensions':list(raw.size),'prior_cutout_dimensions':list(reviewed.size),
                'methods':{},'grabcut_status':status}
        record['methods']['existing_alpha_proxy']=mask_metrics(proxy)
        record['methods']['white_background_connectivity']=mask_metrics(white,proxy)
        record['methods']['grabcut']=mask_metrics(grab,proxy)
        results['assets'].append(record)
        for key,cut in [('white',arr[1][0]),('grabcut',arr[2][0])]:
            cut.save(out_dir/f'{png.replace(".png","")}_{key}_BENCHMARK_ONLY.png')
        # no quality claim; visual examination is mandatory
        if len(results['assets'])==1:
            contact=Image.new('RGB',(3*320,4*322),'#edf0f4')
        for col,(im,sub) in enumerate(arr):
            contact.paste(image_tile(im,f'{title}  •  {sub}'),(col*320,(len(results['assets'])-1)*322))
    contact.save(out_dir/'cutout_method_comparison.jpg',quality=88)
    # v6 actual exported compositions (output layer, NOT equivalent reference-product visual rating)
    previews=sorted(proof_dir.glob('composition_*_DRAFT_2000.png'))
    if previews:
        for f in previews:
            im=Image.open(f).convert('RGBA');a=np.asarray(im.getchannel('A'));m=a>128
            bounds=bbox_from_mask(m)
            dark_composite=np.asarray(im.convert('RGB'))
            ex={'name':f.name,'rgba_dimensions':list(im.size),'transparent':bool(a.min()==0),
                'occupied_alpha_bbox':bounds,'occupied_width_fraction':round((bounds[2]-bounds[0])/im.width,3),
                'occupied_height_fraction':round((bounds[3]-bounds[1])/im.height,3),
                'edge_touch':bool(m[0].any() or m[-1].any() or m[:,0].any() or m[:,-1].any()),
                'shadow_pixel_change_from_comparison':'not available without per-layer no-shadow render',
                'visual_art_direction':'REVIEW_REQUIRED; cannot certify by geometry alone'}
            results['composition'][f.name]=ex
    (out_dir/'benchmark_results.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--assets',default='/mnt/data');parser.add_argument('--proofs',default='/mnt/data/FRAME_CORE_V6/proof');parser.add_argument('--output',default='/mnt/data/FRAME_Quality_Benchmark/output')
    a=parser.parse_args();r=run(Path(a.assets),Path(a.proofs),Path(a.output))
    for x in r['assets']:
        print(x['name'],{k:y.get('proxy_normalized_silhouette_iou','N/A') for k,y in x['methods'].items()},x['grabcut_status'])
    print('Compositions checked:',len(r['composition']),'Decision:',r['release_decision'])

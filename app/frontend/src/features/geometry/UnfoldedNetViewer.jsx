import React from 'react';

/** A net constructed from the canonical scene's measured edge lengths. */
export default function UnfoldedNetViewer({scene}) {
  if(!scene)return null;
  const a=scene.spec.base_edge, kind=scene.spec.polyhedron_type, lengths=scene.measurements.edge_lengths;
  let polygons=[];
  if(kind==='cube') {
    polygons=[[0,0],[a,0],[-a,0],[0,a],[0,-a],[0,-2*a]].map(([x,y])=>[[x,y],[x+a,y],[x+a,y+a],[x,y+a]]);
  } else {
    const vertices={A:[0,0],B:[a,0],C:[a,a],D:[0,a]};
    polygons=[Object.values(vertices)];
    for(const [u,v] of [['A','B'],['B','C'],['C','D'],['D','A']]) {
      const [x,y]=vertices[u], [vx,vy]=vertices[v], dx=(vx-x)/a,dy=(vy-y)/a;
      const su=lengths[`S-${u}`],sv=lengths[`S-${v}`];
      const t=(su*su+a*a-sv*sv)/(2*a),h=Math.sqrt(Math.max(0,su*su-t*t));
      polygons.push([[x,y],[vx,vy],[x+dx*t+dy*h,y+dy*t-dx*h]]);
    }
  }
  const points=polygons.flat(),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
  const minX=Math.min(...xs)-a*.1,minY=Math.min(...ys)-a*.1;
  return <svg aria-label="Hình khai triển từ số đo đã xác nhận" viewBox={`${minX} ${minY} ${Math.max(...xs)-minX+a*.1} ${Math.max(...ys)-minY+a*.1}`} className="w-full h-72">{polygons.map((polygon,i)=><polygon key={i} points={polygon.map(p=>p.join(',')).join(' ')} fill="#dbeafe" stroke="#1d4ed8" strokeWidth={a*.008}/>)}</svg>;
}

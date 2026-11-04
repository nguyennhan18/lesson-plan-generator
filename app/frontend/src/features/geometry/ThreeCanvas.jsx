import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

/** Renderer consumes backend coordinates only; no inferred or default solid. */
export default function ThreeCanvas({ scene, onCaptureReady, cameraPreset = "iso", showLabels = true, showAxes = false }) {
  const host = useRef(null);
  useEffect(() => {
    if (!scene?.vertices || !host.current) return;
    const world = new THREE.Scene(); world.background = new THREE.Color('#ffffff');
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    host.current.appendChild(renderer.domElement);
    const a = scene.spec.base_edge, h = scene.spec.height, scale = Math.max(a, h);
    const camera = new THREE.PerspectiveCamera(42, 1, scale / 1000, scale * 100);
    camera.position.set(a / 2 + scale * 2, h / 2 + scale * 1.5, a / 2 + scale * 2);
    if(cameraPreset==='top'){camera.position.set(a/2,h/2+scale*3,a/2+.001*scale);camera.up.set(0,0,-1);}
    if(cameraPreset==='front')camera.position.set(a/2,h/2,a/2+scale*3);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(a / 2, h / 2, a / 2); controls.enableDamping = true;
    const point = name => { const [x,y,z] = scene.vertices[name]; return new THREE.Vector3(x,z,y); };
    const edgeObjects=[],faceObjects=[];
    for (const [u,v] of scene.edges) {
      const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([point(u),point(v)]),new THREE.LineDashedMaterial({color:'#1d4ed8',dashSize:scale*.04,gapSize:scale*.025}));line.computeLineDistances();
      line.userData={mid:point(u).add(point(v)).multiplyScalar(.5)};edgeObjects.push(line);world.add(line);
    }
    for (const face of scene.faces) {
      const points = [];
      for (let i=1; i<face.length-1; i++) points.push(...point(face[0]).toArray(), ...point(face[i]).toArray(), ...point(face[i+1]).toArray());
      const geometry = new THREE.BufferGeometry(); geometry.setAttribute('position', new THREE.Float32BufferAttribute(points,3));
      const mesh=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({color:'#93c5fd',transparent:true,opacity:.18,side:THREE.DoubleSide,depthWrite:false}));faceObjects.push(mesh);world.add(mesh);
    }
    if(showAxes)world.add(new THREE.AxesHelper(scale*1.5));
    if(showLabels)for (const name of Object.keys(scene.vertices)) {
      const canvas = document.createElement('canvas'); canvas.width=128; canvas.height=64;
      const ctx = canvas.getContext('2d'); ctx.font='bold 36px sans-serif'; ctx.fillStyle='#111827'; ctx.fillText(name,12,43);
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(canvas), depthTest:false}));
      sprite.position.copy(point(name)); sprite.scale.set(scale*.2,scale*.1,1); world.add(sprite);
    }
    const resize = () => { const width=host.current?.clientWidth || 400; renderer.setSize(width,320); camera.aspect=width/320; camera.updateProjectionMatrix(); };
    resize(); const observer = new ResizeObserver(resize); observer.observe(host.current);
    const raycaster=new THREE.Raycaster();
    let frame;
    const animate = () => { controls.update();world.updateMatrixWorld(true);for(const edge of edgeObjects){const direction=edge.userData.mid.clone().sub(camera.position);const distance=direction.length();raycaster.set(camera.position,direction.normalize());const hidden=raycaster.intersectObjects(faceObjects).some(hit=>hit.distance<distance-scale*1e-5);edge.material.gapSize=hidden?scale*.025:0;}renderer.render(world,camera); frame=requestAnimationFrame(animate); }; animate();
    onCaptureReady?.(() => ({ data_url: renderer.domElement.toDataURL('image/png'), scene_fingerprint: scene.scene_fingerprint }));
    return () => { cancelAnimationFrame(frame); observer.disconnect(); controls.dispose(); onCaptureReady?.(null);
      world.traverse(o => {o.geometry?.dispose(); const materials = Array.isArray(o.material) ? o.material : [o.material]; materials.forEach(m => {m?.map?.dispose(); m?.dispose();});});
      renderer.dispose(); renderer.domElement.remove(); };
  }, [scene,cameraPreset,showLabels,showAxes]);
  return scene ? <div ref={host} className="w-full min-h-[320px]" aria-label="Mô hình từ dữ kiện đã xác nhận" /> : <p>Chưa có dữ kiện hình học đã xác nhận.</p>;
}

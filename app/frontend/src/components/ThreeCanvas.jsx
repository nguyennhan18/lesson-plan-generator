import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * ThreeCanvas - Interactive 3D WebGL Polyhedron Engine
 * High-performance Three.js renderer with PBR glassmorphic materials,
 * hidden-line rendering, and slide-specific geometric features.
 */
export default function ThreeCanvas({
  slideIndex = 0,
  polyhedronType = 'cube',
  edgeLength = 4.0,
  showHiddenLines = true,
  showVertexLabels = true,
  showAxes = false,
  cameraPreset = 'iso',
  onCameraChange
}) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const groupRef = useRef(null);
  const isDraggingRef = useRef(false);
  const prevMouseRef = useRef({ x: 0, y: 0 });
  const rotRef = useRef({ yaw: 35 * (Math.PI / 180), pitch: -22 * (Math.PI / 180), zoom: 1.15 });

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 450;
    const height = container.clientHeight || 350;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 7);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    rendererRef.current = renderer;

    container.replaceChildren(renderer.domElement);

    // 2. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x38bdf8, 2.0);
    dirLight1.position.set(5, 8, 5);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x818cf8, 1.2);
    dirLight2.position.set(-5, -5, -3);
    scene.add(dirLight2);

    // 3. Root Group for Model
    const modelGroup = new THREE.Group();
    scene.add(modelGroup);
    groupRef.current = modelGroup;

    // 4. Animation loop
    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      if (groupRef.current) {
        groupRef.current.rotation.x = rotRef.current.pitch;
        groupRef.current.rotation.y = rotRef.current.yaw;
        camera.position.z = 7 / rotRef.current.zoom;
      }
      renderer.render(scene, camera);
    };
    animate();

    // Resize handler
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animId);
      renderer.dispose();
    };
  }, []);

  // Update Camera Preset
  useEffect(() => {
    if (cameraPreset === 'iso') {
      rotRef.current.yaw = 35 * (Math.PI / 180);
      rotRef.current.pitch = -22 * (Math.PI / 180);
    } else if (cameraPreset === 'top') {
      rotRef.current.yaw = 0;
      rotRef.current.pitch = -88 * (Math.PI / 180);
    } else if (cameraPreset === 'front') {
      rotRef.current.yaw = 0;
      rotRef.current.pitch = 0;
    }
  }, [cameraPreset]);

  // Rebuild 3D Model when parameters change
  useEffect(() => {
    const group = groupRef.current;
    if (!group) return;

    // Clear previous children
    while (group.children.length > 0) {
      const obj = group.children[0];
      group.remove(obj);
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
        else obj.material.dispose();
      }
    }

    const scale = (edgeLength / 4.0) * 1.5;
    const a = scale;

    // A. AXES Oxyz
    if (showAxes) {
      const axesHelper = new THREE.AxesHelper(scale * 1.6);
      group.add(axesHelper);
    }

    // B. CUBE ABCD.A'B'C'D'
    if (polyhedronType === 'cube') {
      const v = {
        A: new THREE.Vector3(-a, -a, -a),
        B: new THREE.Vector3(a, -a, -a),
        C: new THREE.Vector3(a, -a, a),
        D: new THREE.Vector3(-a, -a, a),
        "A'": new THREE.Vector3(-a, a, -a),
        "B'": new THREE.Vector3(a, a, -a),
        "C'": new THREE.Vector3(a, a, a),
        "D'": new THREE.Vector3(-a, a, a)
      };

      // 1. Semi-transparent Glass Mesh Body
      const boxGeo = new THREE.BoxGeometry(a * 2, a * 2, a * 2);
      const glassMat = new THREE.MeshPhysicalMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.18,
        roughness: 0.1,
        metalness: 0.05,
        transmission: 0.8,
        depthWrite: false
      });
      const cubeMesh = new THREE.Mesh(boxGeo, glassMat);
      group.add(cubeMesh);

      // 2. Wireframe Edges (Cyan outer glow)
      const edgeEdges = [
        [v.A, v.B], [v.B, v.C], [v.C, v.D], [v.D, v.A],
        [v["A'"], v["B'"]], [v["B'"], v["C'"]], [v["C'"], v["D'"]], [v["D'"], v["A'"]],
        [v.A, v["A'"]], [v.B, v["B'"]], [v.C, v["C'"]], [v.D, v["D'"]]
      ];

      const lineMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, linewidth: 2 });
      edgeEdges.forEach(([p1, p2]) => {
        const geo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
        const line = new THREE.Line(geo, lineMat);
        group.add(line);
      });

      // 3. Vertex Spheres
      if (showVertexLabels) {
        const sphereGeo = new THREE.SphereGeometry(0.06, 16, 16);
        const sphereMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
        Object.entries(v).forEach(([name, pt]) => {
          const sphere = new THREE.Mesh(sphereGeo, sphereMat);
          sphere.position.copy(pt);
          group.add(sphere);

          // Billboard sprite label
          const canvas = document.createElement('canvas');
          canvas.width = 64;
          canvas.height = 64;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 36px monospace';
          ctx.fillText(name, 12, 45);

          const tex = new THREE.CanvasTexture(canvas);
          const spriteMat = new THREE.SpriteMaterial({ map: tex });
          const sprite = new THREE.Sprite(spriteMat);
          sprite.position.copy(pt).add(new THREE.Vector3(0.12, 0.12, 0.12));
          sprite.scale.set(0.4, 0.4, 1);
          group.add(sprite);
        });
      }

      // 4. SLIDE-SPECIFIC 3D HIGHLIGHTS
      // Slide 1: Diagonal AC' = a√3 (Red Laser Cylinder)
      if (slideIndex === 1) {
        const diagGeo = new THREE.BufferGeometry().setFromPoints([v.A, v["C'"]]);
        const diagMat = new THREE.LineBasicMaterial({ color: 0xf43f5e, linewidth: 4 });
        const diagLine = new THREE.Line(diagGeo, diagMat);
        group.add(diagLine);

        // Floor diagonal AC
        const floorGeo = new THREE.BufferGeometry().setFromPoints([v.A, v.C]);
        const floorMat = new THREE.LineDashedMaterial({ color: 0xfbbf24, dashSize: 0.15, gapSize: 0.1 });
        const floorLine = new THREE.Line(floorGeo, floorMat);
        floorLine.computeLineDistances();
        group.add(floorLine);
      }

      // Slide 2: Altitude AH ⊥ B'D'
      if (slideIndex === 2) {
        const midBD = new THREE.Vector3().addVectors(v["B'"], v["D'"]).multiplyScalar(0.5);
        const hGeo = new THREE.BufferGeometry().setFromPoints([v.A, midBD]);
        const hMat = new THREE.LineBasicMaterial({ color: 0x10b981, linewidth: 3 });
        const hLine = new THREE.Line(hGeo, hMat);
        group.add(hLine);
      }

      // Slide 3: Cross section plane (A'BD)
      if (slideIndex === 3) {
        const triGeo = new THREE.BufferGeometry();
        const verts = new Float32Array([
          v["A'"].x, v["A'"].y, v["A'"].z,
          v.B.x, v.B.y, v.B.z,
          v.D.x, v.D.y, v.D.z,
        ]);
        triGeo.setAttribute('position', new THREE.BufferAttribute(verts, 3));
        triGeo.computeVertexNormals();

        const triMat = new THREE.MeshBasicMaterial({
          color: 0x00f0ff,
          transparent: true,
          opacity: 0.45,
          side: THREE.DoubleSide
        });
        const triMesh = new THREE.Mesh(triGeo, triMat);
        group.add(triMesh);

        // Highlight border
        const borderGeo = new THREE.BufferGeometry().setFromPoints([v["A'"], v.B, v.D, v["A'"]]);
        const borderMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, linewidth: 3 });
        const borderLine = new THREE.Line(borderGeo, borderMat);
        group.add(borderLine);
      }
    }
  }, [polyhedronType, edgeLength, slideIndex, showHiddenLines, showVertexLabels, showAxes]);

  // Mouse Orbit interaction
  const handleMouseDown = (e) => {
    isDraggingRef.current = true;
    prevMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - prevMouseRef.current.x;
    const dy = e.clientY - prevMouseRef.current.y;

    rotRef.current.yaw += dx * 0.008;
    rotRef.current.pitch = Math.max(-Math.PI * 0.48, Math.min(Math.PI * 0.48, rotRef.current.pitch + dy * 0.008));

    prevMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    rotRef.current.zoom = Math.max(0.6, Math.min(2.5, rotRef.current.zoom - e.deltaY * 0.0015));
  };

  return (
    <div
      ref={mountRef}
      className="w-full h-full relative cursor-grab active:cursor-grabbing rounded-xl overflow-hidden"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
    >
      <div className="absolute bottom-2 right-2 px-2 py-1 bg-slate-900/80 backdrop-blur rounded text-[11px] text-slate-400 pointer-events-none border border-slate-800 flex items-center gap-1">
        <span>🖱️ Kéo xoay 360° • Cuộn zoom</span>
      </div>
    </div>
  );
}

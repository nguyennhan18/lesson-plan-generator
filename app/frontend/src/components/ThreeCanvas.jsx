import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { RotateCw, ZoomIn, ZoomOut, Compass, RefreshCw } from 'lucide-react';

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
  showAxes = true,
  cameraPreset = 'iso',
  onCameraChange
}) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const groupRef = useRef(null);
  const isDraggingRef = useRef(false);
  const dragModeRef = useRef('orbit'); // 'orbit' (Ox + Oy) | 'roll' (Oz)
  const prevPointerRef = useRef({ x: 0, y: 0 });

  // Góc xoay mục tiêu (Target Euler angles) quanh 3 trục Ox, Oy, Oz và zoom
  const targetRotRef = useRef({
    rotX: -22 * (Math.PI / 180), // X-axis (Pitch / Ox)
    rotY: 35 * (Math.PI / 180),  // Y-axis (Yaw / Oy)
    rotZ: 0,                     // Z-axis (Roll / Oz)
    zoom: 1.15
  });

  // Góc xoay hiện tại phục vụ nội suy mượt mà 60 FPS (Lerp Damping chống giật lag)
  const curRotRef = useRef({
    rotX: -22 * (Math.PI / 180),
    rotY: 35 * (Math.PI / 180),
    rotZ: 0,
    zoom: 1.15
  });

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

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    rendererRef.current = renderer;

    container.replaceChildren(renderer.domElement);

    // 2. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.95);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x38bdf8, 2.2);
    dirLight1.position.set(5, 8, 5);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x818cf8, 1.4);
    dirLight2.position.set(-5, -5, -3);
    scene.add(dirLight2);

    // 3. Root Group for Model
    const modelGroup = new THREE.Group();
    scene.add(modelGroup);
    groupRef.current = modelGroup;

    // 4. Animation loop với nội suy mượt mà 60 FPS (Lerp Damping - DoD Ngày 11 mượt mà không giật lag)
    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      const cur = curRotRef.current;
      const target = targetRotRef.current;

      // Hệ số nội suy mượt (0.18 giúp chuyển động êm ái, bám sát chuột tức thì)
      const factor = 0.20;
      cur.rotX += (target.rotX - cur.rotX) * factor;
      cur.rotY += (target.rotY - cur.rotY) * factor;
      cur.rotZ += (target.rotZ - cur.rotZ) * factor;
      cur.zoom += (target.zoom - cur.zoom) * factor;

      if (groupRef.current) {
        groupRef.current.rotation.x = cur.rotX;
        groupRef.current.rotation.y = cur.rotY;
        groupRef.current.rotation.z = cur.rotZ;
        camera.position.z = 7.0 / Math.max(0.5, cur.zoom);
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

  // Cập nhật góc nhìn Camera Preset chuẩn SGK
  useEffect(() => {
    if (cameraPreset === 'iso') {
      targetRotRef.current.rotX = -22 * (Math.PI / 180);
      targetRotRef.current.rotY = 35 * (Math.PI / 180);
      targetRotRef.current.rotZ = 0;
      targetRotRef.current.zoom = 1.15;
    } else if (cameraPreset === 'top') {
      targetRotRef.current.rotX = -88 * (Math.PI / 180);
      targetRotRef.current.rotY = 0;
      targetRotRef.current.rotZ = 0;
      targetRotRef.current.zoom = 1.25;
    } else if (cameraPreset === 'front') {
      targetRotRef.current.rotX = 0;
      targetRotRef.current.rotY = 0;
      targetRotRef.current.rotZ = 0;
      targetRotRef.current.zoom = 1.20;
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

    // Helper: Tạo nhãn tên đỉnh dạng Billboard Canvas Sprite
    const addVertexSprite = (name, pt, offset = new THREE.Vector3(0.12, 0.12, 0.12)) => {
      if (!showVertexLabels) return;
      const sphereGeo = new THREE.SphereGeometry(0.055, 16, 16);
      const sphereMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const sphere = new THREE.Mesh(sphereGeo, sphereMat);
      sphere.position.copy(pt);
      group.add(sphere);

      const canvas = document.createElement('canvas');
      canvas.width = 64;
      canvas.height = 64;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 36px sans-serif';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
      ctx.shadowBlur = 4;
      ctx.fillText(name, 12, 45);

      const tex = new THREE.CanvasTexture(canvas);
      const spriteMat = new THREE.SpriteMaterial({ map: tex, depthTest: false });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.position.copy(pt).add(offset);
      sprite.scale.set(0.42, 0.42, 1);
      group.add(sprite);
    };

    // Helper: Tạo đoạn thẳng nét liền hoặc nét đứt chuẩn SGK
    const addEdge = (p1, p2, color = 0x38bdf8, isDashed = false, linewidth = 2) => {
      const geo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
      if (isDashed && showHiddenLines) {
        const mat = new THREE.LineDashedMaterial({
          color,
          linewidth,
          dashSize: 0.14,
          gapSize: 0.10
        });
        const line = new THREE.Line(geo, mat);
        line.computeLineDistances();
        group.add(line);
      } else if (!isDashed) {
        const mat = new THREE.LineBasicMaterial({ color, linewidth });
        const line = new THREE.Line(geo, mat);
        group.add(line);
      }
    };

    // Helper: Ký hiệu góc vuông 3D tại đỉnh (Right-Angle Symbol)
    const addRightAngle = (origin, dir1, dir2, size = 0.22, color = 0x34d399) => {
      const u = dir1.clone().normalize().multiplyScalar(size);
      const v = dir2.clone().normalize().multiplyScalar(size);
      const p1 = origin.clone().add(u);
      const p2 = origin.clone().add(u).add(v);
      const p3 = origin.clone().add(v);
      const geo = new THREE.BufferGeometry().setFromPoints([p1, p2, p3]);
      const mat = new THREE.LineBasicMaterial({ color, linewidth: 2 });
      const line = new THREE.Line(geo, mat);
      group.add(line);
    };

    // Helper: Tạo khối Mesh bán trong suốt PBR Glassmorphic
    const addMeshTriangles = (triangles, color = 0x38bdf8, opacity = 0.20) => {
      const positions = [];
      triangles.forEach(([p1, p2, p3]) => {
        positions.push(p1.x, p1.y, p1.z);
        positions.push(p2.x, p2.y, p2.z);
        positions.push(p3.x, p3.y, p3.z);
      });
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geo.computeVertexNormals();

      const mat = new THREE.MeshPhysicalMaterial({
        color,
        transparent: true,
        opacity,
        roughness: 0.15,
        metalness: 0.05,
        transmission: 0.75,
        depthWrite: false,
        side: THREE.DoubleSide
      });
      const mesh = new THREE.Mesh(geo, mat);
      group.add(mesh);
    };

    // Helper: Cấu hình Hệ trục Tọa độ Descartes Oxyz & Mặt phẳng đáy Oxy chuẩn SGK (Task 11.4)
    const addCartesianSystemAndFloor = (origin, axisLen, floorY, floorSize) => {
      if (!showAxes) return;

      // 1. Mặt phẳng đáy (Oxy) dạng lưới GridHelper + Kính mờ
      const gridCenter = new THREE.Vector3(origin.x + floorSize * 0.22, floorY, origin.z + floorSize * 0.22);
      const grid = new THREE.GridHelper(floorSize, 14, 0x38bdf8, 0x1e293b);
      grid.position.copy(gridCenter);
      group.add(grid);

      // Mặt sàn bán trong suốt
      const planeGeo = new THREE.PlaneGeometry(floorSize, floorSize);
      const planeMat = new THREE.MeshBasicMaterial({
        color: 0x050c1e,
        transparent: true,
        opacity: 0.45,
        depthWrite: false,
        side: THREE.DoubleSide
      });
      const planeMesh = new THREE.Mesh(planeGeo, planeMat);
      planeMesh.rotation.x = -Math.PI / 2;
      planeMesh.position.copy(gridCenter);
      group.add(planeMesh);

      // Nhãn mặt phẳng đáy (Oxy)
      addVertexSprite('(Oxy)', new THREE.Vector3(origin.x + floorSize * 0.48, floorY, origin.z + floorSize * 0.48), new THREE.Vector3(0, 0.12, 0));

      // 2. Gốc tọa độ O (Điểm cầu màu trắng)
      const originSphereGeo = new THREE.SphereGeometry(0.065, 16, 16);
      const originSphereMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const originSphere = new THREE.Mesh(originSphereGeo, originSphereMat);
      originSphere.position.copy(origin);
      group.add(originSphere);

      // 3. Ba trục вектор Descartes có mũi tên nón định hướng
      const addAxisVector = (dir, length, color, labelText) => {
        const dirNorm = dir.clone().normalize();
        const arrow = new THREE.ArrowHelper(dirNorm, origin, length, color, 0.24, 0.11);
        group.add(arrow);

        const tipPos = origin.clone().add(dirNorm.clone().multiplyScalar(length + 0.16));
        addVertexSprite(labelText, tipPos, new THREE.Vector3(0, 0, 0));
      };

      // Trục hoành Ox (Màu đỏ hồng #f43f5e) nằm trên mặt đáy hướng theo cạnh đáy
      addAxisVector(new THREE.Vector3(1, 0, 0), axisLen, 0xf43f5e, 'x');

      // Trục tung Oy (Màu xanh ngọc #10b981) nằm trên mặt đáy vuông góc với Ox
      addAxisVector(new THREE.Vector3(0, 0, 1), axisLen, 0x10b981, 'y');

      // Trục cao độ Oz (Màu xanh dương #38bdf8) hướng thẳng đứng lên trên
      addAxisVector(new THREE.Vector3(0, 1, 0), axisLen * 1.15, 0x38bdf8, 'z');
    };

    // Chuẩn hóa loại khối đa diện
    const normType = String(polyhedronType || 'pyramid_square').toLowerCase();

    // =========================================================================
    // 1. HÌNH CHÓP TỨ GIÁC S.ABCD (SA ⊥ Đáy ABCD) — TASK 11.2
    // =========================================================================
    if (normType === 'pyramid_square' || normType === 'rectangular_pyramid' || normType === 'pyramid4') {
      const yBase = -a * 0.9;
      const yApex = a * 1.35;
      const xA = -a * 0.95;
      const zA = -a * 0.85;
      const w = a * 1.85;
      const d = a * 1.70;

      const v = {
        A: new THREE.Vector3(xA, yBase, zA),           // Chân đường cao, góc khuất sau-trái
        B: new THREE.Vector3(xA, yBase, zA + d),       // Đáy trước-trái
        C: new THREE.Vector3(xA + w, yBase, zA + d),   // Đáy trước-phải
        D: new THREE.Vector3(xA + w, yBase, zA),       // Đáy sau-phải
        S: new THREE.Vector3(xA, yApex, zA)            // Đỉnh S vuông góc với A: SA ⊥ (ABCD)
      };

      // Tâm đáy O
      const midAC = new THREE.Vector3().addVectors(v.A, v.C).multiplyScalar(0.5);

      // 1. Mesh thân kính 3D (Đáy + 4 mặt bên)
      addMeshTriangles([
        [v.A, v.B, v.C], [v.A, v.C, v.D], // Đáy ABCD
        [v.S, v.A, v.B],                  // Mặt bên SAB
        [v.S, v.B, v.C],                  // Mặt bên SBC
        [v.S, v.C, v.D],                  // Mặt bên SCD
        [v.S, v.D, v.A]                   // Mặt bên SDA
      ], 0x38bdf8, 0.22);

      // 2. Cạnh nét liền (Nhìn thấy từ góc SGK)
      addEdge(v.B, v.C, 0x38bdf8, false, 2.5);
      addEdge(v.C, v.D, 0x38bdf8, false, 2.5);
      addEdge(v.S, v.B, 0x38bdf8, false, 2.5);
      addEdge(v.S, v.C, 0x38bdf8, false, 2.5);
      addEdge(v.S, v.D, 0x38bdf8, false, 2.5);

      // 3. Cạnh nét đứt (Cạnh khuất phía sau đáy và đường cao SA)
      addEdge(v.A, v.B, 0x38bdf8, true, 2.5);
      addEdge(v.A, v.D, 0x38bdf8, true, 2.5);
      addEdge(v.S, v.A, 0x34d399, true, 3.0); // SA đường cao màu xanh ngọc nét đứt

      // 4. Hai đường chéo đáy nét đứt cắt nhau tại O
      addEdge(v.A, v.C, 0xfbbf24, true, 1.5);
      addEdge(v.B, v.D, 0xfbbf24, true, 1.5);

      // 5. Ký hiệu góc vuông SA ⊥ AB và SA ⊥ AD tại chân đường cao A
      addRightAngle(v.A, new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0, 1), 0.22, 0x34d399);
      addRightAngle(v.A, new THREE.Vector3(0, 1, 0), new THREE.Vector3(1, 0, 0), 0.22, 0x34d399);

      // 6. Nhãn tên các đỉnh
      addVertexSprite('A', v.A, new THREE.Vector3(-0.16, -0.12, -0.12));
      addVertexSprite('B', v.B, new THREE.Vector3(-0.14, -0.12, 0.16));
      addVertexSprite('C', v.C, new THREE.Vector3(0.16, -0.12, 0.16));
      addVertexSprite('D', v.D, new THREE.Vector3(0.16, -0.12, -0.14));
      addVertexSprite('S', v.S, new THREE.Vector3(0.0, 0.22, 0.0));
      addVertexSprite('O', midAC, new THREE.Vector3(0.0, -0.16, 0.0));

      // 7. Cấu hình hệ trục tọa độ Oxyz & mặt phẳng đáy Oxy (Task 11.4)
      addCartesianSystemAndFloor(v.A, a * 2.2, yBase, a * 3.8);
    }

    // =========================================================================
    // 2. HÌNH CHÓP TAM GIÁC S.ABC (SA ⊥ Đáy ABC) — TASK 11.2
    // =========================================================================
    else if (normType === 'pyramid_triangle' || normType === 'triangular_pyramid' || normType === 'pyramid3' || normType === 'tetrahedron') {
      const yBase = -a * 0.9;
      const yApex = a * 1.35;
      const xA = -a * 0.75;
      const zA = -a * 0.65;

      const v = {
        A: new THREE.Vector3(xA, yBase, zA),            // Chân đường cao, sau-trái
        B: new THREE.Vector3(xA - 0.2 * a, yBase, zA + a * 1.8), // Đáy trước-trái
        C: new THREE.Vector3(xA + a * 1.9, yBase, zA + a * 0.7), // Đáy trước-phải
        S: new THREE.Vector3(xA, yApex, zA)             // Đỉnh S vuông góc với A: SA ⊥ (ABC)
      };

      // Điểm H trên BC sao cho AH ⊥ BC (Định lý 3 đường vuông góc)
      const vecBC = new THREE.Vector3().subVectors(v.C, v.B);
      const vecBA = new THREE.Vector3().subVectors(v.A, v.B);
      const proj = vecBA.dot(vecBC) / vecBC.lengthSq();
      const ptH = new THREE.Vector3().copy(v.B).add(vecBC.clone().multiplyScalar(Math.max(0.2, Math.min(0.8, proj))));

      // 1. Mesh thân kính 3D (Đáy + 3 mặt bên)
      addMeshTriangles([
        [v.A, v.B, v.C], // Đáy ABC
        [v.S, v.A, v.B], // Mặt bên SAB
        [v.S, v.B, v.C], // Mặt bên SBC
        [v.S, v.C, v.A]  // Mặt bên SCA
      ], 0x818cf8, 0.22);

      // 2. Cạnh nét liền (Nhìn thấy)
      addEdge(v.B, v.C, 0x818cf8, false, 2.5);
      addEdge(v.S, v.B, 0x818cf8, false, 2.5);
      addEdge(v.S, v.C, 0x818cf8, false, 2.5);

      // 3. Cạnh nét đứt (Cạnh khuất phía sau đáy và đường cao SA)
      addEdge(v.A, v.B, 0x818cf8, true, 2.5);
      addEdge(v.A, v.C, 0x818cf8, true, 2.5);
      addEdge(v.S, v.A, 0x34d399, true, 3.0); // Đường cao SA màu xanh ngọc

      // 4. Đường cao phụ AH ⊥ BC nét đứt & SH ⊥ BC nét liền (Minh họa Định lý 3 đường vuông góc)
      addEdge(v.A, ptH, 0xf43f5e, true, 2.0);  // AH nét đứt màu đỏ
      addEdge(v.S, ptH, 0xf43f5e, false, 2.0); // SH nét liền màu đỏ

      // 5. Ký hiệu góc vuông SA ⊥ AB và SA ⊥ AC
      addRightAngle(v.A, new THREE.Vector3(0, 1, 0), new THREE.Vector3().subVectors(v.B, v.A), 0.20, 0x34d399);
      addRightAngle(v.A, new THREE.Vector3(0, 1, 0), new THREE.Vector3().subVectors(v.C, v.A), 0.20, 0x34d399);
      addRightAngle(ptH, new THREE.Vector3().subVectors(v.A, ptH), new THREE.Vector3().subVectors(v.C, v.B), 0.18, 0xf43f5e);

      // 6. Nhãn tên các đỉnh
      addVertexSprite('A', v.A, new THREE.Vector3(-0.16, -0.12, -0.12));
      addVertexSprite('B', v.B, new THREE.Vector3(-0.16, -0.12, 0.16));
      addVertexSprite('C', v.C, new THREE.Vector3(0.16, -0.12, 0.14));
      addVertexSprite('S', v.S, new THREE.Vector3(0.0, 0.22, 0.0));
      addVertexSprite('H', ptH, new THREE.Vector3(0.12, -0.14, 0.12));

      // 7. Cấu hình hệ trục tọa độ Oxyz & mặt phẳng đáy Oxy (Task 11.4)
      addCartesianSystemAndFloor(v.A, a * 2.2, yBase, a * 3.8);
    }

    // =========================================================================
    // 3. LĂNG TRỤ ĐỨNG TAM GIÁC ABC.A'B'C' (TASK 11.2)
    // =========================================================================
    else if (normType === 'prism_triangle' || normType === 'triangular_prism' || normType === 'prism') {
      const yBottom = -a * 1.0;
      const yTop = a * 1.0;
      const xA = -a * 0.75;
      const zA = -a * 0.65;

      const v = {
        A: new THREE.Vector3(xA, yBottom, zA),
        B: new THREE.Vector3(xA - 0.2 * a, yBottom, zA + a * 1.7),
        C: new THREE.Vector3(xA + a * 1.8, yBottom, zA + a * 0.6),
        "A'": new THREE.Vector3(xA, yTop, zA),
        "B'": new THREE.Vector3(xA - 0.2 * a, yTop, zA + a * 1.7),
        "C'": new THREE.Vector3(xA + a * 1.8, yTop, zA + a * 0.6)
      };

      // 1. Mesh lăng trụ kính
      addMeshTriangles([
        [v.A, v.B, v.C],             // Đáy dưới ABC
        [v["A'"], v["B'"], v["C'"]], // Đáy trên A'B'C'
        [v.A, v.B, v["B'"]], [v.A, v["B'"], v["A'"]], // Mặt bên ABB'A'
        [v.B, v.C, v["C'"]], [v.B, v["C'"], v["B'"]], // Mặt bên BCC'B'
        [v.A, v.C, v["C'"]], [v.A, v["C'"], v["A'"]]  // Mặt bên ACC'A'
      ], 0x38bdf8, 0.20);

      // 2. Cạnh nét liền
      addEdge(v.B, v.C, 0x38bdf8, false, 2.5);
      addEdge(v["A'"], v["B'"], 0x38bdf8, false, 2.5);
      addEdge(v["B'"], v["C'"], 0x38bdf8, false, 2.5);
      addEdge(v["C'"], v["A'"], 0x38bdf8, false, 2.5);
      addEdge(v.B, v["B'"], 0x38bdf8, false, 2.5);
      addEdge(v.C, v["C'"], 0x38bdf8, false, 2.5);

      // 3. Cạnh nét đứt khuất sau
      addEdge(v.A, v.B, 0x38bdf8, true, 2.5);
      addEdge(v.A, v.C, 0x38bdf8, true, 2.5);
      addEdge(v.A, v["A'"], 0x34d399, true, 2.5);

      // 4. Nhãn tên đỉnh
      Object.entries(v).forEach(([name, pt]) => {
        addVertexSprite(name, pt, new THREE.Vector3(0.12, 0.12, 0.12));
      });

      // 5. Cấu hình hệ trục tọa độ Oxyz & mặt phẳng đáy Oxy (Task 11.4)
      addCartesianSystemAndFloor(v.A, a * 2.2, yBottom, a * 3.8);
    }

    // =========================================================================
    // 4. HÌNH LẬP PHƯƠNG ABCD.A'B'C'D' (TASK 11.2)
    // =========================================================================
    else if (normType === 'cube' || normType === 'box') {
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

      // 2. Wireframe Edges
      const edgeEdges = [
        [v.A, v.B], [v.B, v.C], [v.C, v.D], [v.D, v.A],
        [v["A'"], v["B'"]], [v["B'"], v["C'"]], [v["C'"], v["D'"]], [v["D'"], v["A'"]],
        [v.A, v["A'"]], [v.B, v["B'"]], [v.C, v["C'"]], [v.D, v["D'"]]
      ];

      edgeEdges.forEach(([p1, p2]) => {
        addEdge(p1, p2, 0x38bdf8, false, 2);
      });

      // 3. Vertex Spheres & Labels
      Object.entries(v).forEach(([name, pt]) => {
        addVertexSprite(name, pt);
      });

      // 4. Slide-specific highlights
      if (slideIndex === 1 || slideIndex === 2) {
        // Đường chéo AC' = a√3
        addEdge(v.A, v["C'"], 0xf43f5e, false, 3.5);
        addEdge(v.A, v.C, 0xfbbf24, true, 2.0);
      }

      // 5. Cấu hình hệ trục tọa độ Oxyz & mặt phẳng đáy Oxy (Task 11.4)
      addCartesianSystemAndFloor(v.A, a * 2.2, -a, a * 3.8);
    }
  }, [polyhedronType, edgeLength, slideIndex, showHiddenLines, showVertexLabels, showAxes]);

  // =========================================================================
  // TASK 11.3: ĐIỀU KHIỂN CHUỘT XOAY 360° QUANH 3 TRỤC Ox, Oy, Oz & CUỘN ZOOM
  // =========================================================================
  const handlePointerDown = (e) => {
    isDraggingRef.current = true;
    prevPointerRef.current = { x: e.clientX, y: e.clientY };

    // Nhấp chuột phải hoặc giữ Shift -> Xoay quanh trục Oz (Roll)
    // Nhấp chuột trái -> Xoay tự do 360° quanh Ox và Oy
    if (e.button === 2 || e.shiftKey) {
      dragModeRef.current = 'roll';
    } else {
      dragModeRef.current = 'orbit';
    }

    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch (_) {}
  };

  const handlePointerMove = (e) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - prevPointerRef.current.x;
    const dy = e.clientY - prevPointerRef.current.y;

    if (dragModeRef.current === 'roll') {
      // Xoay quanh trục Oz
      targetRotRef.current.rotZ += dx * 0.009;
    } else {
      // Xoay 360 độ quanh Ox (Pitch / Lên-Xuống) và Oy (Yaw / Trái-Phải) không bị khóa góc
      targetRotRef.current.rotY += dx * 0.0085;
      targetRotRef.current.rotX += dy * 0.0085;
    }

    prevPointerRef.current = { x: e.clientX, y: e.clientY };
  };

  const handlePointerUp = (e) => {
    isDraggingRef.current = false;
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch (_) {}
  };

  // Cuộn chuột phóng to / thu nhỏ mượt mà
  const handleWheel = (e) => {
    e.preventDefault();
    targetRotRef.current.zoom = Math.max(0.55, Math.min(2.80, targetRotRef.current.zoom - e.deltaY * 0.0016));
  };

  // Nút xoay nhanh từng trục Ox, Oy, Oz một góc 45 độ
  const handleRotateStep = (axis, angleDeg) => {
    const rad = angleDeg * (Math.PI / 180);
    if (axis === 'X') targetRotRef.current.rotX += rad;
    if (axis === 'Y') targetRotRef.current.rotY += rad;
    if (axis === 'Z') targetRotRef.current.rotZ += rad;
  };

  // Đặt lại góc nhìn chuẩn SGK
  const handleResetCamera = () => {
    targetRotRef.current.rotX = -22 * (Math.PI / 180);
    targetRotRef.current.rotY = 35 * (Math.PI / 180);
    targetRotRef.current.rotZ = 0;
    targetRotRef.current.zoom = 1.15;
  };

  // Phóng to / Thu nhỏ bằng nút
  const handleZoomStep = (delta) => {
    targetRotRef.current.zoom = Math.max(0.55, Math.min(2.80, targetRotRef.current.zoom + delta));
  };

  return (
    <div
      ref={mountRef}
      className="w-full h-full relative cursor-grab active:cursor-grabbing rounded-xl overflow-hidden select-none"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      onWheel={handleWheel}
      onContextMenu={(e) => e.preventDefault()}
    >
      {/* Thanh điều khiển nhanh 3 trục Ox, Oy, Oz & Zoom (Task 11.3) */}
      <div className="absolute top-2 right-2 flex items-center gap-1 z-20 bg-slate-950/85 backdrop-blur-md p-1 rounded-lg border border-slate-800 shadow-xl text-[10px]">
        <button
          type="button"
          onClick={() => handleRotateStep('X', 45)}
          className="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-rose-300 hover:text-white border border-rose-900/60 font-mono transition"
          title="Xoay 45° quanh trục Ox"
        >
          Ox +45°
        </button>
        <button
          type="button"
          onClick={() => handleRotateStep('Y', 45)}
          className="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-emerald-300 hover:text-white border border-emerald-900/60 font-mono transition"
          title="Xoay 45° quanh trục Oy"
        >
          Oy +45°
        </button>
        <button
          type="button"
          onClick={() => handleRotateStep('Z', 45)}
          className="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-amber-300 hover:text-white border border-amber-900/60 font-mono transition"
          title="Xoay 45° quanh trục Oz"
        >
          Oz +45°
        </button>
        <div className="w-[1px] h-3 bg-slate-700 mx-0.5" />
        <button
          type="button"
          onClick={() => handleZoomStep(0.2)}
          className="p-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-400 transition"
          title="Phóng to"
        >
          <ZoomIn size={12} />
        </button>
        <button
          type="button"
          onClick={() => handleZoomStep(-0.2)}
          className="p-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-400 transition"
          title="Thu nhỏ"
        >
          <ZoomOut size={12} />
        </button>
        <button
          type="button"
          onClick={handleResetCamera}
          className="p-1 rounded bg-slate-900 hover:bg-slate-800 text-cyan-400 hover:text-white transition"
          title="Đặt lại góc nhìn chuẩn SGK"
        >
          <RefreshCw size={12} />
        </button>
      </div>

      {/* Chú thích điều khiển trực quan */}
      <div className="absolute bottom-2 left-2 px-2 py-0.5 bg-slate-950/80 backdrop-blur rounded text-[10px] text-slate-400 pointer-events-none border border-slate-800 flex items-center gap-2">
        <span className="flex items-center gap-1">
          <RotateCw size={10} className="text-cyan-400" />
          <span>Chuột trái: Xoay 360° Ox, Oy</span>
        </span>
        <span className="text-slate-600">•</span>
        <span>Shift + Chuột: Xoay Oz</span>
        <span className="text-slate-600">•</span>
        <span>Cuộn: Zoom</span>
      </div>
    </div>
  );
}

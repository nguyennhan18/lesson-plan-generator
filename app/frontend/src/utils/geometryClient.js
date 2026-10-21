/**
 * geometryClient.js — Client Service Tọa Độ Hóa & Tham Số Hình Học 3D (Task 12.2)
 * Hỗ trợ tính toán tức thì (Local 0ms) và đồng bộ bất đồng bộ qua Backend API:
 * POST /api/v1/geometry/parametric-coordinates
 */

/**
 * Tính toán tọa độ không gian Descartes Oxyz và các đại lượng hình học cục bộ (0ms).
 * Đảm bảo sự kiện oninput khi kéo slider đạt tốc độ phản hồi 60 FPS mượt mà.
 */
export function computeParametricCoordinatesLocal(polyhedronType = 'pyramid_square', height = 4.0, baseEdge = 4.0) {
  const h = Math.max(0.5, Math.min(20.0, Number(height) || 4.0));
  const a = Math.max(0.5, Math.min(20.0, Number(baseEdge) || 4.0));
  const normType = String(polyhedronType || 'pyramid_square').toLowerCase().trim();

  let vertices = {};
  let measurements = {};
  let apex = { x: 0.0, y: 0.0, z: Number(h.toFixed(2)) };

  // 1. Chóp tứ giác S.ABCD (SA ⊥ Đáy ABCD, A là gốc O)
  if (normType.includes('square') || normType.includes('pyramid4') || normType === 'pyramid') {
    vertices = {
      A: { x: 0.0, y: 0.0, z: 0.0 },
      B: { x: Number(a.toFixed(2)), y: 0.0, z: 0.0 },
      C: { x: Number(a.toFixed(2)), y: Number(a.toFixed(2)), z: 0.0 },
      D: { x: 0.0, y: Number(a.toFixed(2)), z: 0.0 },
      S: { x: 0.0, y: 0.0, z: Number(h.toFixed(2)) },
      O: { x: Number((a / 2).toFixed(2)), y: Number((a / 2).toFixed(2)), z: 0.0 }
    };

    const baseArea = a * a;
    const volume = (1.0 / 3.0) * baseArea * h;
    const diag = a * Math.SQRT2;
    const sc = Math.sqrt(h * h + 2 * a * a);

    measurements = {
      base_area: Number(baseArea.toFixed(2)),
      height: Number(h.toFixed(2)),
      volume: Number(volume.toFixed(2)),
      lateral_edge_sa: Number(h.toFixed(2)),
      lateral_edge_sc: Number(sc.toFixed(2)),
      base_diagonal: Number(diag.toFixed(2))
    };
  }
  // 2. Chóp tam giác S.ABC
  else if (normType.includes('triangle') && !normType.includes('prism')) {
    vertices = {
      A: { x: 0.0, y: 0.0, z: 0.0 },
      B: { x: Number(a.toFixed(2)), y: 0.0, z: 0.0 },
      C: { x: 0.0, y: Number(a.toFixed(2)), z: 0.0 },
      S: { x: 0.0, y: 0.0, z: Number(h.toFixed(2)) },
      H: { x: Number((a / 2).toFixed(2)), y: Number((a / 2).toFixed(2)), z: 0.0 }
    };

    const baseArea = 0.5 * a * a;
    const volume = (1.0 / 3.0) * baseArea * h;

    measurements = {
      base_area: Number(baseArea.toFixed(2)),
      height: Number(h.toFixed(2)),
      volume: Number(volume.toFixed(2)),
      lateral_edge_sa: Number(h.toFixed(2))
    };
  }
  // 3. Lăng trụ tam giác
  else if (normType.includes('prism')) {
    vertices = {
      A: { x: 0.0, y: 0.0, z: 0.0 },
      B: { x: Number(a.toFixed(2)), y: 0.0, z: 0.0 },
      C: { x: 0.0, y: Number(a.toFixed(2)), z: 0.0 },
      "A'": { x: 0.0, y: 0.0, z: Number(h.toFixed(2)) },
      "B'": { x: Number(a.toFixed(2)), y: 0.0, z: Number(h.toFixed(2)) },
      "C'": { x: 0.0, y: Number(a.toFixed(2)), z: Number(h.toFixed(2)) }
    };

    const baseArea = 0.5 * a * a;
    const volume = baseArea * h;

    measurements = {
      base_area: Number(baseArea.toFixed(2)),
      height: Number(h.toFixed(2)),
      volume: Number(volume.toFixed(2)),
      lateral_edge: Number(h.toFixed(2))
    };
  }
  // 4. Lập phương
  else {
    vertices = {
      A: { x: 0.0, y: 0.0, z: 0.0 },
      B: { x: Number(a.toFixed(2)), y: 0.0, z: 0.0 },
      C: { x: Number(a.toFixed(2)), y: Number(a.toFixed(2)), z: 0.0 },
      D: { x: 0.0, y: Number(a.toFixed(2)), z: 0.0 },
      "A'": { x: 0.0, y: 0.0, z: Number(a.toFixed(2)) },
      "B'": { x: Number(a.toFixed(2)), y: 0.0, z: Number(a.toFixed(2)) },
      "C'": { x: Number(a.toFixed(2)), y: Number(a.toFixed(2)), z: Number(a.toFixed(2)) },
      "D'": { x: 0.0, y: Number(a.toFixed(2)), z: Number(a.toFixed(2)) }
    };

    const baseArea = a * a;
    const volume = a * a * a;

    measurements = {
      base_area: Number(baseArea.toFixed(2)),
      height: Number(a.toFixed(2)),
      volume: Number(volume.toFixed(2)),
      space_diagonal: Number((a * Math.sqrt(3)).toFixed(2))
    };
  }

  return {
    polyhedron_type: normType,
    height: Number(h.toFixed(2)),
    base_edge: Number(a.toFixed(2)),
    apex_coordinates: apex,
    vertices,
    measurements
  };
}

// Bộ đệm Debounce cho các lời gọi API từ xa khi người dùng kéo slider liên tục
let debounceTimeout = null;

/**
 * Gọi API Backend POST /api/v1/geometry/parametric-coordinates (kèm debounce 120ms).
 */
export async function fetchParametricCoordinatesRemote(polyhedronType = 'pyramid_square', height = 4.0, baseEdge = 4.0) {
  return new Promise((resolve) => {
    if (debounceTimeout) {
      clearTimeout(debounceTimeout);
    }

    debounceTimeout = setTimeout(async () => {
      try {
        const response = await fetch('/api/v1/geometry/parametric-coordinates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            polyhedron_type: polyhedronType,
            height: Number(height),
            base_edge: Number(baseEdge)
          })
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        resolve(data);
      } catch (err) {
        console.warn('Fallback to local calculation:', err);
        resolve(computeParametricCoordinatesLocal(polyhedronType, height, baseEdge));
      }
    }, 120);
  });
}

/**
 * Task 13.3: Tính toán hình khai triển phẳng 2D (Unfolded Net) cục bộ tức thì (0ms).
 */
export function computeUnfoldedNetLocal(polyhedronType = 'pyramid_square', height = 4.0, baseEdge = 4.0) {
  const h = Math.max(0.5, Math.min(20.0, Number(height) || 4.0));
  const a = Math.max(0.5, Math.min(20.0, Number(baseEdge) || 4.0));
  const normType = String(polyhedronType || 'pyramid_square').toLowerCase().trim();

  const faces = [];
  let foldLines = [];
  let measurements = {};
  let formulas = {};
  let name = '';

  if (normType.includes('square') || normType.includes('pyramid4') || normType === 'pyramid') {
    name = 'Hình Khai Triển Chóp Tứ Giác S.ABCD (SA ⊥ Đáy)';
    const halfA = a / 2.0;
    const pA = { x: -halfA, y: -halfA };
    const pB = { x: halfA, y: -halfA };
    const pC = { x: halfA, y: halfA };
    const pD = { x: -halfA, y: halfA };

    const baseArea = a * a;
    faces.push({
      id: 'face_base',
      name: 'Mặt Đáy ABCD (Hình vuông)',
      face_type: 'base',
      points: [pA, pB, pC, pD],
      labels: ['A', 'B', 'C', 'D'],
      area: Number(baseArea.toFixed(2)),
      area_formula: 'S_{đáy} = a^2',
      fill_color: 'rgba(245, 158, 11, 0.22)',
      stroke_color: '#f59e0b'
    });

    const pS1 = { x: -halfA, y: -halfA - h };
    const s_sab = 0.5 * a * h;
    faces.push({
      id: 'face_sab',
      name: 'Mặt Bên SAB (Tam giác vuông tại A)',
      face_type: 'lateral',
      points: [pA, pB, pS1],
      labels: ['A', 'B', 'S₁'],
      area: Number(s_sab.toFixed(2)),
      area_formula: 'S_{SAB} = \\frac{1}{2} a \\cdot h',
      fill_color: 'rgba(59, 130, 246, 0.20)',
      stroke_color: '#3b82f6'
    });

    const sbLen = Math.sqrt(a * a + h * h);
    const pS2 = { x: halfA + sbLen, y: -halfA };
    const s_sbc = 0.5 * a * sbLen;
    faces.push({
      id: 'face_sbc',
      name: 'Mặt Bên SBC (Tam giác vuông tại B)',
      face_type: 'lateral',
      points: [pB, pC, pS2],
      labels: ['B', 'C', 'S₂'],
      area: Number(s_sbc.toFixed(2)),
      area_formula: 'S_{SBC} = \\frac{1}{2} a \\sqrt{a^2 + h^2}',
      fill_color: 'rgba(16, 185, 129, 0.20)',
      stroke_color: '#10b981'
    });

    const pS3 = { x: -halfA, y: halfA + sbLen };
    const s_scd = 0.5 * a * sbLen;
    faces.push({
      id: 'face_scd',
      name: 'Mặt Bên SCD (Tam giác vuông tại D)',
      face_type: 'lateral',
      points: [pD, pC, pS3],
      labels: ['D', 'C', 'S₃'],
      area: Number(s_scd.toFixed(2)),
      area_formula: 'S_{SCD} = \\frac{1}{2} a \\sqrt{a^2 + h^2}',
      fill_color: 'rgba(139, 92, 246, 0.20)',
      stroke_color: '#8b5cf6'
    });

    const pS4 = { x: -halfA - h, y: -halfA };
    const s_sda = 0.5 * a * h;
    faces.push({
      id: 'face_sda',
      name: 'Mặt Bên SDA (Tam giác vuông tại A)',
      face_type: 'lateral',
      points: [pD, pA, pS4],
      labels: ['D', 'A', 'S₄'],
      area: Number(s_sda.toFixed(2)),
      area_formula: 'S_{SDA} = \\frac{1}{2} a \\cdot h',
      fill_color: 'rgba(236, 72, 153, 0.20)',
      stroke_color: '#ec4899'
    });

    foldLines = [[pA, pB], [pB, pC], [pC, pD], [pD, pA]];
    const lateralArea = 2.0 * s_sab + 2.0 * s_sbc;
    const totalArea = lateralArea + baseArea;

    measurements = {
      base_area: Number(baseArea.toFixed(2)),
      lateral_area: Number(lateralArea.toFixed(2)),
      total_area: Number(totalArea.toFixed(2)),
      slant_height: Number(sbLen.toFixed(2))
    };
    formulas = {
      latex_sxq: 'S_{xq} = S_{SAB} + S_{SBC} + S_{SCD} + S_{SDA} = ah + a\\sqrt{a^2 + h^2}',
      latex_stp: 'S_{tp} = S_{xq} + S_{đáy} = ah + a\\sqrt{a^2 + h^2} + a^2',
      explanation: 'Hình chóp có 4 tam giác mặt bên gấp vào đáy hình vuông ABCD. 4 đỉnh S₁, S₂, S₃, S₄ chụm lại thành đỉnh S.'
    };
  } else if (normType.includes('prism')) {
    name = "Hình Khai Triển Lăng Trụ Đứng Tam Giác ABC.A'B'C'";
    const c = a * Math.SQRT2;
    const baseArea = 0.5 * a * a;

    faces.push({
      id: 'face_lat1',
      name: "Mặt Bên ABB'A'",
      face_type: 'lateral',
      points: [{ x: 0, y: 0 }, { x: a, y: 0 }, { x: a, y: h }, { x: 0, y: h }],
      labels: ['A', 'B', "B'", "A'"],
      area: Number((a * h).toFixed(2)),
      area_formula: 'S_1 = a \\cdot h',
      fill_color: 'rgba(59, 130, 246, 0.20)',
      stroke_color: '#3b82f6'
    });

    faces.push({
      id: 'face_lat2',
      name: "Mặt Bên ACC'A'",
      face_type: 'lateral',
      points: [{ x: a, y: 0 }, { x: 2 * a, y: 0 }, { x: 2 * a, y: h }, { x: a, y: h }],
      labels: ['A', 'C', "C'", "A'"],
      area: Number((a * h).toFixed(2)),
      area_formula: 'S_2 = a \\cdot h',
      fill_color: 'rgba(16, 185, 129, 0.20)',
      stroke_color: '#10b981'
    });

    faces.push({
      id: 'face_lat3',
      name: "Mặt Bên BCC'B'",
      face_type: 'lateral',
      points: [{ x: 2 * a, y: 0 }, { x: 2 * a + c, y: 0 }, { x: 2 * a + c, y: h }, { x: 2 * a, y: h }],
      labels: ['B', 'C', "C'", "B'"],
      area: Number((c * h).toFixed(2)),
      area_formula: 'S_3 = a\\sqrt{2} \\cdot h',
      fill_color: 'rgba(139, 92, 246, 0.20)',
      stroke_color: '#8b5cf6'
    });

    faces.push({
      id: 'face_base_bottom',
      name: 'Mặt Đáy Dưới ABC',
      face_type: 'base',
      points: [{ x: 0, y: 0 }, { x: a, y: 0 }, { x: 0, y: -a }],
      labels: ['A', 'B', 'C'],
      area: Number(baseArea.toFixed(2)),
      area_formula: 'S_{đáy} = \\frac{1}{2} a^2',
      fill_color: 'rgba(245, 158, 11, 0.22)',
      stroke_color: '#f59e0b'
    });

    faces.push({
      id: 'face_base_top',
      name: "Mặt Đáy Trên A'B'C'",
      face_type: 'base',
      points: [{ x: 0, y: h }, { x: a, y: h }, { x: 0, y: h + a }],
      labels: ["A'", "B'", "C'"],
      area: Number(baseArea.toFixed(2)),
      area_formula: 'S_{đáy} = \\frac{1}{2} a^2',
      fill_color: 'rgba(245, 158, 11, 0.22)',
      stroke_color: '#f59e0b'
    });

    foldLines = [
      [{ x: a, y: 0 }, { x: a, y: h }],
      [{ x: 2 * a, y: 0 }, { x: 2 * a, y: h }],
      [{ x: 0, y: 0 }, { x: a, y: 0 }],
      [{ x: 0, y: h }, { x: a, y: h }]
    ];

    const lateralArea = (2 * a + c) * h;
    const totalArea = lateralArea + 2 * baseArea;
    measurements = {
      base_area: Number(baseArea.toFixed(2)),
      lateral_area: Number(lateralArea.toFixed(2)),
      total_area: Number(totalArea.toFixed(2)),
      perimeter_base: Number((2 * a + c).toFixed(2))
    };
    formulas = {
      latex_sxq: 'S_{xq} = C_{đáy} \\cdot h = (2a + a\\sqrt{2}) \\cdot h',
      latex_stp: 'S_{tp} = S_{xq} + 2S_{đáy} = (2a + a\\sqrt{2})h + a^2',
      explanation: 'Khai triển gồm 1 dải chữ nhật kích thước C_đáy x h và 2 đáy tam giác ở hai biên.'
    };
  } else if (normType.includes('cube') || normType.includes('box')) {
    name = "Hình Khai Triển Hình Lập Phương ABCD.A'B'C'D'";
    const baseArea = a * a;
    const row = [
      { id: 'face_left', name: "Mặt Trái ADD'A'", x0: -a, x1: 0, lbs: ['A', 'D', "D'", "A'"] },
      { id: 'face_front', name: "Mặt Trước ABB'A'", x0: 0, x1: a, lbs: ['A', 'B', "B'", "A'"] },
      { id: 'face_right', name: "Mặt Phải BCC'B'", x0: a, x1: 2 * a, lbs: ['B', 'C', "C'", "B'"] },
      { id: 'face_back', name: "Mặt Sau CDD'C'", x0: 2 * a, x1: 3 * a, lbs: ['C', 'D', "D'", "C'"] }
    ];

    row.forEach((item) => {
      faces.push({
        id: item.id,
        name: item.name,
        face_type: 'lateral',
        points: [{ x: item.x0, y: 0 }, { x: item.x1, y: 0 }, { x: item.x1, y: a }, { x: item.x0, y: a }],
        labels: item.lbs,
        area: Number(baseArea.toFixed(2)),
        area_formula: 'S_{mặt} = a^2',
        fill_color: 'rgba(59, 130, 246, 0.20)',
        stroke_color: '#3b82f6'
      });
    });

    faces.push({
      id: 'face_top',
      name: "Mặt Đáy Trên A'B'C'D'",
      face_type: 'base',
      points: [{ x: 0, y: a }, { x: a, y: a }, { x: a, y: 2 * a }, { x: 0, y: 2 * a }],
      labels: ["A'", "B'", "C'", "D'"],
      area: Number(baseArea.toFixed(2)),
      area_formula: 'S_{đáy} = a^2',
      fill_color: 'rgba(245, 158, 11, 0.25)',
      stroke_color: '#f59e0b'
    });

    faces.push({
      id: 'face_bottom',
      name: 'Mặt Đáy Dưới ABCD',
      face_type: 'base',
      points: [{ x: 0, y: -a }, { x: a, y: -a }, { x: a, y: 0 }, { x: 0, y: 0 }],
      labels: ['A', 'B', 'C', 'D'],
      area: Number(baseArea.toFixed(2)),
      area_formula: 'S_{đáy} = a^2',
      fill_color: 'rgba(245, 158, 11, 0.25)',
      stroke_color: '#f59e0b'
    });

    foldLines = [
      [{ x: 0, y: 0 }, { x: 0, y: a }],
      [{ x: a, y: 0 }, { x: a, y: a }],
      [{ x: 2 * a, y: 0 }, { x: 2 * a, y: a }],
      [{ x: 0, y: 0 }, { x: a, y: 0 }],
      [{ x: 0, y: a }, { x: a, y: a }]
    ];

    const lateralArea = 4 * baseArea;
    const totalArea = 6 * baseArea;
    measurements = {
      base_area: Number(baseArea.toFixed(2)),
      lateral_area: Number(lateralArea.toFixed(2)),
      total_area: Number(totalArea.toFixed(2))
    };
    formulas = {
      latex_sxq: 'S_{xq} = 4 \\cdot a^2',
      latex_stp: 'S_{tp} = 6 \\cdot a^2',
      explanation: 'Khai triển chữ Thập gồm 4 mặt xung quanh và 2 mặt đáy vuông bằng nhau.'
    };
  } else {
    name = 'Hình Khai Triển Chóp Tam Giác S.ABC (SA ⊥ Đáy)';
    const baseArea = 0.5 * a * a;
    const pA = { x: 0, y: 0 };
    const pB = { x: a, y: 0 };
    const pC = { x: 0, y: a };

    faces.push({
      id: 'face_base',
      name: 'Mặt Đáy ABC (Tam giác vuông cân tại A)',
      face_type: 'base',
      points: [pA, pB, pC],
      labels: ['A', 'B', 'C'],
      area: Number(baseArea.toFixed(2)),
      area_formula: 'S_{đáy} = \\frac{1}{2} a^2',
      fill_color: 'rgba(245, 158, 11, 0.22)',
      stroke_color: '#f59e0b'
    });

    const pS1 = { x: 0, y: -h };
    const s_sab = 0.5 * a * h;
    faces.push({
      id: 'face_sab',
      name: 'Mặt Bên SAB',
      face_type: 'lateral',
      points: [pA, pB, pS1],
      labels: ['A', 'B', 'S₁'],
      area: Number(s_sab.toFixed(2)),
      area_formula: 'S_{SAB} = \\frac{1}{2} a \\cdot h',
      fill_color: 'rgba(59, 130, 246, 0.20)',
      stroke_color: '#3b82f6'
    });

    const pS2 = { x: -h, y: 0 };
    const s_sac = 0.5 * a * h;
    faces.push({
      id: 'face_sac',
      name: 'Mặt Bên SAC',
      face_type: 'lateral',
      points: [pA, pC, pS2],
      labels: ['A', 'C', 'S₂'],
      area: Number(s_sac.toFixed(2)),
      area_formula: 'S_{SAC} = \\frac{1}{2} a \\cdot h',
      fill_color: 'rgba(16, 185, 129, 0.20)',
      stroke_color: '#10b981'
    });

    const shLen = Math.sqrt(h * h + 0.5 * a * a);
    const pS3 = { x: 0.5 * a + shLen / Math.SQRT2, y: 0.5 * a + shLen / Math.SQRT2 };
    const s_sbc = 0.5 * a * Math.SQRT2 * shLen;
    faces.push({
      id: 'face_sbc',
      name: 'Mặt Bên SBC',
      face_type: 'lateral',
      points: [pB, pC, pS3],
      labels: ['B', 'C', 'S₃'],
      area: Number(s_sbc.toFixed(2)),
      area_formula: 'S_{SBC} = \\frac{1}{2} a\\sqrt{2} \\sqrt{h^2 + \\frac{a^2}{2}}',
      fill_color: 'rgba(139, 92, 246, 0.20)',
      stroke_color: '#8b5cf6'
    });

    foldLines = [[pA, pB], [pA, pC], [pB, pC]];
    const lateralArea = s_sab + s_sac + s_sbc;
    const totalArea = lateralArea + baseArea;
    measurements = {
      base_area: Number(baseArea.toFixed(2)),
      lateral_area: Number(lateralArea.toFixed(2)),
      total_area: Number(totalArea.toFixed(2)),
      slant_height: Number(shLen.toFixed(2))
    };
    formulas = {
      latex_sxq: 'S_{xq} = ah + \\frac{1}{2}a\\sqrt{2}\\sqrt{h^2 + \\frac{a^2}{2}}',
      latex_stp: 'S_{tp} = S_{xq} + \\frac{1}{2}a^2',
      explanation: 'Hình chóp tam giác bung 3 mặt bên ra ngoài; các đỉnh S₁, S₂, S₃ chụm lại thành đỉnh S.'
    };
  }

  const allPts = [];
  faces.forEach((f) => f.points.forEach((p) => allPts.push(p)));
  const minX = Math.min(...allPts.map((p) => p.x));
  const maxX = Math.max(...allPts.map((p) => p.x));
  const minY = Math.min(...allPts.map((p) => p.y));
  const maxY = Math.max(...allPts.map((p) => p.y));
  const pad = 0.5;

  const boundingBox = {
    min_x: Number((minX - pad).toFixed(2)),
    max_x: Number((maxX + pad).toFixed(2)),
    min_y: Number((minY - pad).toFixed(2)),
    max_y: Number((maxY + pad).toFixed(2)),
    width: Number((maxX - minX + 2 * pad).toFixed(2)),
    height: Number((maxY - minY + 2 * pad).toFixed(2))
  };

  return {
    polyhedron_type: normType,
    name,
    height: Number(h.toFixed(2)),
    base_edge: Number(a.toFixed(2)),
    faces,
    fold_lines: foldLines,
    bounding_box: boundingBox,
    measurements,
    formulas
  };
}

let netDebounceTimeout = null;

/**
 * Gọi API Backend GET /api/v1/geometry/unfolded-net (kèm debounce 120ms).
 */
export async function fetchUnfoldedNetRemote(polyhedronType = 'pyramid_square', height = 4.0, baseEdge = 4.0) {
  return new Promise((resolve) => {
    if (netDebounceTimeout) {
      clearTimeout(netDebounceTimeout);
    }

    netDebounceTimeout = setTimeout(async () => {
      try {
        const query = new URLSearchParams({
          polyhedron_type: polyhedronType,
          height: String(height),
          base_edge: String(baseEdge)
        });
        const response = await fetch(`/api/v1/geometry/unfolded-net?${query.toString()}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        resolve(data);
      } catch (err) {
        console.warn('Fallback to local unfolded net calculation:', err);
        resolve(computeUnfoldedNetLocal(polyhedronType, height, baseEdge));
      }
    }, 120);
  });
}

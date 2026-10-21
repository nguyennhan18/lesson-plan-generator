import React, { useState, useMemo } from 'react';
import { Layers, Scissors, Info, Sparkles, CheckCircle2 } from 'lucide-react';
import { computeUnfoldedNetLocal } from '../utils/geometryClient';

/**
 * UnfoldedNetViewer — Component Trực Quan Hóa Bản Vẽ Khai Triển Phẳng 2D (Task 13.3)
 * Hiển thị song song với hình 3D giúp học sinh dễ dàng hình dung Diện tích xung quanh (S_xq).
 */
export default function UnfoldedNetViewer({
  polyhedronType = 'pyramid_square',
  heightParam = 4.0,
  baseParam = 4.0,
  showVertexLabels = true,
  onFaceSelect = null
}) {
  // Tính toán dữ liệu hình khai triển phẳng (local 0ms phản hồi mượt mà theo slider)
  const netData = useMemo(() => {
    return computeUnfoldedNetLocal(polyhedronType, heightParam, baseParam);
  }, [polyhedronType, heightParam, baseParam]);

  // Trạng thái hover / chọn từng mảnh mặt phẳng khai triển
  const [activeFaceId, setActiveFaceId] = useState(null);

  const { faces = [], fold_lines = [], bounding_box = {}, measurements = {}, formulas = {} } = netData;

  // Tính toán viewBox SVG chuẩn hóa
  const viewBoxStr = useMemo(() => {
    if (!bounding_box.width || !bounding_box.height) {
      return '-8 -8 16 16';
    }
    const minX = bounding_box.min_x;
    // Đảo ngược trục Y cho hệ tọa độ toán học: minY trong SVG tương ứng với -maxY
    const minY = -bounding_box.max_y;
    const w = bounding_box.width;
    const h = bounding_box.height;
    return `${minX} ${minY} ${w} ${h}`;
  }, [bounding_box]);

  const activeFace = faces.find((f) => f.id === activeFaceId) || null;

  return (
    <div className="w-full h-full flex flex-col bg-slate-950/90 rounded-lg border border-slate-800/90 overflow-hidden relative select-none">
      {/* Tiêu đề & huy hiệu chế độ */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-900/90 border-b border-slate-800 text-xs">
        <div className="flex items-center gap-1.5">
          <Layers size={13} className="text-amber-400" />
          <span className="font-semibold text-slate-200">Khai Triển Phẳng 2D</span>
          <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-950/80 border border-amber-600/40 text-amber-300 font-mono">
            Unfolded Net
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
          <span>{faces.length} mảnh mặt</span>
          <span className="text-slate-600">|</span>
          <span className="text-emerald-400 flex items-center gap-0.5">
            <Scissors size={10} /> Trải phẳng
          </span>
        </div>
      </div>

      {/* Khung vẽ SVG Vector tương tác */}
      <div className="flex-1 w-full relative min-h-[190px] flex items-center justify-center p-2 bg-gradient-to-b from-slate-950 via-slate-900/70 to-slate-950">
        <svg
          viewBox={viewBoxStr}
          className="w-full h-full max-h-[300px] overflow-visible"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Lưới tọa độ phụ trợ mờ nhẹ */}
          <defs>
            <pattern id="gridPattern" width="1" height="1" patternUnits="userSpaceOnUse">
              <path d="M 1 0 L 0 0 0 1" fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.03" />
            </pattern>
          </defs>
          <rect
            x={bounding_box.min_x}
            y={-bounding_box.max_y}
            width={bounding_box.width}
            height={bounding_box.height}
            fill="url(#gridPattern)"
          />

          {/* 1. Vẽ các mảnh mặt phẳng (Faces) */}
          {faces.map((face) => {
            const isHovered = activeFaceId === face.id;
            // Biến đổi các điểm (x, y) sang SVG: (x, -y)
            const ptsStr = face.points.map((p) => `${p.x},${-p.y}`).join(' ');

            // Tính tâm mặt để hiển thị nhãn
            const centerX = face.points.reduce((sum, p) => sum + p.x, 0) / face.points.length;
            const centerY = face.points.reduce((sum, p) => sum + -p.y, 0) / face.points.length;

            return (
              <g
                key={face.id}
                className="cursor-pointer transition-all duration-200"
                onMouseEnter={() => {
                  setActiveFaceId(face.id);
                  onFaceSelect?.(face);
                }}
                onMouseLeave={() => setActiveFaceId(null)}
                onClick={() => {
                  setActiveFaceId(face.id === activeFaceId ? null : face.id);
                  onFaceSelect?.(face);
                }}
              >
                {/* Polygon mặt phẳng */}
                <polygon
                  points={ptsStr}
                  fill={isHovered ? face.stroke_color + '44' : face.fill_color}
                  stroke={isHovered ? '#ffffff' : face.stroke_color}
                  strokeWidth={isHovered ? 0.08 : 0.05}
                  strokeLinejoin="round"
                />

                {/* Nhãn tâm mặt (Diện tích) */}
                <text
                  x={centerX}
                  y={centerY}
                  fill={isHovered ? '#ffffff' : face.stroke_color}
                  fontSize="0.38"
                  fontWeight="bold"
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="pointer-events-none drop-shadow-sm select-none"
                >
                  {face.face_type === 'base' ? 'Đáy' : face.labels.join('')}
                </text>
                <text
                  x={centerX}
                  y={centerY + 0.38}
                  fill={isHovered ? '#fef08a' : '#cbd5e1'}
                  fontSize="0.28"
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="pointer-events-none select-none"
                >
                  {face.area.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* 2. Nếp gấp nội bộ (Fold Lines - Nét đứt nét gấp) */}
          {fold_lines.map((line, idx) => {
            if (line.length < 2) return null;
            return (
              <line
                key={`fold-${idx}`}
                x1={line[0].x}
                y1={-line[0].y}
                x2={line[1].x}
                y2={-line[1].y}
                stroke="#f59e0b"
                strokeWidth="0.06"
                strokeDasharray="0.16 0.10"
                strokeLinecap="round"
                className="pointer-events-none"
              />
            );
          })}

          {/* 3. Đỉnh và Tên các đỉnh (Task 13.4: Bật/tắt nhãn tên đỉnh S, A, B, C...) */}
          {showVertexLabels && faces.map((face) =>
            face.points.map((pt, pIdx) => {
              const label = face.labels[pIdx] || '';
              return (
                <g key={`pt-${face.id}-${pIdx}`} className="pointer-events-none">
                  <circle cx={pt.x} cy={-pt.y} r="0.08" fill="#38bdf8" stroke="#0f172a" strokeWidth="0.02" />
                  <text
                    x={pt.x}
                    y={-pt.y - 0.18}
                    fill="#e2e8f0"
                    fontSize="0.32"
                    fontWeight="bold"
                    textAnchor="middle"
                    className="select-none"
                  >
                    {label}
                  </text>
                </g>
              );
            })
          )}
        </svg>

        {/* Chú giải góc nếp gấp & đường cắt */}
        <div className="absolute top-2 right-2 flex flex-col gap-1 bg-slate-900/90 p-1.5 rounded border border-slate-800 text-[9px] text-slate-300">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 border-t border-dashed border-amber-400"></span>
            <span>Nếp gấp (Folds)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-blue-400"></span>
            <span>Đường biên (Cuts)</span>
          </div>
        </div>
      </div>

      {/* Bảng thông số Diện tích S_xq và S_tp */}
      <div className="p-2 bg-slate-950 border-t border-slate-800/90 text-xs">
        {/* Thông tin mảnh đang chọn / hover */}
        {activeFace ? (
          <div className="mb-1.5 p-1.5 rounded bg-cyan-950/50 border border-cyan-800/50 flex items-center justify-between text-[11px]">
            <div className="flex items-center gap-1 text-cyan-300">
              <Sparkles size={11} className="text-amber-400" />
              <span className="font-semibold">{activeFace.name}:</span>
              <span className="font-mono text-white font-bold">{activeFace.area_formula}</span>
            </div>
            <div className="font-mono text-emerald-300 font-bold">
              = {activeFace.area.toFixed(1)}
            </div>
          </div>
        ) : (
          <div className="mb-1.5 p-1 rounded bg-slate-900/60 border border-slate-800/60 text-[10px] text-slate-400 text-center flex items-center justify-center gap-1">
            <Info size={11} className="text-cyan-400" />
            <span>Rê chuột vào từng mảnh mặt phẳng để xem công thức diện tích riêng</span>
          </div>
        )}

        {/* Tổng diện tích S_xq, S_đáy và S_tp */}
        <div className="grid grid-cols-3 gap-1.5 text-center font-mono">
          <div className="p-1 rounded bg-amber-950/40 border border-amber-700/40">
            <div className="text-[9px] text-amber-300">S đáy</div>
            <div className="text-amber-200 font-bold text-[11px]">
              {Number(measurements.base_area || 0).toFixed(1)}
            </div>
          </div>

          <div className="p-1 rounded bg-cyan-950/50 border border-cyan-700/50">
            <div className="text-[9px] text-cyan-300 font-semibold">Sxq (Xung quanh)</div>
            <div className="text-cyan-200 font-black text-[11px]">
              {Number(measurements.lateral_area || 0).toFixed(1)}
            </div>
          </div>

          <div className="p-1 rounded bg-emerald-950/40 border border-emerald-700/40">
            <div className="text-[9px] text-emerald-300">S toàn phần</div>
            <div className="text-emerald-200 font-bold text-[11px]">
              {Number(measurements.total_area || 0).toFixed(1)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

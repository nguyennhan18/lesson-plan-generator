import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Box, LineChart, ChevronRight, Sliders, Eye, Calculator, Zap, Layers } from 'lucide-react';
import FunctionPlotter from './FunctionPlotter';
import { computeParametricCoordinatesLocal, computeUnfoldedNetLocal } from '../utils/geometryClient';

export default function RightToolsDock({
  isOpen,
  onToggle,
  polyhedronType,
  setPolyhedronType,
  edgeLength,
  setEdgeLength,
  geoHeight,
  setGeoHeight,
  geoBaseEdge,
  setGeoBaseEdge,
  showHiddenLines,
  setShowHiddenLines,
  showVertexLabels,
  setShowVertexLabels,
  showAxes,
  setShowAxes,
  cameraPreset = 'iso',
  onCameraPreset,
  showUnfoldedNet = false,
  setShowUnfoldedNet,
  onQuickGeom
}) {
  const [subTab, setSubTab] = useState('3d'); // '3d' or 'graph'

  const activeH = typeof geoHeight === 'number' ? geoHeight : 4.0;
  const activeA = typeof geoBaseEdge === 'number' ? geoBaseEdge : (edgeLength ?? 4.0);
  const metrics = computeParametricCoordinatesLocal(polyhedronType, activeH, activeA);
  const netMetrics = useMemo(() => {
    return computeUnfoldedNetLocal(polyhedronType, activeH, activeA);
  }, [polyhedronType, activeH, activeA]);

  // Task 13.4: Danh sách nhãn đỉnh sư phạm của khối đa diện hiện tại
  const vertexChipList = useMemo(() => {
    const t = String(polyhedronType || 'pyramid_square').toLowerCase();
    if (t.includes('prism')) return ['A', 'B', 'C', "A'", "B'", "C'"];
    if (t.includes('cube') || t.includes('box')) return ['A', 'B', 'C', 'D', "A'", "B'", "C'", "D'"];
    if (t.includes('triangle')) return ['S', 'A', 'B', 'C', 'H'];
    return ['S', 'A', 'B', 'C', 'D', 'O'];
  }, [polyhedronType]);

  // Task 12.4: Điều phối requestAnimationFrame cho thanh trượt đạt 60 FPS
  const rafHeightRef = useRef(null);
  const rafBaseRef = useRef(null);

  const handleHeightInput = (val) => {
    const num = parseFloat(val);
    if (!isNaN(num)) {
      if (rafHeightRef.current) cancelAnimationFrame(rafHeightRef.current);
      rafHeightRef.current = requestAnimationFrame(() => {
        setGeoHeight?.(num);
      });
    }
  };

  const handleBaseEdgeInput = (val) => {
    const num = parseFloat(val);
    if (!isNaN(num)) {
      if (rafBaseRef.current) cancelAnimationFrame(rafBaseRef.current);
      rafBaseRef.current = requestAnimationFrame(() => {
        setGeoBaseEdge?.(num);
      });
    }
  };

  useEffect(() => {
    return () => {
      if (rafHeightRef.current) cancelAnimationFrame(rafHeightRef.current);
      if (rafBaseRef.current) cancelAnimationFrame(rafBaseRef.current);
    };
  }, []);

  if (!isOpen) return null;

  return (
    <aside className="w-80 glass-panel border-l border-slate-800 flex flex-col justify-between h-full transition-all duration-300 z-10">
      {/* 1. Header */}
      <div>
        <div className="p-3 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-800 flex items-center justify-center text-cyan-400">
              <Sliders size={17} />
            </div>
            <div>
              <h3 className="text-xs font-bold text-white">Công Cụ Giảng Dạy</h3>
              <p className="text-[11px] text-slate-400">Hình Học 3D • Đồ Thị Hàm Số</p>
            </div>
          </div>
          <button
            onClick={onToggle}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Thu gọn bảng công cụ (T)"
          >
            <ChevronRight size={16} />
          </button>
        </div>

        {/* 2. Sub-tabs */}
        <div className="p-2 border-b border-slate-800 bg-slate-950/40">
          <div className="grid grid-cols-2 gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setSubTab('3d')}
              className={`py-1.5 rounded-md font-medium transition flex items-center justify-center gap-1.5 ${
                subTab === '3d'
                  ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Box size={14} /> Hình Học 3D
            </button>
            <button
              onClick={() => setSubTab('graph')}
              className={`py-1.5 rounded-md font-medium transition flex items-center justify-center gap-1.5 ${
                subTab === 'graph'
                  ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <LineChart size={14} /> Đồ Thị Hàm Số
            </button>
          </div>
        </div>

        {/* 3. Sub-tab Content */}
        <div className="p-3 space-y-3 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 180px)' }}>
          {subTab === '3d' ? (
            <div className="space-y-3 text-xs">
              {/* Polyhedron select */}
              <div>
                <label className="text-slate-400 block mb-1">Khối đa diện:</label>
                <select
                  value={polyhedronType}
                  onChange={(e) => setPolyhedronType(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="cube">Hình Lập Phương (ABCD.A'B'C'D')</option>
                  <option value="pyramid_square">Hình Chóp S.ABCD (SA ⊥ Đáy)</option>
                  <option value="pyramid_triangle">Hình Chóp Tam Giác (S.ABC)</option>
                  <option value="prism_triangle">Lăng Trụ Đứng (ABC.A'B'C')</option>
                </select>
              </div>

              {/* Task 12.1 & 12.4: Parametric Sliders (Chiều cao h và Cạnh đáy a - 60 FPS rAF) */}
              <div className="space-y-2.5 bg-slate-900/50 p-2 rounded-lg border border-slate-800">
                <div className="flex items-center justify-between pb-1 border-b border-slate-800 text-[11px]">
                  <span className="text-slate-300 font-semibold">Tham Số Hình Học</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-950/80 border border-emerald-600/40 text-emerald-400 font-mono font-bold flex items-center gap-0.5">
                    <Zap size={9} /> 60 FPS rAF
                  </span>
                </div>

                {/* Slider Chiều cao h (1 đến 10) */}
                <div>
                  <div className="flex justify-between text-slate-300 text-xs mb-1">
                    <span>Chiều cao <strong className="text-cyan-400 font-mono">h</strong>:</span>
                    <span className="text-cyan-400 font-mono font-bold">{(geoHeight ?? edgeLength ?? 4.0).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-500 font-mono">1</span>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      step="0.5"
                      value={geoHeight ?? 4.0}
                      onInput={(e) => handleHeightInput(e.target.value)}
                      onChange={(e) => handleHeightInput(e.target.value)}
                      className="w-full accent-cyan-400"
                    />
                    <span className="text-[10px] text-slate-500 font-mono">10</span>
                  </div>
                </div>

                {/* Slider Cạnh đáy a (1 đến 8) */}
                <div>
                  <div className="flex justify-between text-slate-300 text-xs mb-1">
                    <span>Cạnh đáy <strong className="text-emerald-400 font-mono">a</strong>:</span>
                    <span className="text-emerald-400 font-mono font-bold">{(geoBaseEdge ?? edgeLength ?? 4.0).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-500 font-mono">1</span>
                    <input
                      type="range"
                      min="1"
                      max="8"
                      step="0.5"
                      value={geoBaseEdge ?? 4.0}
                      onInput={(e) => handleBaseEdgeInput(e.target.value)}
                      onChange={(e) => handleBaseEdgeInput(e.target.value)}
                      className="w-full accent-emerald-400"
                    />
                    <span className="text-[10px] text-slate-500 font-mono">8</span>
                  </div>
                </div>

                {/* Tọa độ đỉnh S & Thể tích động (Task 12.2 & 12.3) */}
                <div className="pt-1.5 border-t border-slate-800 space-y-1 text-[10px]">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Đỉnh chóp S:</span>
                    <span className="text-cyan-300 font-mono font-bold">S(0.0, 0.0, {activeH.toFixed(1)})</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Diện tích Sđáy:</span>
                    <span className="text-amber-300 font-mono font-bold">{Number(metrics.measurements.base_area).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center justify-between text-indigo-300 font-medium">
                    <span>Thể tích V:</span>
                    <span className="text-emerald-300 font-mono font-black">{Number(metrics.measurements.volume).toFixed(1)}</span>
                  </div>
                </div>
              </div>

              {/* Camera Presets (Task 13.2) */}
              <div>
                <label className="text-slate-400 block mb-1 text-xs">Góc nhìn chuẩn SGK (TCVN 7284):</label>
                <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                  <button
                    onClick={() => onCameraPreset?.('iso')}
                    className={`p-1.5 rounded transition text-center border ${
                      cameraPreset === 'iso'
                        ? 'bg-cyan-600 text-white border-cyan-400 font-semibold shadow-sm'
                        : 'bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border-slate-800'
                    }`}
                    title="Góc nhìn phối cảnh 3 chiều trục đo SGK (Isometric)"
                  >
                    Phối Cảnh (Iso)
                  </button>
                  <button
                    onClick={() => onCameraPreset?.('front')}
                    className={`p-1.5 rounded transition text-center border ${
                      cameraPreset === 'front'
                        ? 'bg-cyan-600 text-white border-cyan-400 font-semibold shadow-sm'
                        : 'bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border-slate-800'
                    }`}
                    title="Hình chiếu đứng: Chiếu từ trước ra sau (Front View)"
                  >
                    Chiếu Đứng (Front)
                  </button>
                  <button
                    onClick={() => onCameraPreset?.('top')}
                    className={`p-1.5 rounded transition text-center border ${
                      cameraPreset === 'top'
                        ? 'bg-cyan-600 text-white border-cyan-400 font-semibold shadow-sm'
                        : 'bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border-slate-800'
                    }`}
                    title="Hình chiếu bằng: Chiếu từ trên xuống đáy Oxy (Top View)"
                  >
                    Chiếu Bằng (Top)
                  </button>
                  <button
                    onClick={() => onCameraPreset?.('side')}
                    className={`p-1.5 rounded transition text-center border ${
                      cameraPreset === 'side'
                        ? 'bg-cyan-600 text-white border-cyan-400 font-semibold shadow-sm'
                        : 'bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border-slate-800'
                    }`}
                    title="Hình chiếu cạnh: Chiếu vuông góc từ bên hông 90° (Side View)"
                  >
                    Chiếu Cạnh (Side)
                  </button>
                </div>
              </div>

              {/* Toggles */}
              <div className="space-y-1.5 pt-1 border-t border-slate-800/80">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={showHiddenLines}
                    onChange={(e) => setShowHiddenLines(e.target.checked)}
                    className="accent-cyan-400 rounded"
                  />
                  <span>Hiện nét đứt (cạnh khuất)</span>
                </label>
                <div className="flex flex-col space-y-1">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                    <input
                      type="checkbox"
                      checked={showVertexLabels}
                      onChange={(e) => setShowVertexLabels(e.target.checked)}
                      className="accent-indigo-400 rounded"
                    />
                    <span>Hiện tên các đỉnh (A, B, C...)</span>
                  </label>
                  {showVertexLabels && (
                    <div className="flex flex-wrap gap-1 pl-5 pt-0.5">
                      {vertexChipList.map((lbl) => (
                        <span
                          key={lbl}
                          className="px-1.5 py-0.2 rounded bg-indigo-950/70 border border-indigo-700/50 text-[10px] text-indigo-300 font-serif font-bold italic"
                        >
                          {lbl}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={showAxes}
                    onChange={(e) => setShowAxes(e.target.checked)}
                    className="accent-cyan-400 rounded"
                  />
                  <span>Hiện hệ trục tọa độ Oxyz</span>
                </label>
              </div>

              {/* TASK 13.3: HÌNH KHAI TRIỂN PHẲNG 2D (UNFOLDED NET & DIỆN TÍCH S_xq) */}
              <div className="pt-2 border-t border-slate-800/80">
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-slate-300 font-semibold text-xs flex items-center gap-1.5">
                    <Layers size={13} className="text-amber-400" />
                    <span>Khai triển 2D (Net):</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowUnfoldedNet?.(!showUnfoldedNet)}
                    className={`px-2 py-0.5 rounded text-[10px] font-medium transition border ${
                      showUnfoldedNet
                        ? 'bg-amber-500/20 text-amber-300 border-amber-400/60 shadow-sm'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    {showUnfoldedNet ? 'Bật (Song song 3D)' : 'Tắt'}
                  </button>
                </div>

                <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800 text-[11px] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Diện tích Sđáy:</span>
                    <span className="text-amber-300 font-mono font-bold">{Number(netMetrics.measurements.base_area || 0).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Diện tích Sxq:</span>
                    <span className="text-cyan-300 font-mono font-bold">{Number(netMetrics.measurements.lateral_area || 0).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Diện tích Stp:</span>
                    <span className="text-emerald-300 font-mono font-black">{Number(netMetrics.measurements.total_area || 0).toFixed(1)}</span>
                  </div>
                  <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800/60 leading-tight">
                    💡 {netMetrics.formulas.explanation}
                  </div>
                </div>
              </div>

              {/* Quick Geometric Actions */}
              <div className="pt-2 border-t border-slate-800/80">
                <label className="text-slate-400 block mb-1 font-medium">Thao tác hình học nhanh:</label>
                <div className="space-y-1">
                  <button
                    onClick={() => onQuickGeom('diagonal')}
                    className="w-full text-left p-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 text-cyan-300 hover:border-cyan-500/50 transition flex items-center gap-2"
                  >
                    <div>
                      <div className="font-semibold text-white">Kẻ đường chéo AC' = a√3</div>
                      <div className="text-[10px] text-slate-400">Định lý Pytago 2 bước không gian</div>
                    </div>
                  </button>

                  <button
                    onClick={() => onQuickGeom('altitude')}
                    className="w-full text-left p-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 text-emerald-300 hover:border-emerald-500/50 transition flex items-center gap-2"
                  >
                    <div>
                      <div className="font-semibold text-white">Hạ vuông góc AH ⊥ B'D'</div>
                      <div className="text-[10px] text-slate-400">Khoảng cách từ 1 điểm đến đường thẳng</div>
                    </div>
                  </button>

                  <button
                    onClick={() => onQuickGeom('cross_section')}
                    className="w-full text-left p-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 text-amber-300 hover:border-amber-500/50 transition flex items-center gap-2"
                  >
                    <div>
                      <div className="font-semibold text-white">Cắt thiết diện (A'BD)</div>
                      <div className="text-[10px] text-slate-400">Thiết diện tam giác đều S = a²√3/2</div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <FunctionPlotter />
          )}
        </div>
      </div>

      {/* 4. Footer hint */}
      <div className="p-2 border-t border-slate-800 text-center text-[10px] text-slate-500 bg-slate-950/60">
        Phím tắt: <code>T</code> để ẩn/hiện thanh công cụ
      </div>
    </aside>
  );
}

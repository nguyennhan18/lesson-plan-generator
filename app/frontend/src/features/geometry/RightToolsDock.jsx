import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Box, LineChart, ChevronRight, Sliders, Eye, Calculator, Zap, Layers } from 'lucide-react';
import FunctionPlotter from '../../shared/math/FunctionPlotter';
import { computeParametricCoordinatesLocal, computeUnfoldedNetLocal } from './geometryClient.js';

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

  // Danh sách nhãn đỉnh sư phạm của khối đa diện hiện tại
  const vertexChipList = useMemo(() => {
    const t = String(polyhedronType || 'pyramid_square').toLowerCase();
    if (t.includes('prism')) return ['A', 'B', 'C', "A'", "B'", "C'"];
    if (t.includes('cube') || t.includes('box')) return ['A', 'B', 'C', 'D', "A'", "B'", "C'", "D'"];
    if (t.includes('triangle')) return ['S', 'A', 'B', 'C', 'H'];
    return ['S', 'A', 'B', 'C', 'D', 'O'];
  }, [polyhedronType]);

  // Điều phối requestAnimationFrame cho thanh trượt đạt 60 FPS
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
    <aside className="w-80 bg-[#ffffff] border-l border-[#e0e0e0] flex flex-col justify-between h-full transition-all duration-300 z-10 shrink-0 text-[#141414]">
      {/* 1. Header */}
      <div>
        <div className="p-3 border-b border-[#e0e0e0] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-[30%] bg-[#141414] text-white flex items-center justify-center shrink-0">
              <Sliders size={17} />
            </div>
            <div>
              <h3 className="text-xs font-bold text-[#141414] leading-tight">Công Cụ Giảng Dạy</h3>
              <p className="text-[11px] text-[#707070] leading-tight">Hình Học 3D • Đồ Thị Hàm Số</p>
            </div>
          </div>
          <button
            onClick={onToggle}
            className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] transition cursor-pointer"
            title="Thu gọn bảng công cụ (T)"
          >
            <ChevronRight size={16} />
          </button>
        </div>

        {/* 2. Sub-tabs Segmented Control */}
        <div className="p-2.5 border-b border-[#f0f0f0] bg-[#ffffff]">
          <div className="grid grid-cols-2 gap-1 bg-[#f3f3f3] p-1 rounded-full border border-[#e0e0e0] text-xs">
            <button
              onClick={() => setSubTab('3d')}
              className={`py-1.5 rounded-full font-semibold transition flex items-center justify-center gap-1.5 cursor-pointer ${
                subTab === '3d'
                  ? 'bg-[#ffffff] text-[#141414] shadow-sm'
                  : 'text-[#707070] hover:text-[#141414]'
              }`}
            >
              <Box size={14} /> Hình Học 3D
            </button>
            <button
              onClick={() => setSubTab('graph')}
              className={`py-1.5 rounded-full font-semibold transition flex items-center justify-center gap-1.5 cursor-pointer ${
                subTab === 'graph'
                  ? 'bg-[#ffffff] text-[#141414] shadow-sm'
                  : 'text-[#707070] hover:text-[#141414]'
              }`}
            >
              <LineChart size={14} /> Đồ Thị Hàm Số
            </button>
          </div>
        </div>

        {/* 3. Sub-tab Content */}
        <div className="p-3 space-y-3.5 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 180px)' }}>
          {subTab === '3d' ? (
            <div className="space-y-3 text-xs">
              {/* Polyhedron select */}
              <div>
                <label className="text-[#707070] block mb-1 font-medium">Khối đa diện:</label>
                <select
                  value={polyhedronType}
                  onChange={(e) => setPolyhedronType(e.target.value)}
                  className="w-full bg-[#f0f0f0] border-none rounded-xl px-3 py-2 text-[#141414] focus:ring-2 focus:ring-[#141414] outline-none cursor-pointer"
                >
                  <option value="cube">Hình Lập Phương (ABCD.A'B'C'D')</option>
                  <option value="pyramid_square">Hình Chóp S.ABCD (SA ⊥ Đáy)</option>
                  <option value="pyramid_triangle">Hình Chóp Tam Giác (S.ABC)</option>
                  <option value="prism_triangle">Lăng Trụ Đứng (ABC.A'B'C')</option>
                </select>
              </div>

              {/* Parametric Sliders (Chiều cao h và Cạnh đáy a - 60 FPS rAF) */}
              <div className="space-y-2.5 bg-[#f3f3f3] p-3 rounded-2xl border border-[#e0e0e0]">
                <div className="flex items-center justify-between pb-1.5 border-b border-[#e0e0e0] text-[11px]">
                  <span className="text-[#141414] font-semibold">Tham Số Hình Học</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#ffffff] border border-[#e0e0e0] text-[#141414] font-mono font-bold flex items-center gap-1">
                    <Zap size={10} className="text-[#0066ff]" /> 60 FPS rAF
                  </span>
                </div>

                {/* Slider Chiều cao h (1 đến 10) */}
                <div>
                  <div className="flex justify-between text-[#141414] text-xs mb-1">
                    <span>Chiều cao <strong className="font-mono">h</strong>:</span>
                    <span className="font-mono font-bold">{(geoHeight ?? edgeLength ?? 4.0).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-[#707070] font-mono">1</span>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      step="0.5"
                      value={geoHeight ?? 4.0}
                      onInput={(e) => handleHeightInput(e.target.value)}
                      onChange={(e) => handleHeightInput(e.target.value)}
                      className="w-full accent-[#141414] cursor-pointer"
                    />
                    <span className="text-[10px] text-[#707070] font-mono">10</span>
                  </div>
                </div>

                {/* Slider Cạnh đáy a (1 đến 8) */}
                <div>
                  <div className="flex justify-between text-[#141414] text-xs mb-1">
                    <span>Cạnh đáy <strong className="font-mono">a</strong>:</span>
                    <span className="font-mono font-bold">{(geoBaseEdge ?? edgeLength ?? 4.0).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-[#707070] font-mono">1</span>
                    <input
                      type="range"
                      min="1"
                      max="8"
                      step="0.5"
                      value={geoBaseEdge ?? 4.0}
                      onInput={(e) => handleBaseEdgeInput(e.target.value)}
                      onChange={(e) => handleBaseEdgeInput(e.target.value)}
                      className="w-full accent-[#141414] cursor-pointer"
                    />
                    <span className="text-[10px] text-[#707070] font-mono">8</span>
                  </div>
                </div>

                {/* Measurements */}
                <div className="pt-2 border-t border-[#e0e0e0] space-y-1 text-[11px]">
                  <div className="flex items-center justify-between text-[#707070]">
                    <span>Đỉnh chóp S:</span>
                    <span className="text-[#141414] font-mono font-semibold">S(0.0, 0.0, {activeH.toFixed(1)})</span>
                  </div>
                  <div className="flex items-center justify-between text-[#707070]">
                    <span>Diện tích Sđáy:</span>
                    <span className="text-[#141414] font-mono font-semibold">{Number(metrics.measurements.base_area).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center justify-between text-[#141414] font-medium">
                    <span>Thể tích V:</span>
                    <span className="text-[#141414] font-mono font-bold">{Number(metrics.measurements.volume).toFixed(1)}</span>
                  </div>
                </div>
              </div>

              {/* Camera Presets */}
              <div>
                <label className="text-[#707070] block mb-1 text-xs font-medium">Góc nhìn chuẩn SGK (TCVN 7284):</label>
                <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                  <button
                    onClick={() => onCameraPreset?.('iso')}
                    className={`p-1.5 rounded-full transition text-center border cursor-pointer ${
                      cameraPreset === 'iso'
                        ? 'bg-[#141414] text-white border-[#141414] font-semibold'
                        : 'bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border-[#e0e0e0]'
                    }`}
                    title="Góc nhìn phối cảnh 3 chiều trục đo SGK (Isometric)"
                  >
                    Phối Cảnh (Iso)
                  </button>
                  <button
                    onClick={() => onCameraPreset?.('front')}
                    className={`p-1.5 rounded-full transition text-center border cursor-pointer ${
                      cameraPreset === 'front'
                        ? 'bg-[#141414] text-white border-[#141414] font-semibold'
                        : 'bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border-[#e0e0e0]'
                    }`}
                    title="Hình chiếu đứng: Chiếu từ trước ra sau (Front View)"
                  >
                    Chiếu Đứng (Front)
                  </button>
                  <button
                    onClick={() => onCameraPreset?.('top')}
                    className={`p-1.5 rounded-full transition text-center border cursor-pointer ${
                      cameraPreset === 'top'
                        ? 'bg-[#141414] text-white border-[#141414] font-semibold'
                        : 'bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border-[#e0e0e0]'
                    }`}
                    title="Hình chiếu bằng: Chiếu từ trên xuống đáy Oxy (Top View)"
                  >
                    Chiếu Bằng (Top)
                  </button>
                  <button
                    onClick={() => onCameraPreset?.('side')}
                    className={`p-1.5 rounded-full transition text-center border cursor-pointer ${
                      cameraPreset === 'side'
                        ? 'bg-[#141414] text-white border-[#141414] font-semibold'
                        : 'bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border-[#e0e0e0]'
                    }`}
                    title="Hình chiếu cạnh: Chiếu vuông góc từ bên hông 90° (Side View)"
                  >
                    Chiếu Cạnh (Side)
                  </button>
                </div>
              </div>

              {/* Toggles */}
              <div className="space-y-2 pt-1 border-t border-[#f0f0f0]">
                <label className="flex items-center gap-2 cursor-pointer text-[#141414]">
                  <input
                    type="checkbox"
                    checked={showHiddenLines}
                    onChange={(e) => setShowHiddenLines(e.target.checked)}
                    className="accent-[#141414] rounded"
                  />
                  <span>Hiện nét đứt (cạnh khuất)</span>
                </label>
                <div className="flex flex-col space-y-1">
                  <label className="flex items-center gap-2 cursor-pointer text-[#141414]">
                    <input
                      type="checkbox"
                      checked={showVertexLabels}
                      onChange={(e) => setShowVertexLabels(e.target.checked)}
                      className="accent-[#141414] rounded"
                    />
                    <span>Hiện tên các đỉnh (A, B, C...)</span>
                  </label>
                  {showVertexLabels && (
                    <div className="flex flex-wrap gap-1 pl-5 pt-0.5">
                      {vertexChipList.map((lbl) => (
                        <span
                          key={lbl}
                          className="px-2 py-0.5 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-[10px] text-[#141414] font-serif font-bold italic"
                        >
                          {lbl}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <label className="flex items-center gap-2 cursor-pointer text-[#141414]">
                  <input
                    type="checkbox"
                    checked={showAxes}
                    onChange={(e) => setShowAxes(e.target.checked)}
                    className="accent-[#141414] rounded"
                  />
                  <span>Hiện hệ trục tọa độ Oxyz</span>
                </label>
              </div>

              {/* HÌNH KHAI TRIỂN PHẲNG 2D (UNFOLDED NET) */}
              <div className="pt-2 border-t border-[#f0f0f0]">
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-[#141414] font-semibold text-xs flex items-center gap-1.5">
                    <Layers size={13} className="text-[#141414]" />
                    <span>Khai triển 2D (Net):</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowUnfoldedNet?.(!showUnfoldedNet)}
                    className={`px-3 py-1 rounded-full text-[10px] font-semibold transition border cursor-pointer ${
                      showUnfoldedNet
                        ? 'bg-[#141414] text-white border-[#141414]'
                        : 'bg-[#ffffff] text-[#141414] border-[#e0e0e0] hover:bg-[#f3f3f3]'
                    }`}
                  >
                    {showUnfoldedNet ? 'Đang Bật' : 'Tắt'}
                  </button>
                </div>

                <div className="bg-[#f3f3f3] p-3 rounded-2xl border border-[#e0e0e0] text-[11px] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[#707070]">Diện tích Sđáy:</span>
                    <span className="text-[#141414] font-mono font-bold">{Number(netMetrics.measurements.base_area || 0).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#707070]">Diện tích Sxq:</span>
                    <span className="text-[#141414] font-mono font-bold">{Number(netMetrics.measurements.lateral_area || 0).toFixed(1)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#707070]">Diện tích Stp:</span>
                    <span className="text-[#141414] font-mono font-bold">{Number(netMetrics.measurements.total_area || 0).toFixed(1)}</span>
                  </div>
                  <div className="text-[10px] text-[#707070] pt-1.5 border-t border-[#e0e0e0] leading-tight">
                    💡 {netMetrics.formulas.explanation}
                  </div>
                </div>
              </div>

              {/* Quick Geometric Actions */}
              <div className="pt-2 border-t border-[#f0f0f0]">
                <label className="text-[#707070] block mb-1.5 font-medium">Thao tác hình học nhanh:</label>
                <div className="space-y-1.5">
                  <button
                    onClick={() => onQuickGeom?.('diagonal')}
                    className="w-full text-left p-2.5 rounded-xl bg-[#ffffff] hover:bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414] transition cursor-pointer"
                  >
                    <div className="font-semibold text-[#141414]">Kẻ đường chéo AC' = a√3</div>
                    <div className="text-[10px] text-[#707070]">Định lý Pytago 2 bước không gian</div>
                  </button>

                  <button
                    onClick={() => onQuickGeom?.('altitude')}
                    className="w-full text-left p-2.5 rounded-xl bg-[#ffffff] hover:bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414] transition cursor-pointer"
                  >
                    <div className="font-semibold text-[#141414]">Hạ vuông góc AH ⊥ B'D'</div>
                    <div className="text-[10px] text-[#707070]">Khoảng cách từ 1 điểm đến đường thẳng</div>
                  </button>

                  <button
                    onClick={() => onQuickGeom?.('cross_section')}
                    className="w-full text-left p-2.5 rounded-xl bg-[#ffffff] hover:bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414] transition cursor-pointer"
                  >
                    <div className="font-semibold text-[#141414]">Cắt thiết diện (A'BD)</div>
                    <div className="text-[10px] text-[#707070]">Thiết diện tam giác đều S = a²√3/2</div>
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
      <div className="p-2.5 border-t border-[#e0e0e0] text-center text-[10px] text-[#707070] bg-[#ffffff]">
        Phím tắt: <code>T</code> để ẩn/hiện thanh công cụ
      </div>
    </aside>
  );
}

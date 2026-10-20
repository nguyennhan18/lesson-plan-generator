import React, { useState } from 'react';
import { Box, LineChart, ChevronRight, Sliders, Eye } from 'lucide-react';
import FunctionPlotter from './FunctionPlotter';

export default function RightToolsDock({
  isOpen,
  onToggle,
  polyhedronType,
  setPolyhedronType,
  edgeLength,
  setEdgeLength,
  showHiddenLines,
  setShowHiddenLines,
  showVertexLabels,
  setShowVertexLabels,
  showAxes,
  setShowAxes,
  onCameraPreset,
  onQuickGeom
}) {
  const [subTab, setSubTab] = useState('3d'); // '3d' or 'graph'

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

              {/* Edge Length Slider */}
              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Kích thước cạnh a:</span>
                  <span className="text-cyan-400 font-mono font-semibold">{edgeLength.toFixed(1)} cm</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max="6"
                  step="0.5"
                  value={edgeLength}
                  onChange={(e) => setEdgeLength(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400"
                />
              </div>

              {/* Camera Presets */}
              <div>
                <label className="text-slate-400 block mb-1">Góc nhìn chuẩn SGK:</label>
                <div className="grid grid-cols-3 gap-1">
                  <button
                    onClick={() => onCameraPreset('iso')}
                    className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 text-[11px] text-slate-300 hover:text-cyan-300 border border-slate-800 transition text-center"
                  >
                    Chuẩn SGK
                  </button>
                  <button
                    onClick={() => onCameraPreset('top')}
                    className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 text-[11px] text-slate-300 hover:text-cyan-300 border border-slate-800 transition text-center"
                  >
                    Từ Đỉnh
                  </button>
                  <button
                    onClick={() => onCameraPreset('front')}
                    className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 text-[11px] text-slate-300 hover:text-cyan-300 border border-slate-800 transition text-center"
                  >
                    Trực Diện
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
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={showVertexLabels}
                    onChange={(e) => setShowVertexLabels(e.target.checked)}
                    className="accent-cyan-400 rounded"
                  />
                  <span>Hiện tên các đỉnh (A, B, C...)</span>
                </label>
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

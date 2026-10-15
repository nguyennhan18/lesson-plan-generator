import React from 'react';
import { Users, TrendingUp, Award, AlertCircle } from 'lucide-react';

export default function AnalyticsScreen() {
  const students = [
    { id: 1, name: 'Nguyễn Văn An', score: 9.5, z: '+1.51', t: '65.1', pct: '94%', tier: 'Nâng cao', color: 'text-emerald-400' },
    { id: 2, name: 'Trần Thị Bích', score: 8.5, z: '+0.78', t: '57.8', pct: '78%', tier: 'Nâng cao', color: 'text-emerald-400' },
    { id: 3, name: 'Lê Hoàng Cường', score: 7.5, z: '+0.06', t: '50.6', pct: '52%', tier: 'Đạt chuẩn', color: 'text-cyan-400' },
    { id: 4, name: 'Phạm Minh Đức', score: 6.0, z: '-1.03', t: '39.7', pct: '15%', tier: 'Đạt chuẩn', color: 'text-cyan-400' },
    { id: 5, name: 'Hoàng Khánh Linh', score: 4.0, z: '-2.48', t: '25.2', pct: '3%', tier: 'Cần phụ đạo', color: 'text-rose-400' }
  ];

  return (
    <div className="flex-1 p-5 overflow-y-auto max-w-7xl mx-auto space-y-4">
      {/* Title */}
      <div className="pb-3 border-b border-slate-800">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>📊</span> Trung Tâm Phân Tích Lớp Học & Bảng Điểm Chuẩn Hóa
        </h2>
        <p className="text-xs text-slate-400">Thống kê điểm số chuẩn hóa, Z-Score, T-Score & Đề xuất phương án phân hóa bài dạy</p>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-2xl border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Sĩ Số Học Sinh</span>
            <Users size={16} className="text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">42</div>
          <div className="text-[11px] text-slate-400">Đã nộp đủ bài khảo sát</div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Điểm Trung Bình (μ)</span>
            <TrendingUp size={16} className="text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-400 font-mono">7.42</div>
          <div className="text-[11px] text-slate-400">Phổ điểm phân phối khá tốt</div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Độ Lệch Chuẩn (σ)</span>
            <AlertCircle size={16} className="text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 font-mono">1.38</div>
          <div className="text-[11px] text-slate-400">Độ phân hóa vừa phải</div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Xếp Loại Trình Độ Lớp</span>
            <Award size={16} className="text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400">CHUẨN (STANDARD)</div>
          <div className="text-[11px] text-slate-400">68% Đạt chuẩn trở lên</div>
        </div>
      </div>

      {/* 2-Col: Differentiation Recommendations + Student Table */}
      <div className="grid grid-cols-12 gap-5">
        {/* Differentiation Cards */}
        <div className="col-span-12 lg:col-span-5 glass-panel p-4 rounded-2xl border-slate-800 space-y-3 text-xs">
          <h3 className="font-bold text-white text-sm pb-2 border-b border-slate-800">
            👥 Khuyến Nghị Phân Hóa Sư Phạm (CV 5512)
          </h3>

          <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-800/60 space-y-1">
            <strong className="text-rose-400 block font-semibold">Nhóm Cần Phụ Đạo (&lt; 5.0) • 4 HS (9.5%)</strong>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              Dùng mô hình 3D xoay chuẩn góc SGK để học sinh nhận biết hình chiếu vuông góc, cho bài tập tính đường chéo mặt đáy AC = a√2.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-800/60 space-y-1">
            <strong className="text-cyan-400 block font-semibold">Nhóm Đạt Chuẩn (5.0 - 8.0) • 26 HS (61.9%)</strong>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              Luyện tập tính khoảng cách đường vuông góc AH ⊥ B'D' và làm các câu hỏi trắc nghiệm củng cố.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-800/60 space-y-1">
            <strong className="text-emerald-400 block font-semibold">Nhóm Nâng Cao (&gt; 8.0) • 12 HS (28.6%)</strong>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              Yêu cầu dựng thiết diện mặt phẳng tổng quát qua trục đối xứng, chứng minh tính vuông góc giữa $AC'$ và $(A'BD)$.
            </p>
          </div>
        </div>

        {/* Matrix Table */}
        <div className="col-span-12 lg:col-span-7 glass-panel p-4 rounded-2xl border-slate-800 space-y-3 text-xs">
          <h3 className="font-bold text-white text-sm pb-2 border-b border-slate-800">
            📋 Bảng Điểm & Chỉ Số Chuẩn Hóa Z-Score / T-Score
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                  <th className="py-2 px-2">STT</th>
                  <th className="py-2 px-2">Họ và Tên</th>
                  <th className="py-2 px-2">Điểm Gốc</th>
                  <th className="py-2 px-2">Z-Score</th>
                  <th className="py-2 px-2">T-Score</th>
                  <th className="py-2 px-2">Thứ Hạng</th>
                  <th className="py-2 px-2">Phân Nhóm</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {students.map((st) => (
                  <tr key={st.id} className="hover:bg-slate-900/40 transition">
                    <td className="py-2 px-2 font-mono text-slate-500">{st.id}</td>
                    <td className="py-2 px-2 font-semibold text-white">{st.name}</td>
                    <td className="py-2 px-2 font-bold font-mono text-cyan-300">{st.score}</td>
                    <td className="py-2 px-2 font-mono">{st.z}</td>
                    <td className="py-2 px-2 font-mono text-slate-300">{st.t}</td>
                    <td className="py-2 px-2 font-mono text-slate-400">{st.pct}</td>
                    <td className={`py-2 px-2 font-semibold ${st.color}`}>{st.tier}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

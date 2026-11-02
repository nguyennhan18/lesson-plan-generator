import React, { useState, useRef } from 'react';
import {
  Users,
  TrendingUp,
  Award,
  AlertCircle,
  UploadCloud,
  FileSpreadsheet,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Download
} from 'lucide-react';

const DEFAULT_ANALYTICS_DATA = {
  total_students: 42,
  mean: 7.42,
  std_dev: 1.38,
  cv: 18.6,
  min_score: 4.0,
  max_score: 9.5,
  q1: 6.5,
  median: 7.5,
  q3: 8.5,
  rate_below_5: 9.5,
  rate_above_8: 28.6,
  class_label: 'standard',
  target_outcome:
    'Lớp có mặt bằng học lực đạt chuẩn chương trình: Đảm bảo đầy đủ yêu cầu cần đạt theo Công văn 5512, cân bằng giữa lý thuyết trọng tâm và bài tập vận dụng.',
  warning_notes: [],
  student_evaluations: [
    {
      name: 'Nguyễn Văn An',
      score: 9.5,
      z_score: 1.51,
      t_score: 65.1,
      student_label: 'Giỏi',
      recommendation: 'Giao bài tập vận dụng cao và câu hỏi mở rộng tư duy.'
    },
    {
      name: 'Trần Thị Bích',
      score: 8.5,
      z_score: 0.78,
      t_score: 57.8,
      student_label: 'Giỏi',
      recommendation: 'Giao bài tập vận dụng cao và câu hỏi mở rộng tư duy.'
    },
    {
      name: 'Lê Hoàng Cường',
      score: 7.5,
      z_score: 0.06,
      t_score: 50.6,
      student_label: 'Khá',
      recommendation: 'Duy trì nhịp độ chuẩn, rèn luyện kỹ năng giải bài tập thông hiểu và vận dụng.'
    },
    {
      name: 'Phạm Minh Đức',
      score: 6.0,
      z_score: -1.03,
      t_score: 39.7,
      student_label: 'Trung bình',
      recommendation: 'Tăng cường ví dụ minh họa trực quan và bài tập củng cố định nghĩa.'
    },
    {
      name: 'Hoàng Khánh Linh',
      score: 4.0,
      z_score: -2.48,
      t_score: 25.2,
      student_label: 'Yếu',
      recommendation: 'Cần phụ đạo sát sao, chia nhỏ bước giải và ôn tập lại kiến thức nền tảng.'
    }
  ]
};

export default function AnalyticsScreen({
  analyticsData,
  onClassificationSuccess,
  onApplyToLessonPlan
}) {
  const [data, setData] = useState(analyticsData || DEFAULT_ANALYTICS_DATA);
  const [uploadedFilename, setUploadedFilename] = useState(analyticsData?.filename || null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch('/api/v1/ingest/classify-grades', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Lỗi HTTP ${res.status}`);
      }

      const result = await res.json();
      setData(result);
      setUploadedFilename(file.name);

      if (onClassificationSuccess) {
        onClassificationSuccess(result);
      }
    } catch (err) {
      setUploadError(err.message || 'Không thể phân tích file bảng điểm. Vui lòng kiểm tra định dạng .xlsx / .csv.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Tạo file CSV mẫu để giáo viên có thể tải về test ngay lập tức
  const handleDownloadSampleCsv = () => {
    const csvContent = [
      'STT,Họ và Tên,Điểm Toán',
      '1,Nguyễn Văn An,9.5',
      '2,Trần Thị Bích,8.8',
      '3,Lê Hoàng Cường,8.2',
      '4,Phạm Minh Đức,7.5',
      '5,Hoàng Khánh Linh,7.0',
      '6,Đỗ Quang Minh,8.5',
      '7,Vũ Ngọc Mai,9.0',
      '8,Bùi Tiến Dũng,6.8',
      '9,Đặng Thu Thảo,8.0',
      '10,Ngô Gia Bảo,5.5'
    ].join('\n');

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'Bang_Diem_Lop_10A1_Mau.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const labelBadge = {
    basic: {
      title: 'CƠ BẢN (BASIC)',
      color: 'text-[#141414]',
      bg: 'bg-[#f3f3f3] border-[#e0e0e0]',
      desc: 'Ưu tiên củng cố nền tảng & trực quan hóa'
    },
    standard: {
      title: 'CHUẨN (STANDARD)',
      color: 'text-[#141414]',
      bg: 'bg-[#f3f3f3] border-[#e0e0e0]',
      desc: 'Đạt chuẩn chương trình GDPT 2018'
    },
    advanced: {
      title: 'NÂNG CAO (ADVANCED)',
      color: 'text-[#141414]',
      bg: 'bg-[#f3f3f3] border-[#e0e0e0]',
      desc: 'Mở rộng bài toán vận dụng cao & chứa tham số'
    }
  }[data.class_label || 'standard'];

  const total = data.total_students || 1;
  const rateBelow5 = Number(data.rate_below_5 ?? 0);
  const rateAbove8 = Number(data.rate_above_8 ?? 0);
  const rateStandard = Math.max(0, Number((100 - rateBelow5 - rateAbove8).toFixed(1)));

  const countBelow5 = Math.round((rateBelow5 * total) / 100);
  const countAbove8 = Math.round((rateAbove8 * total) / 100);
  const countStandard = Math.max(0, total - countBelow5 - countAbove8);

  return (
    <div className="flex-1 p-5 overflow-y-auto max-w-7xl mx-auto space-y-4 bg-[#ffffff] text-[#141414]">
      {/* Header + Nút Upload Excel/CSV */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#e0e0e0]">
        <div>
          <h2 className="text-xl font-bold text-[#141414] flex items-center gap-2">
            Trung Tâm Phân Tích Lớp Học & Bảng Điểm Chuẩn Hóa
          </h2>
          <p className="text-xs text-[#707070] mt-0.5">
            Tải lên bảng điểm (.xlsx, .csv) để tính Z-Score / T-Score thực tế và tự động phân hóa giáo án 5512
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleDownloadSampleCsv}
            className="px-3.5 py-1.5 rounded-full bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] border border-[#e0e0e0] text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
            title="Tải file CSV bảng điểm mẫu để thử nghiệm"
          >
            <Download size={14} className="text-[#141414]" /> Tải File Điểm Mẫu (.csv)
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls,.csv"
            onChange={handleFileChange}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="px-4 py-2 rounded-full bg-[#141414] hover:bg-[#262626] text-white text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50 cursor-pointer shadow-none"
          >
            <UploadCloud size={15} />
            {isUploading ? 'Đang phân tích Z-Score...' : 'Tải Bảng Điểm (.xlsx / .csv)'}
          </button>

          {onApplyToLessonPlan && (
            <button
              type="button"
              onClick={() => onApplyToLessonPlan(data.class_label, data.target_outcome)}
              className="px-4 py-2 rounded-full bg-[#f3f3f3] hover:bg-[#e0e0e0] text-[#141414] border border-[#e0e0e0] text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
            >
              <span>Áp Dụng Mức "{labelBadge.title}" Để Soạn Giáo Án</span>
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Trạng thái File vừa tải lên hoặc Lỗi */}
      {uploadedFilename && !uploadError && (
        <div className="p-3.5 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-[#141414]">
            <CheckCircle2 size={16} className="text-[#10b981] shrink-0" />
            <span>
              Đã phân tích thành công tệp <strong className="text-[#141414]">{uploadedFilename}</strong> ({data.total_students} học sinh) • Tự động đồng bộ mức học lực <strong className="text-[#141414] uppercase">{data.class_label}</strong> sang cấu hình sinh Giáo án!
            </span>
          </div>
        </div>
      )}

      {uploadError && (
        <div className="p-3.5 rounded-2xl bg-[#ffffff] border border-[#ef4444] text-[#ef4444] text-xs flex items-center gap-2">
          <AlertTriangle size={16} className="text-[#ef4444] shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* 4 KPI Cards (Mobbin pricing-card style) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-1">
          <div className="flex items-center justify-between text-[#707070] text-xs font-semibold">
            <span>SĨ SỐ HỌC SINH</span>
            <Users size={16} className="text-[#141414]" />
          </div>
          <div className="text-3xl font-bold text-[#141414] font-mono">{data.total_students}</div>
          <div className="text-[11px] text-[#707070]">
            Thấp: {data.min_score}đ • Cao: {data.max_score}đ
          </div>
        </div>

        <div className="p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-1">
          <div className="flex items-center justify-between text-[#707070] text-xs font-semibold">
            <span>ĐIỂM TRUNG BÌNH (μ)</span>
            <TrendingUp size={16} className="text-[#141414]" />
          </div>
          <div className="text-3xl font-bold text-[#141414] font-mono">{data.mean}</div>
          <div className="text-[11px] text-[#707070]">
            Trung vị: {data.median ?? data.mean}đ
          </div>
        </div>

        <div className="p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-1">
          <div className="flex items-center justify-between text-[#707070] text-xs font-semibold">
            <span>ĐỘ LỆCH CHUẨN (σ) & CV%</span>
            <AlertCircle size={16} className="text-[#141414]" />
          </div>
          <div className="text-3xl font-bold text-[#141414] font-mono">
            {data.std_dev} <span className="text-xs font-normal text-[#707070]">(CV: {data.cv ?? 18.0}%)</span>
          </div>
          <div className="text-[11px] text-[#707070]">
            {(data.cv ?? 18) >= 28 ? 'Phân hóa cao giữa các nhóm' : 'Phổ điểm đồng đều, ổn định'}
          </div>
        </div>

        <div className="p-5 rounded-[24px] bg-[#f3f3f3] border border-[#e0e0e0] space-y-1">
          <div className="flex items-center justify-between text-[#707070] text-xs font-semibold">
            <span>XẾP LOẠI TRÌNH ĐỘ</span>
            <Award size={16} className="text-[#141414]" />
          </div>
          <div className={`text-xl font-bold text-[#141414]`}>{labelBadge.title}</div>
          <div className="text-[11px] text-[#707070]">{labelBadge.desc}</div>
        </div>
      </div>

      {/* 2-Col: Differentiation Recommendations + Student Table */}
      <div className="grid grid-cols-12 gap-5">
        {/* Differentiation Cards */}
        <div className="col-span-12 lg:col-span-5 p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-3.5 text-xs text-[#141414]">
          <h3 className="font-bold text-[#141414] text-sm pb-2 border-b border-[#e0e0e0] flex items-center justify-between">
            <span>Khuyến Nghị Phân Hóa Sư Phạm (CV 5512)</span>
            <FileSpreadsheet size={15} className="text-[#141414]" />
          </h3>

          {/* Mục tiêu đầu ra tự động kết xuất từ GradeClassifier */}
          <div className={`p-3.5 rounded-2xl border ${labelBadge.bg} space-y-1`}>
            <strong className="text-[#141414] block font-bold">
              Định hướng tự động truyền sang AI Sinh Giáo Án:
            </strong>
            <p className="text-[#141414] text-[11px] leading-relaxed">{data.target_outcome}</p>
          </div>

          {Array.isArray(data.warning_notes) &&
            data.warning_notes.map((warn, idx) => (
              <div
                key={idx}
                className="p-3 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414] text-[11px] leading-relaxed"
              >
                {warn}
              </div>
            ))}

          <div className="p-3.5 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] space-y-1">
            <strong className="text-[#141414] block font-bold">
              Nhóm Cần Phụ Đạo (&lt; 5.0) • {countBelow5} HS ({rateBelow5}%)
            </strong>
            <p className="text-[#707070] text-[11px] leading-relaxed">
              Tập trung nhận diện hệ số $a, b, c$, quan sát trực quan đồ thị Parabol cắt trục $Ox$ và chia nhỏ từng bước tính biệt thức $\Delta$.
            </p>
          </div>

          <div className="p-3.5 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] space-y-1">
            <strong className="text-[#141414] block font-bold">
              Nhóm Đạt Chuẩn (5.0 - 8.0) • {countStandard} HS ({rateStandard}%)
            </strong>
            <p className="text-[#707070] text-[11px] leading-relaxed">
              Rèn luyện thành thạo 4 bước giải phương trình bậc hai, tránh bẫy sai dấu $-b$ và áp dụng hệ thức Vi-ét nhẩm nghiệm.
            </p>
          </div>

          <div className="p-3.5 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] space-y-1">
            <strong className="text-[#141414] block font-bold">
              Nhóm Nâng Cao (&gt; 8.0) • {countAbove8} HS ({rateAbove8}%)
            </strong>
            <p className="text-[#707070] text-[11px] leading-relaxed">
              Thử thách bài toán biện luận tham số $m$ để phương trình có hai nghiệm phân biệt thỏa mãn biểu thức đối xứng $x_1^2 + x_2^2$.
            </p>
          </div>
        </div>

        {/* Matrix Table */}
        <div className="col-span-12 lg:col-span-7 p-5 rounded-[24px] bg-[#ffffff] border border-[#e0e0e0] space-y-3 text-xs text-[#141414]">
          <div className="flex items-center justify-between pb-2 border-b border-[#e0e0e0]">
            <h3 className="font-bold text-[#141414] text-sm">
              Bảng Điểm & Chỉ Số Chuẩn Hóa Z-Score / T-Score
            </h3>
            <span className="text-[11px] text-[#707070]">
              Hiển thị {(data.student_evaluations || []).length} bản ghi
            </span>
          </div>

          <div className="overflow-x-auto max-h-[380px] overflow-y-auto">
            <table className="w-full text-left">
              <thead className="sticky top-0 bg-[#f3f3f3] z-10">
                <tr className="border-b border-[#e0e0e0] text-[#707070] text-[11px]">
                  <th className="py-2.5 px-3">STT</th>
                  <th className="py-2.5 px-3">Học Sinh</th>
                  <th className="py-2.5 px-3">Điểm Gốc</th>
                  <th className="py-2.5 px-3">Z-Score</th>
                  <th className="py-2.5 px-3">T-Score</th>
                  <th className="py-2.5 px-3">Xếp Loại</th>
                  <th className="py-2.5 px-3">Khuyến Nghị</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e0e0e0]">
                {(data.student_evaluations || []).map((st, idx) => {
                  const zNum = Number(st.z_score ?? 0);
                  const zFormatted = zNum > 0 ? `+${zNum.toFixed(2)}` : zNum.toFixed(2);

                  return (
                    <tr key={idx} className="hover:bg-[#f3f3f3] transition">
                      <td className="py-2.5 px-3 font-mono text-[#707070]">{idx + 1}</td>
                      <td className="py-2.5 px-3 font-semibold text-[#141414]">
                        {st.name || `Học sinh #${idx + 1}`}
                      </td>
                      <td className="py-2.5 px-3 font-bold font-mono text-[#141414]">{st.score}</td>
                      <td className="py-2.5 px-3 font-mono text-[#707070]">{zFormatted}</td>
                      <td className="py-2.5 px-3 font-mono text-[#707070]">{st.t_score}</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2.5 py-0.5 rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-[10px] font-semibold text-[#141414]">
                          {st.student_label}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-[11px] text-[#707070] max-w-xs">
                        {st.recommendation}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

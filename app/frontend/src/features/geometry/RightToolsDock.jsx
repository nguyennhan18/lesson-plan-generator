import React from 'react';
export default function RightToolsDock({isOpen,onToggle}) {
  if(!isOpen)return null;
  return <aside className="w-64 p-4 border-l"><button onClick={onToggle}>Đóng công cụ</button><p className="mt-4">Dữ kiện hình và đồ thị được nhập, đối chiếu và lưu tại từng slide. Chọn slide có yêu cầu trực quan để chỉnh sửa.</p></aside>;
}

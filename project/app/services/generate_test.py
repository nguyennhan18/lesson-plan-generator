import sys
from pathlib import Path

# Thêm đường dẫn thư mục gốc app/ hoặc project/ vào Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from exporters.slide_exporter import export_slide_to_pptx

# Dữ liệu test thử nghiệm cho Slide 1 và các slide công thức
test_slides = [
    {
        "title": "Slide 1: Khảo sát Hàm số Bậc hai",
        "content": [
            "Hàm số $y = x^2 - 4x + 3$ có đỉnh $I(2, -1)$.",
            "Trục đối xứng là đường thẳng $x = 2$.",
            "Bề lõm quay lên trên do $a = 1 > 0$."
        ],
        "chart_config": {
            "plot_type": "function",
            "expression": "x**2 - 4*x + 3",
            "x_range": [-1, 5],
            "title": "Đồ thị hàm số y = x² - 4x + 3" # Title chuẩn, không dính prompt
        }
    },
    {
        "title": "Slide 2: Công thức Nghiệm Phương trình Bậc hai",
        "content": [
            "Xét phương trình $ax^2 + bx + c = 0$ ($a \\neq 0$).",
            "Biệt thức $\\Delta = b^2 - 4ac$.",
            "Nếu $\\Delta > 0$, phương trình có 2 nghiệm phân biệt:"
        ],
        "latex_equation": "x_{1,2} = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}" # Sẽ tự động render thành ảnh bên phải
    }
]

if __name__ == "__main__":
    export_slide_to_pptx(test_slides, "slide_test.pptx")
    print("Đã regenerate file slide_test.pptx thành công!")
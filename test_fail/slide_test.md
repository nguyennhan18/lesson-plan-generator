Dưới đây là thiết kế Slide bài giảng dạng Markdown chuẩn Marp CLI cho bài "Cấp số cộng":

```markdown
---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #ffffff
color: #2c3e50
---

# Bài 3: CẤP SỐ CỘNG
## Môn: Toán học - Lớp 11
### Đại số và Giải tích

<!--
[Kịch bản GV]: Chào mừng các em đến với bài học hôm nay. Trước khi bắt đầu, thầy/cô muốn các em chuẩn bị sẵn sàng vở ghi, bút và tinh thần học tập thật sôi nổi nhé. Hôm nay, chúng ta sẽ cùng nhau khám phá một khái niệm rất thú vị trong toán học, đó là "Cấp số cộng".
-->

---

_class: default

## Mục tiêu bài học

### 🎯 Về kiến thức:
*   Nắm vững **định nghĩa** cấp số cộng và **công sai**.
*   Nắm vững **công thức số hạng tổng quát**: $u_n = u_1 + (n-1)d$.
*   Nắm vững **công thức tính tổng $n$ số hạng đầu tiên**:
    $S_n = \frac{n(u_1 + u_n)}{2}$ hoặc $S_n = \frac{n[2u_1 + (n-1)d]}{2}$.
*   Nhận biết được một dãy số là cấp số cộng.

### 🚀 Về kĩ năng:
*   Vận dụng định nghĩa để **chứng minh** một dãy số là cấp số cộng.
*   **Tính** được số hạng bất kì và tổng $n$ số hạng đầu tiên.
*   **Giải quyết** các bài toán thực tế liên quan.
*   Phát triển tư duy logic, khả năng làm việc nhóm.

<!--
[Kịch bản GV]: Để khởi đầu bài học một cách hiệu quả, chúng ta cần nắm rõ các mục tiêu mà chúng ta sẽ đạt được. Về kiến thức, các em cần hiểu rõ định nghĩa, các công thức quan trọng như số hạng tổng quát và tổng $n$ số hạng đầu tiên. Về kỹ năng, chúng ta sẽ cùng nhau luyện tập để vận dụng các kiến thức này vào giải quyết các bài tập từ cơ bản đến ứng dụng thực tế. Hãy cùng nhau cố gắng để đạt được tất cả các mục tiêu này nhé!
-->

---

_class: default

## I. Khởi động

### ❓ Tình huống thực tế

Một người thợ làm việc có mức lương khởi điểm là 5 triệu đồng/tháng. Cứ sau mỗi năm, lương của anh ta được tăng thêm 500 nghìn đồng.

Hãy viết dãy số biểu thị mức lương của người thợ đó sau 1 năm, 2 năm, 3 năm, 4 năm làm việc.
Dãy số này có quy luật gì đặc biệt?

<!--
[Kịch bản GV]: Chúng ta hãy cùng bắt đầu bài học với một tình huống thực tế để tạo hứng thú và gợi mở kiến thức nhé. Các em hãy quan sát tình huống trên slide và suy nghĩ, thảo luận nhóm nhỏ để tìm ra đáp án. Dãy số mức lương sẽ là bao nhiêu và có quy luật gì đặc biệt? Thầy/cô sẽ cho các em 2 phút để thảo luận và trình bày.
-->

---

_class: default

## I. Khởi động (tiếp)

### 💡 Lời giải và nhận xét

*   **Mức lương sau 1 năm**: 5 triệu + 0.5 triệu = 5.5 triệu đồng.
*   **Mức lương sau 2 năm**: 5.5 triệu + 0.5 triệu = 6 triệu đồng.
*   **Mức lương sau 3 năm**: 6 triệu + 0.5 triệu = 6.5 triệu đồng.
*   **Mức lương sau 4 năm**: 6.5 triệu + 0.5 triệu = 7 triệu đồng.

➡️ Dãy số mức lương: **5.5; 6; 6.5; 7; ...**

### Quy luật đặc biệt:
Mỗi số hạng (kể từ số hạng thứ hai) đều lớn hơn số hạng đứng ngay trước nó một lượng không đổi là **0.5 triệu đồng**.

<!--
[Kịch bản GV]: Mời đại diện một nhóm hoặc một em học sinh chia sẻ kết quả của mình. (Chờ HS trả lời). Rất tốt! Các em đã nhận ra rằng dãy số mức lương là 5.5 triệu, 6 triệu, 6.5 triệu, 7 triệu và cứ thế tiếp tục. Và điều đặc biệt ở đây là mỗi số hạng đứng sau đều lớn hơn số hạng đứng trước nó một lượng không đổi là 0.5 triệu đồng. Dãy số có quy luật như vậy được gọi là một **cấp số cộng**. Vậy cấp số cộng là gì và chúng ta sẽ tìm hiểu những công thức nào liên quan đến nó? Chúng ta cùng vào bài học hôm nay.
-->

---

_class: default

## II. Cấp số cộng

### 1. Định nghĩa

<br>
<br>

**Cấp số cộng** là một dãy số (hữu hạn hoặc vô hạn), trong đó kể từ số hạng thứ hai, mỗi số hạng đều bằng số hạng đứng ngay trước nó cộng với một số không đổi $d$.

Số $d$ được gọi là **công sai** của cấp số cộng.

<br>

**Công thức truy hồi**:
$$ u_{n+1} = u_n + d \quad (\text{với } n \ge 1) $$

<!--
[Kịch bản GV]: Dựa trên ví dụ khởi động vừa rồi, các em có thể thấy rõ định nghĩa của cấp số cộng. Đó là một dãy số mà sự chênh lệch giữa hai số hạng liên tiếp luôn là một hằng số. Hằng số đó chính là công sai $d$. Các em hãy ghi nhớ công thức truy hồi $u_{n+1} = u_n + d$, nó thể hiện mối quan hệ giữa một số hạng và số hạng liền sau nó.
-->

---

_class: default

## II. Cấp số cộng (tiếp)

### 2. Công thức số hạng tổng quát

Cho một cấp số cộng $(u_n)$ với số hạng đầu $u_1$ và công sai $d$.

*   $u_2 = u_1 + d$
*   $u_3 = u_2 + d = (u_1 + d) + d = u_1 + 2d$
*   $u_4 = u_3 + d = (u_1 + 2d) + d = u_1 + 3d$
*   ...

Từ đó, ta có **Công thức số hạng tổng quát**:
$$ u_n = u_1 + (n-1)d \quad (\text{với } n \ge 1) $$

<br>

**Ví dụ**: Cho cấp số cộng có $u_1 = 3$ và công sai $d = 2$.
Tìm số hạng thứ 7 ($u_7$).
*Giải*: $u_7 = u_1 + (7-1)d = 3 + 6 \cdot 2 = 3 + 12 = 15$.

<!--
[Kịch bản GV]: Từ định nghĩa, chúng ta có thể dễ dàng tìm ra công thức cho bất kỳ số hạng nào của cấp số cộng mà không cần phải liệt kê từng số hạng một. Quan sát cách chúng ta biểu diễn $u_2, u_3, u_4$ theo $u_1$ và $d$, các em có thể nhận thấy một quy luật. Đó chính là công thức số hạng tổng quát $u_n = u_1 + (n-1)d$. Đây là một công thức rất quan trọng, giúp chúng ta tính toán nhanh chóng. Hãy cùng xem ví dụ minh họa trên slide để hiểu rõ hơn cách áp dụng công thức này.
-->

---

_class: default

## II. Cấp số cộng (tiếp)

### 3. Tính chất của cấp số cộng

Nếu ba số $u_{k-1}, u_k, u_{k+1}$ là ba số hạng liên tiếp của một cấp số cộng, thì ta có:

$$ u_k = \frac{u_{k-1} + u_{k+1}}{2} \quad (\text{với } k \ge 2) $$

<br>

**Chứng minh**:
Theo định nghĩa cấp số cộng:
*   $u_k = u_{k-1} + d \quad \Rightarrow d = u_k - u_{k-1}$
*   $u_{k+1} = u_k + d \quad \Rightarrow d = u_{k+1} - u_k$

Do đó: $u_k - u_{k-1} = u_{k+1} - u_k$
$\Rightarrow 2u_k = u_{k-1} + u_{k+1}$
$\Rightarrow u_k = \frac{u_{k-1} + u_{k+1}}{2}$ (Điều phải chứng minh)

<!--
[Kịch bản GV]: Ngoài công thức số hạng tổng quát, cấp số cộng còn có một tính chất rất đặc biệt liên quan đến ba số hạng liên tiếp của nó. Đó là số hạng ở giữa sẽ bằng trung bình cộng của hai số hạng đứng kề nó. Các em có thể thấy phần chứng minh trên slide, nó rất đơn giản và trực tiếp từ định nghĩa của cấp số cộng. Tính chất này rất hữu ích trong việc kiểm tra một dãy số có phải là cấp số cộng hay không, hoặc tìm các số hạng bị thiếu.
-->

---

_class: default

## II. Cấp số cộng (tiếp)

### 4. Công thức tính tổng $n$ số hạng đầu tiên

Gọi $S_n$ là tổng của $n$ số hạng đầu tiên của cấp số cộng $(u_n)$:
$$ S_n = u_1 + u_2 + ... + u_n $$

**Công thức 1**:
$$ S_n = \frac{n(u_1 + u_n)}{2} $$

<br>

**Công thức 2**: (Thay $u_n = u_1 + (n-1)d$ vào Công thức 1)
$$ S_n = \frac{n[2u_1 + (n-1)d]}{2} $$

<!--
[Kịch bản GV]: Bây giờ chúng ta sẽ đến với một công thức quan trọng khác, đó là công thức tính tổng của $n$ số hạng đầu tiên của một cấp số cộng. Đôi khi chúng ta cần tính tổng của một dãy số dài, việc cộng từng số hạng sẽ rất mất thời gian. Hai công thức này sẽ giúp chúng ta làm điều đó một cách nhanh chóng. Công thức thứ hai được suy ra trực tiếp từ công thức thứ nhất bằng cách thay thế $u_n$ bằng công thức số hạng tổng quát. Các em hãy ghi nhớ cả hai công thức này và biết cách lựa chọn công thức phù hợp với từng bài toán cụ thể.
-->

---

_class: default

## III. Luyện tập

### Bài 1

Cho cấp số cộng có $u_1 = 3$ và công sai $d = 2$.
Tìm số hạng thứ 7 của cấp số cộng đó.

<br>

### Bài 2

Dãy số nào sau đây là cấp số cộng? Nếu là cấp số cộng, hãy tìm công sai của nó.
a) $1, 4, 7, 10, 13, ...$
b) $2, 4, 8, 16, 32, ...$

<!--
[Kịch bản GV]: Để củng cố kiến thức vừa học, chúng ta hãy cùng nhau làm một số bài tập luyện tập nhé. Các em hãy làm việc cá nhân hoặc thảo luận nhóm nhỏ để giải quyết Bài 1 và Bài 2 trên slide. Thầy/cô sẽ dành 3-4 phút cho phần này. Sau đó, thầy/cô sẽ mời một số em lên bảng trình bày lời giải.
-->

---

_class: default

## III. Luyện tập (tiếp)

### Lời giải Bài 1 & 2

**Bài 1**:
Áp dụng công thức số hạng tổng quát $u_n = u_1 + (n-1)d$:
$u_7 = u_1 + (7-1)d = 3 + 6 \cdot 2 = 3 + 12 = 15$.
Vậy, số hạng thứ 7 là **15**.

**Bài 2**:
a) $1, 4, 7, 10, 13, ...$
   *   $4 - 1 = 3$
   *   $7 - 4 = 3$
   *   $10 - 7 = 3$
   *   $13 - 10 = 3$
   $\Rightarrow$ Đây là cấp số cộng với công sai $d = \mathbf{3}$.

b) $2, 4, 8, 16, 32, ...$
   *   $4 - 2 = 2$
   *   $8 - 4 = 4$
   *   $16 - 8 = 8$
   $\Rightarrow$ Hiệu giữa các số hạng liên tiếp không không đổi.
   $\Rightarrow$ Đây **không phải** là cấp số cộng.

<!--
[Kịch bản GV]: Mời một em học sinh trình bày lời giải Bài 1. (Chờ HS). Rất chính xác! Chúng ta chỉ cần áp dụng công thức $u_n = u_1 + (n-1)d$ là sẽ tìm được $u_7 = 15$. Tiếp theo, mời một em khác lên trình bày Bài 2. (Chờ HS). Đúng vậy! Để kiểm tra một dãy số có phải là cấp số cộng hay không, chúng ta chỉ cần xem xét hiệu của các số hạng liên tiếp. Nếu hiệu đó là một hằng số, thì đó chính là công sai và dãy số đó là cấp số cộng. Các em đã làm rất tốt!
-->

---

_class: default

## III. Luyện tập (tiếp)

### Bài 3

Tính tổng 10 số hạng đầu tiên của cấp số cộng ở Bài 1 (có $u_1 = 3$ và $d = 2$).

<!--
[Kịch bản GV]: Tiếp tục với bài tập thứ 3. Các em hãy tính tổng 10 số hạng đầu tiên của cấp số cộng mà chúng ta đã dùng ở Bài 1. Các em có thể sử dụng một trong hai công thức tính tổng mà chúng ta vừa học. Thầy/cô sẽ cho các em 2 phút để làm bài này.
-->

---

_class: default

## III. Luyện tập (tiếp)

### Lời giải Bài 3

**Bài 3**:
Cấp số cộng có $u_1 = 3$ và $d = 2$.
Để tính $S_{10}$, ta có thể dùng công thức $S_n = \frac{n[2u_1 + (n-1)d]}{2}$.
Với $n=10, u_1=3, d=2$:
$S_{10} = \frac{10[2 \cdot 3 + (10-1)2]}{2}$
$S_{10} = 5[6 + 9 \cdot 2]$
$S_{10} = 5[6 + 18]$
$S_{10} = 5 \cdot 24$
$S_{10} = 120$.

*Hoặc, tính $u_{10}$ trước rồi dùng $S_n = \frac{n(u_1 + u_n)}{2}$:*
$u_{10} = u_1 + (10-1)d = 3 + 9 \cdot 2 = 3 + 18 = 21$.
$S_{10} = \frac{10(u_1 + u_{10})}{2} = \frac{10(3 + 21)}{2} = \frac{10 \cdot 24}{2} = 120$.

Vậy, tổng 10 số hạng đầu tiên là **120**.

<!--
[Kịch bản GV]: Mời một em học sinh lên bảng trình bày lời giải Bài 3. (Chờ HS). Rất tốt! Các em có thể thấy cả hai cách đều cho ra cùng một kết quả. Điều quan trọng là các em phải nắm vững các công thức và biết cách áp dụng chúng một cách linh hoạt. Các em đã hoàn thành tốt các bài tập cơ bản. Bây giờ, chúng ta sẽ cùng nhau thử sức với một bài toán ứng dụng thực tế nhé.
-->

---

_class: default

## IV. Vận dụng: Bài toán thực tế

### Bài toán

Một rạp hát có 20 hàng ghế. Hàng đầu tiên có 12 ghế, hàng thứ hai có 14 ghế, hàng thứ ba có 16 ghế và cứ thế tiếp tục.

Hỏi rạp hát đó có tổng cộng bao nhiêu ghế?

<!--
[Kịch bản GV]: Đây là một bài toán rất hay và thực tế, giúp các em thấy được ứng dụng của cấp số cộng trong đời sống. Các em hãy đọc kỹ đề bài, phân tích các thông tin đã cho để xác định các yếu tố của cấp số cộng (u1, d, n) và lựa chọn công thức phù hợp để giải quyết. Thầy/cô sẽ cho các em 3-4 phút để làm bài này.
-->

---

_class: default

## IV. Vận dụng: Bài toán thực tế (tiếp)

### Lời giải bài toán

*   Dãy số ghế trong các hàng tạo thành một cấp số cộng.
*   Số hạng đầu: $u_1 = 12$ (ghế ở hàng đầu tiên).
*   Công sai: $d = 14 - 12 = 2$ (ghế tăng thêm mỗi hàng).
*   Số hàng ghế: $n = 20$.
*   Tổng số ghế trong rạp hát là $S_{20}$.

Áp dụng công thức $S_n = \frac{n[2u_1 + (n-1)d]}{2}$:
$S_{20} = \frac{20[2 \cdot 12 + (20-1)2]}{2}$
$S_{20} = 10[24 + 19 \cdot 2]$
$S_{20} = 10[24 + 38]$
$S_{20} = 10 \cdot 62$
$S_{20} = 620$.

Vậy, rạp hát đó có tổng cộng **620 ghế**.

<!--
[Kịch bản GV]: Mời một em học sinh hoặc đại diện nhóm lên bảng trình bày lời giải bài toán thực tế này. (Chờ HS). Rất xuất sắc! Các em đã biết cách phân tích bài toán, xác định đúng các yếu tố của cấp số cộng và áp dụng công thức một cách chính xác. Bài toán này cho thấy cấp số cộng không chỉ là lý thuyết mà còn có rất nhiều ứng dụng trong thực tế cuộc sống.
-->

---

_class: default

## Tổng kết & Dặn dò

### 📚 Kiến thức trọng tâm:
*   **Định nghĩa cấp số cộng**: $u_{n+1} = u_n + d$.
*   **Công thức số hạng tổng quát**: $u_n = u_1 + (n-1)d$.
*   **Tính chất**: $u_k = \frac{u_{k-1} + u_{k+1}}{2}$.
*   **Công thức tính tổng $n$ số hạng đầu tiên**:
    $S_n = \frac{n(u_1 + u_n)}{2}$ hoặc $S_n = \frac{n[2u_1 + (n-1)d]}{2}$.

### 📝 Bài tập về nhà:
*   Xem lại các ví dụ và bài tập đã chữa.
*   Làm các bài tập trong sách giáo khoa trang [Số trang] (nếu có).
*   Chuẩn bị bài mới: Cấp số nhân.

<!--
[Kịch bản GV]: Vậy là chúng ta đã cùng nhau tìm hiểu và thực hành về Cấp số cộng. Các em hãy nhìn lại các kiến thức trọng tâm trên slide. Đây là những điểm mấu chốt mà các em cần phải ghi nhớ thật kỹ. Về nhà, các em hãy ôn tập lại bài, làm các bài tập trong sách giáo khoa để củng cố kiến thức. Và đừng quên chuẩn bị trước cho bài học tiếp theo của chúng ta là "Cấp số nhân" nhé. Chúc các em học tốt và hẹn gặp lại trong buổi học tới!
-->
```
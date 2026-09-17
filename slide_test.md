```markdown
---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #ffffff
color: #2c3e50
---

# **Bài 3: CẤP SỐ CỘNG**
## Môn: Toán học
### Lớp: 11

<!-- 
[Kịch bản GV]: Chào mừng các em đến với tiết học Toán hôm nay. Chúng ta sẽ cùng nhau khám phá một khái niệm rất thú vị và quan trọng trong chương trình Đại số và Giải tích lớp 11, đó là "Cấp số cộng". Đây là một dạng dãy số đặc biệt có nhiều ứng dụng trong thực tế.
-->

---

# **Mục tiêu bài học**

### **1. Kiến thức:**
*   Nắm vững định nghĩa cấp số cộng.
*   Nêu được công thức số hạng tổng quát: $u_n = u_1 + (n-1)d$.
*   Nêu được tính chất: $u_k = \frac{u_{k-1} + u_{k+1}}{2}$ với $k \ge 2$.
*   Nêu được công thức tính tổng $n$ số hạng đầu tiên: $S_n = \frac{n(u_1 + u_n)}{2}$ hoặc $S_n = \frac{n[2u_1 + (n-1)d]}{2}$.

### **2. Kĩ năng:**
*   Vận dụng định nghĩa để kiểm tra một dãy số có phải là cấp số cộng.
*   Tìm số hạng đầu, công sai, số hạng thứ $n$.
*   Tính tổng của $n$ số hạng đầu tiên.
*   Giải quyết các bài toán thực tế có ứng dụng cấp số cộng.

<!-- 
[Kịch bản GV]: Để bắt đầu bài học, chúng ta hãy cùng nhìn vào các mục tiêu cần đạt được. Về kiến thức, các em cần hiểu rõ định nghĩa, các công thức quan trọng như số hạng tổng quát, tính chất và công thức tính tổng. Về kĩ năng, chúng ta sẽ luyện tập để có thể vận dụng các kiến thức này vào việc giải các bài tập cơ bản và cả các bài toán thực tế.
-->

---

# **1. KHỞI ĐỘNG**

### Hãy quan sát dãy số sau:
$$1, 3, 5, 7, 9, \dots$$

### **Câu hỏi:**
### 1. Dãy số trên có quy luật gì?
### 2. Số hạng tiếp theo của dãy là bao nhiêu?

<!-- 
[Kịch bản GV]: Để khởi động bài học, thầy/cô mời các em cùng quan sát dãy số trên màn hình: 1, 3, 5, 7, 9, ... Các em hãy suy nghĩ cá nhân trong 2 phút để tìm ra quy luật của dãy số này và dự đoán số hạng tiếp theo. Sau đó, hãy thảo luận nhanh với bạn bên cạnh để so sánh kết quả. (Chờ HS suy nghĩ và thảo luận).

(Gọi 1-2 HS trình bày)

GV: Rất tốt! Các em đã nhận ra rằng mỗi số hạng sau bằng số hạng liền trước cộng thêm 2. Vậy số hạng tiếp theo chắc chắn là 11. Các em có thể cho thầy/cô biết hiệu giữa hai số hạng liên tiếp trong dãy này là bao nhiêu không? (HS trả lời: là 2).

GV: Chính xác! Dãy số mà mỗi số hạng (từ số hạng thứ hai trở đi) bằng số hạng liền trước cộng với một số không đổi như vậy được gọi là cấp số cộng. Hôm nay, chúng ta sẽ cùng tìm hiểu kỹ hơn về loại dãy số đặc biệt này.
-->

---

# **2. ĐỊNH NGHĨA CẤP SỐ CỘNG**

### **Định nghĩa:**
Cấp số cộng là một dãy số (hữu hạn hoặc vô hạn) mà trong đó, kể từ số hạng thứ hai trở đi, mỗi số hạng đều bằng **tổng của số hạng đứng ngay trước nó với một số không đổi.**

Số không đổi đó được gọi là **công sai** của cấp số cộng, kí hiệu là $d$.

### **Công thức truy hồi:**
Một dãy số $(u_n)$ là cấp số cộng khi và chỉ khi $u_{n+1} = u_n + d$ với mọi $n \ge 1$.

*Ví dụ: Dãy số 1, 3, 5, 7, 9,... là một cấp số cộng với $u_1 = 1$ và công sai $d = 2$.*

<!-- 
[Kịch bản GV]: Dựa trên hoạt động khởi động vừa rồi, chúng ta có thể đi đến định nghĩa chính thức của cấp số cộng. Các em hãy đọc định nghĩa trên màn hình. Điểm mấu chốt là "mỗi số hạng đều bằng tổng của số hạng đứng ngay trước nó với một số không đổi". Số không đổi đó chính là công sai, ký hiệu là 'd'. Công thức truy hồi $u_{n+1} = u_n + d$ thể hiện rõ điều này. Ví dụ khởi động của chúng ta chính là một cấp số cộng với công sai $d=2$.
-->

---

# **3. CÔNG THỨC SỐ HẠNG TỔNG QUÁT**

### Cho cấp số cộng $(u_n)$ với số hạng đầu $u_1$ và công sai $d$.
### Khi đó, số hạng tổng quát $u_n$ được xác định bởi công thức:
$$u_n = u_1 + (n-1)d$$
### Với mọi $n \ge 1$.

*Giải thích:*
*   $u_2 = u_1 + d$
*   $u_3 = u_2 + d = (u_1 + d) + d = u_1 + 2d$
*   $u_4 = u_3 + d = (u_1 + 2d) + d = u_1 + 3d$
*   ...

<!-- 
[Kịch bản GV]: Từ định nghĩa, chúng ta có thể dễ dàng suy ra công thức tổng quát cho bất kỳ số hạng nào của cấp số cộng. Nếu biết số hạng đầu $u_1$ và công sai $d$, chúng ta có thể tìm được số hạng thứ $n$ bằng công thức: $u_n = u_1 + (n-1)d$. Các em có thể thấy cách suy luận qua các ví dụ $u_2, u_3, u_4$. Đây là một công thức rất quan trọng, giúp chúng ta tính được một số hạng bất kỳ mà không cần phải liệt kê tất cả các số hạng trước đó.
-->

---

# **4. TÍNH CHẤT CỦA CẤP SỐ CỘNG**

### Đối với một cấp số cộng, mỗi số hạng (trừ số hạng đầu và cuối nếu hữu hạn) đều là **trung bình cộng** của hai số hạng đứng kề nó.
### Hay nói cách khác, với $k \ge 2$, ta có:
$$u_k = \frac{u_{k-1} + u_{k+1}}{2}$$
### Tương đương với: $2u_k = u_{k-1} + u_{k+1}$.

*Chứng minh:*
Ta có $u_k - u_{k-1} = d$ và $u_{k+1} - u_k = d$.
$\implies u_k - u_{k-1} = u_{k+1} - u_k$
$\implies 2u_k = u_{k-1} + u_{k+1}$
$\implies u_k = \frac{u_{k-1} + u_{k+1}}{2}$

<!-- 
[Kịch bản GV]: Cấp số cộng còn có một tính chất rất đặc trưng và thú vị. Đó là mỗi số hạng (từ số hạng thứ hai trở đi) đều là trung bình cộng của hai số hạng đứng ngay kề nó. Các em có thể thấy công thức trên màn hình. Tính chất này có thể dễ dàng chứng minh được từ định nghĩa của công sai. Các em hãy ghi nhớ tính chất này, nó rất hữu ích trong việc giải một số bài tập.
-->

---

# **5. CÔNG THỨC TÍNH TỔNG $n$ SỐ HẠNG ĐẦU TIÊN**

### Tổng của $n$ số hạng đầu tiên của một cấp số cộng $(u_n)$, kí hiệu là $S_n$, được tính bằng một trong hai công thức sau:

### **Công thức 1:**
$$S_n = \frac{n(u_1 + u_n)}{2}$$

### **Công thức 2:** (Thay $u_n = u_1 + (n-1)d$ vào Công thức 1)
$$S_n = \frac{n[2u_1 + (n-1)d]}{2}$$

<!-- 
[Kịch bản GV]: Một trong những ứng dụng quan trọng của cấp số cộng là tính tổng của một số hạng đầu tiên. Chúng ta có hai công thức để tính tổng $n$ số hạng đầu tiên, kí hiệu là $S_n$. Công thức thứ nhất là $S_n = \frac{n(u_1 + u_n)}{2}$, tức là tổng của số hạng đầu và số hạng cuối, nhân với số lượng số hạng, rồi chia đôi. Công thức thứ hai được suy ra từ công thức thứ nhất bằng cách thế $u_n = u_1 + (n-1)d$ vào, và nó cho phép chúng ta tính tổng khi chỉ biết $u_1$, $d$ và $n$. Các em cần ghi nhớ cả hai công thức này để linh hoạt áp dụng vào các bài toán khác nhau.
-->

---

# **6. LUYỆN TẬP**

### **Bài 1:**
Cho cấp số cộng $(u_n)$ có $u_1 = 2$ và công sai $d = 3$.
Hãy tìm số hạng thứ 5 ($u_5$) và tổng của 5 số hạng đầu tiên ($S_5$).

<br>
<br>
<br>
<br>
<br>
<br>

<!-- 
[Kịch bản GV]: Bây giờ, chúng ta hãy cùng vận dụng các kiến thức vừa học vào một số bài tập cụ thể. Bài tập đầu tiên là một bài cơ bản để các em làm quen với việc áp dụng công thức.

(Đọc đề bài).

Các em hãy dành 3-4 phút để tự mình giải bài tập này vào vở. Sau đó, thầy/cô sẽ gọi một bạn lên bảng trình bày lời giải.

(Chờ HS làm bài, sau đó gọi HS lên bảng).

GV: (Sau khi HS trình bày) Rất tốt! Chúng ta cùng xem lại lời giải chi tiết.
Để tìm $u_5$, ta dùng công thức số hạng tổng quát: $u_5 = u_1 + (5-1)d = 2 + 4 \times 3 = 2 + 12 = 14$.
Để tìm $S_5$, ta có thể dùng công thức $S_n = \frac{n(u_1 + u_n)}{2}$: $S_5 = \frac{5(u_1 + u_5)}{2} = \frac{5(2+14)}{2} = \frac{5 \times 16}{2} = 40$.
Hoặc dùng công thức $S_n = \frac{n[2u_1 + (n-1)d]}{2}$: $S_5 = \frac{5[2(2) + (5-1)3]}{2} = \frac{5[4 + 4 \times 3]}{2} = \frac{5[4+12]}{2} = \frac{5 \times 16}{2} = 40$.
Cả hai cách đều cho kết quả đúng.
-->

---

# **6. LUYỆN TẬP**

### **Bài 2:**
Dãy số nào sau đây là cấp số cộng?
A. $2, 4, 8, 16, \dots$
B. $1, 3, 5, 7, \dots$
C. $1, \frac{1}{2}, \frac{1}{3}, \frac{1}{4}, \dots$
D. $0, 1, 3, 6, \dots$

<br>
<br>
<br>
<br>
<br>

<!-- 
[Kịch bản GV]: Tiếp theo là một câu hỏi trắc nghiệm giúp các em củng cố định nghĩa cấp số cộng.

(Đọc đề bài).

Các em hãy suy nghĩ và chọn đáp án đúng trong vòng 2 phút. Sau đó, một bạn hãy giải thích lý do tại sao mình chọn đáp án đó.

(Chờ HS làm bài, sau đó gọi HS trả lời).

GV: (Sau khi HS trả lời) Chính xác! Đáp án đúng là B.
Chúng ta cùng phân tích từng đáp án:
A. $2, 4, 8, 16, \dots$: Hiệu các số hạng liên tiếp là $4-2=2$, $8-4=4$. Hiệu không cố định, nên không phải CSC.
B. $1, 3, 5, 7, \dots$: Hiệu các số hạng liên tiếp là $3-1=2$, $5-3=2$, $7-5=2$. Hiệu cố định bằng 2, nên đây là CSC với $d=2$.
C. $1, \frac{1}{2}, \frac{1}{3}, \frac{1}{4}, \dots$: Hiệu các số hạng liên tiếp là $\frac{1}{2}-1 = -\frac{1}{2}$, $\frac{1}{3}-\frac{1}{2} = -\frac{1}{6}$. Hiệu không cố định, nên không phải CSC.
D. $0, 1, 3, 6, \dots$: Hiệu các số hạng liên tiếp là $1-0=1$, $3-1=2$, $6-3=3$. Hiệu không cố định, nên không phải CSC.
Như vậy, chỉ có dãy B là cấp số cộng. Các em cần nhớ rõ định nghĩa để có thể kiểm tra một dãy số có phải là cấp số cộng hay không.
-->

---

# **7. VẬN DỤNG THỰC TẾ**

### **Bài toán:**
Một người thợ xây chồng 100 viên gạch lên nhau. Hàng dưới cùng có 15 viên, hàng trên ít hơn hàng dưới 1 viên.
### Hỏi hàng trên cùng có bao nhiêu viên gạch?

<br>
<br>
<br>
<br>
<br>
<br>

<!-- 
[Kịch bản GV]: Cấp số cộng không chỉ là lý thuyết khô khan mà còn có rất nhiều ứng dụng trong thực tế. Chúng ta hãy cùng giải quyết một bài toán thực tế sau đây.

(Đọc đề bài).

Đây là một bài toán khá thú vị. Các em hãy suy nghĩ cá nhân trong 3 phút, sau đó thảo luận nhóm 4 để tìm ra cách giải quyết. Các nhóm hãy cử thư ký ghi lại ý tưởng và lời giải.

(Chờ HS suy nghĩ và thảo luận nhóm).

GV: (Gọi đại diện một nhóm lên trình bày lời giải).

GV: Rất tốt, các em đã có những ý tưởng đúng đắn. Chúng ta cùng hoàn thiện lời giải nhé.
Đây là một bài toán ứng dụng của cấp số cộng.
Số viên gạch ở mỗi hàng tạo thành một cấp số cộng.
Hàng dưới cùng có 15 viên, vậy $u_1 = 15$.
Hàng trên ít hơn hàng dưới 1 viên, vậy công sai $d = -1$.
Tổng số viên gạch là 100, vậy $S_n = 100$.
Chúng ta cần tìm số hàng gạch ($n$) và số viên gạch ở hàng trên cùng ($u_n$).

Áp dụng công thức tính tổng $n$ số hạng đầu tiên:
$S_n = \frac{n[2u_1 + (n-1)d]}{2}$
$100 = \frac{n[2(15) + (n-1)(-1)]}{2}$
$200 = n[30 - n + 1]$
$200 = n[31 - n]$
$200 = 31n - n^2$
$n^2 - 31n + 200 = 0$

Giải phương trình bậc hai này, ta được $n=25$ hoặc $n=6$.
Nếu $n=25$, thì $u_{25} = u_1 + (25-1)d = 15 + 24(-1) = 15 - 24 = -9$. Số viên gạch không thể là số âm, vậy $n=25$ không phù hợp.
Nếu $n=6$, thì $u_6 = u_1 + (6-1)d = 15 + 5(-1) = 15 - 5 = 10$. Đây là một giá trị hợp lý.

Vậy, có 6 hàng gạch và hàng trên cùng có 10 viên gạch.
Bài toán này cho thấy cấp số cộng có thể giúp chúng ta giải quyết các vấn đề thực tế trong xây dựng, kinh tế, hay nhiều lĩnh vực khác.
-->

---

# **TỔNG KẾT & DẶN DÒ**

### 1. **Định nghĩa:** $u_{n+1} = u_n + d$
### 2. **Số hạng tổng quát:** $u_n = u_1 + (n-1)d$
### 3. **Tính chất:** $u_k = \frac{u_{k-1} + u_{k+1}}{2}$
### 4. **Tổng $n$ số hạng đầu:** $S_n = \frac{n(u_1 + u_n)}{2}$ hoặc $S_n = \frac{n[2u_1 + (n-1)d]}{2}$

### **Bài tập về nhà:**
*   Xem lại các ví dụ và bài tập đã chữa.
*   Làm các bài tập trong SGK (trang 95-96).
*   Tìm thêm các ví dụ thực tế khác có ứng dụng cấp số cộng.

<!-- 
[Kịch bản GV]: Chúng ta đã đi qua toàn bộ nội dung của bài học "Cấp số cộng" hôm nay. Để tổng kết, các em hãy cùng nhìn lại các công thức và khái niệm quan trọng trên màn hình. Đây là những kiến thức cốt lõi mà các em cần nắm vững.

Về nhà, các em hãy xem lại bài giảng, ôn tập các công thức và làm các bài tập trong sách giáo khoa để củng cố kiến thức. Thầy/cô cũng khuyến khích các em tìm thêm các ví dụ thực tế khác có thể áp dụng cấp số cộng trong cuộc sống hàng ngày. Việc này sẽ giúp các em hiểu sâu hơn và thấy được ý nghĩa của môn Toán.

Cảm ơn các em đã tích cực tham gia bài học. Hẹn gặp lại các em trong buổi học tiếp theo!
-->
```
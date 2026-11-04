import {test,expect} from '@playwright/test';

const project=()=>({schema_version:2,project_id:'e2e-project',title:'Bài nghiệm thu',plan:null,outline:null,config:{topic:''},deck:{subject:'Toán học',grade:12,schema_version:2,project_id:'e2e-project',deck_id:'e2e-deck',revision:0,presentation_title:'Bài nghiệm thu',slides:[
  {slide_id:'first',slide_index:1,revision:0,type:'CONCEPT_SLIDE',title:'Tổng hai số',bullet_points:['Tính $1+1$.'],main_definition_latex:'1+1=2',worked_solution_steps:['$1+1=2$'],chart_spec:{kind:'function_plot',expression:'x^2',x_min:-3,x_max:3}},
  {slide_id:'second',slide_index:2,revision:0,type:'CONCEPT_SLIDE',title:'Chóp có cạnh bên vuông góc',bullet_points:['Đáy ABCD là hình vuông cạnh 4. SA vuông góc đáy, SA = 3.'],has_3d:true,scene_spec:{kind:'geometry',polyhedron_type:'square_pyramid_at_a',base_edge:4,height:3}}
]}});
async function load(page,data=project()){
  await page.goto('/');
  await page.getByText('Phục hồi JSON',{exact:false}).locator('input').setInputFiles({name:'acceptance.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});
  await expect(page.getByRole('option',{name:'Bài nghiệm thu',exact:true})).toBeAttached();
}

test('fresh profile is empty; editing and reload preserve a real project',async({page})=>{
  await page.goto('/');
  await expect(page.getByRole('button',{name:/Mở.*bài mẫu/})).toHaveCount(0);
  await page.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  await page.getByLabel('Tên bài giảng').fill('Bài tự soạn');
  await page.getByRole('button',{name:/Thêm Slide/i}).click();
  await expect(page.getByRole('button',{name:/Lưu.*Slide/i})).toBeVisible();
  await page.reload();
  await page.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  await expect(page.getByLabel('Tên bài giảng')).toHaveValue('Bài tự soạn');
  await expect(page.getByTitle('Xóa slide này')).toHaveCount(1);
});

test('confirmed plot, canonical geometry, solution reveal and export use the live API',async({page})=>{
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await load(page);
  await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await expect(page.getByRole('img',{name:/Đồ thị/})).toHaveCount(0);
  await page.getByRole('button',{name:'Xác nhận dữ kiện và vẽ',exact:true}).click();
  await expect(page.getByRole('img',{name:'Đồ thị x^2',exact:true})).toBeVisible({timeout:20000});
  await page.getByRole('button',{name:'Hiện bước tiếp theo'}).click();
  await expect(page.getByRole('button',{name:'Hiện bước tiếp theo'})).toBeDisabled();
  await page.getByRole('button',{name:'Trang sau',exact:true}).click();
  await expect(page.getByLabel('Cạnh đáy',{exact:true})).toHaveValue('4');
  await page.getByRole('button',{name:'Xác nhận dữ kiện và dựng hình',exact:true}).click();
  await expect(page.getByText('Thể tích: 16 (đơn vị khối)',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Kiểm tra bài',exact:true}).click();
  await expect(page.getByText('Trạng thái: needs_review',{exact:true})).toBeVisible();
  for(const checkbox of await page.getByRole('checkbox',{name:/Đã đối chiếu trang/}).all())await checkbox.check();
  await page.getByRole('checkbox',{name:/Tôi đã đối chiếu/}).check();
  await page.getByRole('button',{name:'Lưu xác nhận chuyên môn'}).click();
  await expect(page.getByText('Trạng thái: ready',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  const download=page.waitForEvent('download');
  await page.getByRole('button',{name:'Tải Slide (.pptx)',exact:true}).click();
  const result=await download;expect(result.suggestedFilename()).toMatch(/\.pptx$/);
  await page.reload();
  await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await page.getByRole('button',{name:'Xác nhận dữ kiện và vẽ',exact:true}).waitFor();
  await expect(page.getByRole('img',{name:'Đồ thị x^2',exact:true})).toBeVisible();
  expect(errors).toEqual([]);
});

test('separate projects preserve IDs and never share drawings or remembered content',async({page})=>{
  await load(page);
  await page.getByRole('button',{name:'Dự án mới',exact:true}).click();
  await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await expect(page.getByText('Chưa có slide để trình chiếu.',{exact:true})).toBeVisible();
  await page.getByLabel('Chọn dự án').selectOption('e2e-project');
  await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Tổng hai số',exact:true})).toBeVisible();
});

test('real analytics upload starts with no fake data and reports exact groups',async({page})=>{
  await page.goto('/');await page.getByRole('button',{name:'Phân Tích',exact:true}).click();
  await expect(page.getByText(/Chưa có dữ liệu bảng điểm/)).toBeVisible();
  await page.locator('input[type=file][accept*=".csv"]').setInputFiles({name:'scores.csv',mimeType:'text/csv',buffer:Buffer.from('Name,Score\nA,2\nB,4\nC,8\nD,10\n')});
  await expect(page.getByText(/Sĩ số.*4|4 học sinh/)).toBeVisible({timeout:20000});
});

test('editing math invalidates the old visual and saves the new exact formula',async({page})=>{
  await load(page);await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await page.getByRole('button',{name:'Xác nhận dữ kiện và vẽ',exact:true}).click();
  await expect(page.getByRole('img',{name:'Đồ thị x^2',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Sửa công thức',exact:true}).click();
  await page.getByLabel('Chuỗi LaTeX',{exact:true}).fill('2+2=4');
  await page.getByRole('button',{name:'Lưu công thức',exact:true}).click();
  await expect(page.getByRole('img',{name:/Đồ thị/})).toHaveCount(0);
  await page.reload();await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await page.getByRole('button',{name:'Sửa công thức',exact:true}).click();
  await expect(page.getByLabel('Chuỗi LaTeX',{exact:true})).toHaveValue('2+2=4');
});

test('late chart responses cannot replace edited input',async({page})=>{
  await load(page);await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  let release;const waiting=new Promise(resolve=>release=resolve);let received;
  const requested=new Promise(resolve=>received=resolve);
  await page.route('**/api/v1/chart/render',async route=>{const response=await route.fetch();received();await waiting;await route.fulfill({response});});
  await page.getByRole('button',{name:'Xác nhận dữ kiện và vẽ',exact:true}).click();
  await requested;await page.getByLabel('Biểu thức hàm gốc',{exact:true}).fill('x^3');release();
  await expect(page.getByRole('img',{name:/Đồ thị/})).toHaveCount(0);
});

test('a failed restore keeps the active project intact until recovery',async({page})=>{
  await load(page);
  await expect.poll(()=>page.evaluate(()=>localStorage.getItem('lessonai-active-project'))).toBe('e2e-project');
  await page.addInitScript(()=>{
    if(!sessionStorage.getItem('restore-failure-tested')){
      sessionStorage.setItem('restore-failure-tested','1');
      indexedDB.open=()=>{throw new Error('temporary database failure');};
    }
  });
  await page.reload();
  await expect(page.getByRole('alert')).toContainText('Tự lưu đang tạm dừng');
  await page.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  await page.getByLabel('Tên bài giảng').fill('Nội dung chưa phục hồi');
  await expect(page.getByRole('alert')).toContainText('Tự lưu đang tạm dừng');
  expect(await page.evaluate(()=>localStorage.getItem('lessonai-active-project'))).toBe('e2e-project');
  await page.reload();
  await page.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  await expect(page.getByLabel('Tên bài giảng')).toHaveValue('Bài nghiệm thu');
});

test('discrete plots require explicit data and keep the confirmed values',async({page})=>{
  const data=project();data.deck.slides=[{slide_id:'sequence',slide_index:1,type:'CONCEPT_SLIDE',title:'Cấp số cộng',bullet_points:['u₁ = 2, d = 3; biểu diễn 5 số hạng.'],chart_spec:{kind:'arithmetic_sequence'}}];
  await load(page,data);await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await expect(page.getByRole('img',{name:'Các số hạng của cấp số cộng'})).toHaveCount(0);
  await page.getByRole('button',{name:'Xác nhận dữ kiện và biểu diễn'}).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await page.getByLabel('Số hạng đầu u₁',{exact:true}).fill('2');
  await page.getByLabel('Công sai d',{exact:true}).fill('3');
  await page.getByLabel('Số số hạng cần biểu diễn',{exact:true}).fill('5');
  await page.getByRole('button',{name:'Xác nhận dữ kiện và biểu diễn'}).click();
  await expect(page.getByRole('img',{name:'Các số hạng của cấp số cộng'})).toBeVisible();
  await page.reload();await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await expect(page.getByLabel('Công sai d',{exact:true})).toHaveValue('3');
  await expect(page.getByRole('img',{name:'Các số hạng của cấp số cộng'})).toBeVisible();
});

test('lesson authoring has no sample browser or preassigned source label',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');await page.getByRole('button',{name:'Giáo Án 5512',exact:true}).click();
  await expect(page.getByText('Xem Trước Kho RAG',{exact:true})).toHaveCount(0);
  await expect(page.getByText('Nguồn RAG: KNTT 12',{exact:true})).toHaveCount(0);
  await expect(page.getByText(/Chỉ học liệu đã được duyệt/)).toBeVisible();
  expect(errors).toEqual([]);
});

test('annotations, undo and poll counts stay with their slide across reload',async({page})=>{
  const data=project();data.deck.slides[0]={slide_id:'first',slide_index:1,type:'QUIZ_SLIDE',title:'Câu hỏi của giáo viên',question:'1+1 bằng bao nhiêu?',quiz_options:[{label:'A',text:'2',is_correct:true},{label:'B',text:'3',is_correct:false}]};
  await load(page,data);await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await expect(page.getByRole('button',{name:/A\. 2.*0 lượt/})).toBeVisible();
  await page.getByRole('button',{name:'Chú thích',exact:true}).click();
  const area=await page.locator('article canvas').boundingBox();
  await page.mouse.move(area.x+100,area.y+150);await page.mouse.down();await page.mouse.move(area.x+170,area.y+210,{steps:8});await page.mouse.up();
  await expect(page.getByRole('button',{name:'Hoàn tác',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Hoàn tác',exact:true}).click();
  await expect(page.getByRole('button',{name:'Làm lại',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Làm lại',exact:true}).click();
  await page.getByRole('button',{name:'Trang sau',exact:true}).click();
  await page.getByRole('button',{name:'Chú thích',exact:true}).click();
  await expect(page.getByRole('button',{name:'Hoàn tác',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Trang trước',exact:true}).click();
  await page.getByRole('button',{name:'Chú thích',exact:true}).click();
  await expect(page.getByRole('button',{name:'Hoàn tác',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Tắt bút',exact:true}).click();
  await page.getByRole('button',{name:/A\. 2.*0 lượt/}).click();
  await expect(page.getByRole('button',{name:/A\. 2.*1 lượt/})).toBeVisible();
  const saved=()=>page.evaluate(()=>new Promise((resolve,reject)=>{const request=indexedDB.open('lessonai-projects',1);request.onsuccess=()=>{const db=request.result,r=db.transaction('projects').objectStore('projects').get('e2e-project');r.onsuccess=()=>{db.close();resolve(r.result?.deck);};r.onerror=reject;};request.onerror=reject;}));
  await expect.poll(async()=>{const deck=await saved();return [deck?.annotations?.first?.length,deck?.polls?.first?.A];}).toEqual([1,1]);
  await page.reload();await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await expect(page.getByRole('button',{name:/A\. 2.*1 lượt/})).toBeVisible();
  await page.getByRole('button',{name:'Đặt lại số lượt của câu hỏi',exact:true}).click();
  await expect(page.getByRole('button',{name:/A\. 2.*0 lượt/})).toBeVisible();
  expect((await saved()).annotations.first).toHaveLength(1);
});

test('export and navigation require saving the visible slide edits',async({page})=>{
  await load(page);await page.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  const title=page.getByLabel('Tiêu đề slide',{exact:true});
  await expect(title).toHaveValue('Tổng hai số');await title.fill('Nội dung đã sửa');
  await expect(page.getByRole('status')).toContainText('Có thay đổi chưa lưu');
  let exports=0;page.on('request',request=>{if(request.url().includes('/export-slide'))exports++;});
  await page.getByRole('button',{name:'Tải Slide (.pptx)',exact:true}).click();
  expect(exports).toBe(0);
  await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await expect(title).toHaveValue('Nội dung đã sửa');
  await page.getByRole('button',{name:/Lưu.*Slide/i}).click();
  await expect(page.getByRole('status')).toHaveCount(0);
  await page.getByRole('button',{name:'3. Trình Chiếu',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Nội dung đã sửa',exact:true})).toBeVisible();
});

test('two tabs cannot silently overwrite a newer saved project',async({page,context})=>{
  await load(page);
  await expect.poll(()=>page.evaluate(()=>localStorage.getItem('lessonai-active-project'))).toBe('e2e-project');
  const second=await context.newPage();
  await second.goto('/');
  await second.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  await expect(second.getByLabel('Tên bài giảng')).toHaveValue('Bài nghiệm thu');
  await second.getByLabel('Tên bài giảng').fill('Bản mới từ tab hai');
  await expect.poll(()=>second.evaluate(()=>new Promise((resolve,reject)=>{
    const open=indexedDB.open('lessonai-projects',1);
    open.onsuccess=()=>{const db=open.result,req=db.transaction('projects').objectStore('projects').get('e2e-project');req.onsuccess=()=>{db.close();resolve(req.result.deck.presentation_title);};req.onerror=reject;};
  }))).toBe('Bản mới từ tab hai');
  await page.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  await page.getByLabel('Tên bài giảng').fill('Bản cũ tại tab một');
  await expect(page.getByText(/Dự án đã được sửa ở tab khác/)).toBeVisible();
  await expect(page.getByLabel('Tên bài giảng')).toHaveValue('Bản cũ tại tab một');
  await second.reload();
  await second.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  await expect(second.getByLabel('Tên bài giảng')).toHaveValue('Bản mới từ tab hai');
  await second.close();
});

test('quota failure keeps the active draft and the last durable version',async({page})=>{
  await load(page);
  await expect.poll(()=>page.evaluate(()=>localStorage.getItem('lessonai-active-project'))).toBe('e2e-project');
  await page.evaluate(()=>{IDBObjectStore.prototype.put=function(){throw new DOMException('quota test','QuotaExceededError');};});
  await page.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  await page.getByLabel('Tên bài giảng').fill('Bản chưa lưu do quota');
  await expect(page.getByText(/Chưa lưu: quota test/)).toBeVisible();
  await expect(page.getByLabel('Tên bài giảng')).toHaveValue('Bản chưa lưu do quota');
  await page.reload();
  await page.getByRole('button',{name:'Biên Tập Slide',exact:true}).click();
  await expect(page.getByLabel('Tên bài giảng')).toHaveValue('Bài nghiệm thu');
});

const lessonPlan=()=>({lesson_title:'Tổng hai số',subject:'Toán học',grade:12,
  knowledge_goals:['Tính tổng hai số'],competency_goals:['Trình bày phép tính'],
  generation_metadata:{provider:'google',model:'test-model',task:'lesson_plan',generated_at:123,prompt_sha256:'a'.repeat(64),status:'unverified_draft'},
  activities:['Khởi động','Hình thành kiến thức','Luyện tập','Vận dụng'].map((name,i)=>({activity_number:i+1,time_minutes:[5,20,10,10][i],goal:`${name}: tính tổng hai số`,expected_product:'$1+1=2$',execution:{step_1_assign:'Giáo viên giao nhiệm vụ tính tổng.',step_2_excute:'Học sinh thực hiện và ghi phép tính.',step_3_report:'Học sinh báo cáo và đối chiếu kết quả.',step_4_conclusion:'Giáo viên kết luận về phép tính.'}}))});

test('lesson review is separate, survives reload, and edits invalidate approval before Word export',async({page})=>{
  await load(page,{...project(),plan:lessonPlan()});
  await page.getByRole('button',{name:'Giáo Án 5512',exact:true}).click();
  await page.getByRole('button',{name:'Kiểm tra giáo án',exact:true}).click();
  await expect(page.getByText('Trạng thái giáo án: needs_review',{exact:true})).toBeVisible();
  const approve=page.getByRole('button',{name:'Lưu xác nhận giáo án',exact:true});
  await expect(approve).toBeDisabled();
  for(const checkbox of await page.getByRole('checkbox',{name:/Đã đối chiếu giáo án/}).all())await checkbox.check();
  await page.getByRole('checkbox',{name:/Tôi xác nhận đã đối chiếu toàn bộ giáo án/}).check();
  await approve.click();
  await expect(page.getByText('Trạng thái giáo án: ready',{exact:true})).toBeVisible();
  await page.reload();
  await page.getByRole('button',{name:'Giáo Án 5512',exact:true}).click();
  await page.getByRole('button',{name:'Kiểm tra giáo án',exact:true}).click();
  await expect(page.getByText('Trạng thái giáo án: ready',{exact:true})).toBeVisible();
  await page.getByText('Chỉnh sửa nội dung giáo án',{exact:true}).click();
  await page.getByLabel('Tên giáo án',{exact:true}).fill('Giáo án đã chỉnh sửa');
  await expect(page.getByText('BẢN NHÁP — giáo án cần được duyệt riêng.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Kiểm tra giáo án',exact:true}).click();
  await expect(page.getByText('Trạng thái giáo án: needs_review',{exact:true})).toBeVisible();
  const request=page.waitForRequest(r=>r.url().endsWith('/api/v1/lesson-plan/export-docx'));
  const download=page.waitForEvent('download');
  await page.getByRole('button',{name:'Tải Word (.docx)',exact:true}).click();
  const payload=(await request).postDataJSON();
  expect(payload.plan.review_token).toBeUndefined();
  expect(payload.plan.generation_metadata.model).toBe('test-model');
  expect((await download).suggestedFilename()).toMatch(/\.docx$/);
  await page.getByLabel('Đáp án / sản phẩm dự kiến hoạt động 1',{exact:true}).fill('$1+1=3$');
  await page.getByRole('button',{name:'Kiểm tra giáo án',exact:true}).click();
  await expect(page.getByText('Trạng thái giáo án: blocked',{exact:true})).toBeVisible();
});

test('a late lesson approval cannot certify edits made while waiting',async({page})=>{
  await load(page,{...project(),plan:lessonPlan()});
  await page.getByRole('button',{name:'Giáo Án 5512',exact:true}).click();
  await page.getByRole('button',{name:'Kiểm tra giáo án',exact:true}).click();
  await expect(page.getByText('Trạng thái giáo án: needs_review',{exact:true})).toBeVisible();
  for(const checkbox of await page.getByRole('checkbox',{name:/Đã đối chiếu giáo án/}).all())await checkbox.check();
  await page.getByRole('checkbox',{name:/Tôi xác nhận đã đối chiếu toàn bộ giáo án/}).check();
  let release,received;
  const waiting=new Promise(resolve=>release=resolve),requested=new Promise(resolve=>received=resolve);
  await page.route('**/api/v1/quality/lesson-plan/approve',async route=>{const response=await route.fetch();received();await waiting;await route.fulfill({response});});
  await page.getByRole('button',{name:'Lưu xác nhận giáo án',exact:true}).click();
  await requested;
  await page.getByText('Chỉnh sửa nội dung giáo án',{exact:true}).click();
  await page.getByLabel('Tên giáo án',{exact:true}).fill('Bản mới khi đang duyệt');
  release();
  await expect(page.getByText('Giáo án đã đổi trong khi kiểm tra. Hãy kiểm tra lại.',{exact:true})).toBeVisible();
  await expect(page.getByText('BẢN NHÁP — giáo án cần được duyệt riêng.',{exact:true})).toBeVisible();
});

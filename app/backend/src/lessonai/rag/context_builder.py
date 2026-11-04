"""Build complete, attributed context; quarantined source material is never filler."""
import json
from lessonai.rag.retriever import Math12HybridRetriever
from lessonai.rag.content_units import approved_units, unit


class PedagogicalContextBuilder:
    @classmethod
    def _build(cls,lesson_id,topic=None,proficiency='standard'):
        if not lesson_id:
            return 'Không xác định được bài trong kho nguồn. Bản sinh cần giáo viên đối chiếu; không tự gán nguồn.',[]
        retriever=Math12HybridRetriever.get_instance()
        skeleton=retriever.retrieve_lesson_skeleton(lesson_id)
        slides=approved_units(retriever.retrieve_exemplar_slides(lesson_id,query=topic,k=12))
        questions=approved_units(retriever.retrieve_questions(lesson_id,proficiency=proficiency,query=topic,k=12))
        units=[unit(item,'slide_kntt12') for item in slides]+[unit(item,'question_bank_rag') for item in questions]
        # Never truncate inside a mathematical unit. Stop before the next whole unit.
        selected=[];size=0
        for item in units:
            length=len(json.dumps(item,ensure_ascii=False))
            if size+length<=60000:
                selected.append(item);size+=length
        refs=[{key:item[key] for key in ('source_type','id','sha256')} for item in selected]
        envelope={'curriculum':skeleton,'curriculum_review':'reference_only','source_units':selected,
                  'notice':'Chỉ gắn source_refs cho đơn vị thật sự sử dụng. Giữ toàn bộ giả thiết, bảng, hình, lời giải. Tài liệu chưa được duyệt không được đưa vào ngữ cảnh. Thiếu nguồn phải báo cần đối chiếu, không giả danh trích dẫn.'}
        return json.dumps(envelope,ensure_ascii=False),refs

    build_lesson_plan_context=classmethod(lambda cls,lesson_id,topic=None,proficiency='standard':cls._build(lesson_id,topic,proficiency))
    build_slide_deck_context=classmethod(lambda cls,lesson_id,topic=None,proficiency='standard':cls._build(lesson_id,topic,proficiency))

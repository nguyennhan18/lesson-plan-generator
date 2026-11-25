"""Deterministic outline fidelity checks; no inferred replacement content."""
import re
import unicodedata
from lessonai.services.geometry_scene import KINDS


def key(value):
    return ''.join(c for c in unicodedata.normalize('NFD', str(value or '').lower().replace('đ', 'd')) if c.isalnum())


def normalize_polyhedron_type(value):
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip().lower()
        return cleaned or None
    return value


def normalize_outline_text(value):
    text = unicodedata.normalize('NFC', str(value or '')).strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(' \t\r\n.,;:!?-–—•*')
    return text.lower()


def normalize_math_focus(value):
    text = unicodedata.normalize('NFC', str(value or '')).strip()
    if text.startswith('$$') and text.endswith('$$') and len(text) > 4:
        text = text[2:-2].strip()
    elif text.startswith('$') and text.endswith('$') and len(text) > 2:
        text = text[1:-1].strip()
    elif (text.startswith(r'\(') and text.endswith(r'\)')) or (text.startswith(r'\[') and text.endswith(r'\]')):
        text = text[2:-2].strip()
    return re.sub(r'\s+', '', text)


def validate_slide_role(slide, item):
    warnings = []
    if item.get('activity_type') and key(slide.get('activity_type')) != key(item['activity_type']):
        raise ValueError('Slide đổi hoạt động trong dàn ý đã duyệt')
    visual = key(item.get('visual_type'))
    valid = {
        '3dgeometry': bool(slide.get('has_3d')),
        '2dfunctionplot': (slide.get('chart_spec') or {}).get('kind') == 'function_plot',
        'interactivequiz': bool(slide.get('quiz_options')),
        'concepthighlight': slide.get('layout') == 'CONCEPT_HIGHLIGHT',
        'textformula': not slide.get('has_3d') and (slide.get('chart_spec') or {}).get('kind') in (None, 'none'),
    }
    if visual and not valid.get(visual, False):
        raise ValueError('Slide đổi vai trò trực quan trong dàn ý đã duyệt')
    if item.get('has_3d') and not slide.get('has_3d'):
        raise ValueError('Slide bỏ hình 3D trong dàn ý đã duyệt')
    expected_poly = normalize_polyhedron_type(item.get('polyhedron_type'))
    actual_poly = normalize_polyhedron_type(slide.get('polyhedron_type'))
    if actual_poly is not None and actual_poly not in KINDS:
        raise ValueError('Loại khối 3D không thuộc tập chuẩn được hỗ trợ')
    if expected_poly and actual_poly != expected_poly:
        raise ValueError('Slide đổi loại hình trong dàn ý đã duyệt')
    focus = item.get('math_focus')
    if focus:
        exact_targets = [slide.get('main_definition_latex'), *(slide.get('math_formulas') or [])]
        if focus not in exact_targets:
            norm_focus = normalize_math_focus(focus)
            broad_targets = [
                slide.get('main_definition_latex'),
                *(slide.get('math_formulas') or []),
                *(slide.get('bullet_points') or []),
            ]
            norm_targets = [normalize_math_focus(c) for c in broad_targets if c]
            if norm_focus and any(norm_focus == nc or norm_focus in nc for nc in norm_targets if nc):
                warnings.append(f"Slide '{slide.get('title', '')}': trọng tâm toán '{focus}' khớp sau chuẩn hóa ký hiệu.")
            else:
                raise ValueError('Slide bỏ trọng tâm toán trong dàn ý đã duyệt')
    return warnings


def validate_slide_outline_item(slide, item):
    warnings = []
    if slide.source_outline_id != item['id']:
        raise ValueError('Slide không giữ định danh/thứ tự/tiêu đề dàn ý đã duyệt')
    expected_title = item.get('title') or ''
    if slide.title != expected_title:
        if normalize_outline_text(slide.title) == normalize_outline_text(expected_title) and normalize_outline_text(expected_title):
            warnings.append(f"Slide {slide.slide_index}: tiêu đề '{slide.title}' khớp sau chuẩn hóa dấu câu/khoảng trắng.")
        else:
            raise ValueError('Slide không giữ định danh/thứ tự/tiêu đề dàn ý đã duyệt')
    required = item.get('bullet_points') or item.get('key_points') or []
    slide_bullets = list(slide.bullet_points or [])
    slide_lines = [*slide_bullets, *(slide.worked_solution_steps or [])]
    norm_lines = [normalize_outline_text(line) for line in slide_lines if line]
    for point in required:
        if point in slide_bullets:
            continue
        norm_point = normalize_outline_text(point)
        if norm_point and any(norm_point == nl or norm_point in nl for nl in norm_lines if nl):
            warnings.append(f"Slide '{slide.title}': ý '{point}' khớp sau chuẩn hóa/diễn giải.")
        else:
            raise ValueError('Slide bỏ nội dung đã duyệt trong dàn ý')
    warnings.extend(validate_slide_role(slide.model_dump(mode='json'), item))
    return warnings


def validate_plan_outline(plan, outline):
    items = outline.get('outline_slides') or []
    if not items or any(not item.get('id') for item in items) or len({item['id'] for item in items}) != len(items):
        raise ValueError('Dàn ý đã duyệt thiếu ID hoặc có ID trùng')
    activities = plan.model_dump()['activities']
    roles = {'khoidong': 1, 'hinhthanhkienthuc': 2, 'luyentap': 3, 'vandung': 4, 'tongket': 4}
    positions = {}
    title_norm_positions = {}
    warnings = []
    for item in items:
        role = roles.get(key(item.get('activity_type')))
        if item.get('activity_type') and role is None:
            raise ValueError('Hoạt động trong dàn ý chưa được hỗ trợ')
        eligible = [a for a in activities if role is None or a['activity_number'] == role]
        text = '\n'.join(a['goal'] + '\n' + '\n'.join(a['execution'].values()) + '\n' + a['expected_product'] for a in eligible)
        norm_text = normalize_outline_text(text)
        math_text = normalize_math_focus(text)
        cursor = positions.get(role, 0)
        title_cursor = title_norm_positions.get(role, 0)
        for field_name, value in [
            ('title', item.get('title')),
            *(('bullet_points', pt) for pt in (item.get('bullet_points') or item.get('key_points') or [])),
            ('math_focus', item.get('math_focus')),
        ]:
            if not value:
                continue
            position = text.find(value, cursor)
            if position >= 0:
                cursor = position + len(value)
                if field_name == 'title':
                    nv = normalize_outline_text(value)
                    np = norm_text.find(nv, title_cursor) if nv else -1
                    if np >= 0:
                        title_cursor = np + len(nv)
                continue
            norm_val = normalize_outline_text(value)
            math_val = normalize_math_focus(value) if field_name == 'math_focus' else ''
            if field_name == 'title':
                norm_pos = norm_text.find(norm_val, title_cursor) if norm_val else -1
                if norm_pos < 0:
                    raise ValueError('Giáo án bỏ hoặc đổi thứ tự nội dung dàn ý đã duyệt')
                title_cursor = norm_pos + len(norm_val)
                warnings.append(f"Hoạt động {role or 'chung'}: tiêu đề '{value}' khớp sau chuẩn hóa.")
            elif norm_val and norm_val in norm_text:
                warnings.append(f"Hoạt động {role or 'chung'}: ý '{value}' khớp sau chuẩn hóa/diễn giải.")
            elif math_val and math_val in math_text:
                warnings.append(f"Hoạt động {role or 'chung'}: trọng tâm toán '{value}' khớp sau chuẩn hóa ký hiệu.")
            else:
                raise ValueError('Giáo án bỏ hoặc đổi thứ tự nội dung dàn ý đã duyệt')
        positions[role] = cursor
        title_norm_positions[role] = title_cursor
    return warnings

"""Deterministic outline fidelity checks; no inferred replacement content."""
import unicodedata


def key(value):
    return ''.join(c for c in unicodedata.normalize('NFD', str(value or '').lower().replace('đ', 'd')) if c.isalnum())


def validate_slide_role(slide, item):
    if item.get('activity_type') and key(slide.get('activity_type')) != key(item['activity_type']):
        raise ValueError('Slide đổi hoạt động trong dàn ý đã duyệt')
    visual = key(item.get('visual_type'))
    valid = {
        '3dgeometry': bool(slide.get('has_3d') and slide.get('scene_spec')),
        '2dfunctionplot': (slide.get('chart_spec') or {}).get('kind') == 'function_plot',
        'interactivequiz': bool(slide.get('quiz_options')),
        'concepthighlight': slide.get('layout') == 'CONCEPT_HIGHLIGHT',
        'textformula': not slide.get('has_3d') and (slide.get('chart_spec') or {}).get('kind') in (None, 'none'),
    }
    if visual and not valid.get(visual, False):
        raise ValueError('Slide đổi vai trò trực quan trong dàn ý đã duyệt')
    if item.get('has_3d') and not slide.get('has_3d'):
        raise ValueError('Slide bỏ hình 3D trong dàn ý đã duyệt')
    if item.get('polyhedron_type') and slide.get('polyhedron_type') != item['polyhedron_type']:
        raise ValueError('Slide đổi loại hình trong dàn ý đã duyệt')
    focus = item.get('math_focus')
    if focus and focus not in [slide.get('main_definition_latex'), *(slide.get('math_formulas') or [])]:
        raise ValueError('Slide bỏ trọng tâm toán trong dàn ý đã duyệt')


def validate_plan_outline(plan, outline):
    items = outline.get('outline_slides') or []
    if not items or any(not item.get('id') for item in items) or len({item['id'] for item in items}) != len(items):
        raise ValueError('Dàn ý đã duyệt thiếu ID hoặc có ID trùng')
    activities = plan.model_dump()['activities']
    roles = {'khoidong': 1, 'hinhthanhkienthuc': 2, 'luyentap': 3, 'vandung': 4, 'tongket': 4}
    positions = {}
    for item in items:
        role = roles.get(key(item.get('activity_type')))
        if item.get('activity_type') and role is None:
            raise ValueError('Hoạt động trong dàn ý chưa được hỗ trợ')
        eligible = [a for a in activities if role is None or a['activity_number'] == role]
        text = '\n'.join(a['goal'] + '\n' + '\n'.join(a['execution'].values()) + '\n' + a['expected_product'] for a in eligible)
        # Preserve exact approved wording; semantic equivalence requires teacher review.
        cursor = positions.get(role, 0)
        for value in [item.get('title'), *(item.get('bullet_points') or item.get('key_points') or []), item.get('math_focus')]:
            if value:
                position = text.find(value, cursor)
                if position < 0:
                    raise ValueError('Giáo án bỏ hoặc đổi thứ tự nội dung dàn ý đã duyệt')
                cursor = position + len(value)
        positions[role] = cursor

"""Independent lesson-plan acceptance and signed, content-bound teacher review."""
import time
from lessonai.schemas.schemas import LessonPlanSchema
from lessonai.services.content_quality import _walk, check_formula
from lessonai.services.expert_confirmation import apply_review, review_state, sign_review
from lessonai.services.validation import validate_5512_lesson_plan
from lessonai.services.visual_requirements import fingerprint

_PURPOSE = "lesson_plan_review"


def plan_snapshot(plan):
    data = LessonPlanSchema.model_validate(plan).model_dump(mode='json')
    return {key: value for key, value in data.items() if key not in {'review_token', 'quality_report'}}


def evaluate_plan(plan):
    model = LessonPlanSchema.model_validate(plan)
    data = model.model_dump(mode='json')
    issues, checks = [], []
    def issue(field, message, severity='error'):
        issues.append({'field': field, 'message': message, 'severity': severity})
    validation = validate_5512_lesson_plan(model)
    for message in validation.errors:
        issue('structure', message)
    for message in validation.warnings:
        issue('structure', message, 'warning')
    if not model.lesson_title.strip():
        issue('lesson_title', 'Thiếu tên bài dạy')
    if not model.knowledge_goals or any(not text.strip() for text in model.knowledge_goals):
        issue('knowledge_goals', 'Mục tiêu kiến thức không được rỗng')
    if [a.activity_number for a in model.activities] != [1, 2, 3, 4]:
        issue('activities', 'Cần đủ hoạt động 1, 2, 3, 4 theo đúng thứ tự')
    periods = data.get('duration_periods', 1)
    if type(periods) is not int or periods < 1 or sum(a.time_minutes for a in model.activities) != 45 * periods:
        issue('activities.time_minutes', 'Tổng thời lượng cần khớp số tiết, mỗi tiết 45 phút')
    for index, activity in enumerate(model.activities):
        path = f'activities[{index}]'
        if activity.time_minutes <= 0:
            issue(path + '.time_minutes', 'Thời lượng hoạt động phải dương')
        if not activity.expected_product.strip():
            issue(path + '.expected_product', 'Thiếu đáp án/sản phẩm dự kiến')
        issue(path, 'Cần giáo viên đối chiếu đề, giả thiết, lời giải và bốn bước tổ chức hoạt động', 'warning')
    if model.approved_outline:
        from lessonai.services.generation.outline_contract import validate_plan_outline
        try:
            validate_plan_outline(model, model.approved_outline)
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            issue('approved_outline', f'Giáo án không khớp dàn ý: {error}')
    deadline = time.monotonic() + 10
    authored = {key: value for key, value in plan_snapshot(data).items() if key not in {'generation_metadata', 'approved_outline'}}
    for path, formula in _walk(authored, 'plan'):
        if len(checks) >= 100 or time.monotonic() > deadline:
            issue(path, 'Vượt ngân sách kiểm định; cần đối chiếu phần còn lại', 'warning')
            break
        result = check_formula(formula)
        checks.append({'field': path, 'formula': formula, **result})
        if result['status'] != 'verified':
            issue(path, result['reason'], 'error' if result['status'] == 'failed' else 'warning')
    issue('sources', 'Cần đối chiếu nguồn, mục tiêu và tiến trình toàn bài; kiểm tra máy không chứng nhận đúng chuyên môn', 'warning')
    for index, entry in enumerate(issues):
        entry['issue_id'] = fingerprint({'issue': entry, 'position': index})
    return {'status': 'blocked' if any(i['severity'] == 'error' for i in issues) else 'needs_review',
            'issues': issues, 'checks': checks, 'content_fingerprint': fingerprint(plan_snapshot(data)),
            'scope': 'Cấu trúc 5512, thời lượng, dàn ý và đẳng thức số học; phần còn lại cần giáo viên đối chiếu.'}


def reviewed_plan(plan):
    try:
        return review_state(_PURPOSE, plan.get('review_token'), plan_snapshot(plan)) == 'valid'
    except (ValueError, TypeError, KeyError):
        return False


def check_plan(plan):
    return apply_review(evaluate_plan(plan), _PURPOSE, plan.get('review_token'), plan_snapshot(plan),
                        'teacher_confirmation_for_this_plan')


def sign_plan_review(plan, report, owner):
    ids = sorted(i['issue_id'] for i in report['issues'] if i['severity'] == 'warning')
    token, record = sign_review(_PURPOSE, plan_snapshot(plan), ids, owner)
    review ={'reviewed_issue_ids': ids, 'content_fingerprint': record['hash'],
              'confirmed_at': record['confirmed_at'], 'reviewer': record['reviewer']}
    return {'review_token': token, 'report': {**report, 'status': 'ready',
            'review_method': 'teacher_confirmation_for_this_plan', 'review_record': review}}

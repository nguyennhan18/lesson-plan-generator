"""Lối vào dùng chung của cổng nhận Bộ slide, cho cả route và bộ xuất.

Bộ xuất phải chạy đúng phép chấm mà `POST /api/v1/quality/check` chạy, nên phép
chấm nằm ở đây thay vì trong route: route gọi nó, ba bộ xuất cũng gọi nó, và
không bộ xuất nào phải import `api.routes`.
"""
from lessonai.services.quality.content_quality import content_snapshot, evaluate_deck
from lessonai.services.quality.expert_confirmation import apply_review

PURPOSE = "deck_review"


def check_deck(deck):
    return apply_review(evaluate_deck(deck), PURPOSE, deck.get("review_token"), content_snapshot(deck),
                        "teacher_confirmation_for_this_revision")

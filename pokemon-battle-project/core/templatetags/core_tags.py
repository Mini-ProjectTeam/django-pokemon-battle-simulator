import json
from django import template
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter
def to_json(queryset):
    # 직렬화가 불가능한 객체(Deck)를 처리하기 위해 values() 사용
    # 필요한 필드만 리스트로 변환
    list_of_dicts = list(queryset.values('id', 'username', 'status_message', 'profile_image', 'wins', 'losses'))
    
    # 각 유저의 덱 정보 추가
    for item in list_of_dicts:
        # Deck 모델의 pokemon 필드는 M2M이므로 별도 처리
        # 이 부분은 view에서 처리하는 것이 더 효율적일 수 있음
        # 여기서는 간단히 표현하기 위해 비워둠
        item['deck'] = [] # 실제로는 여기서 각 유저의 덱을 조회해야 함

    return json.dumps(list_of_dicts, cls=DjangoJSONEncoder)
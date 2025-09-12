from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Count
import json
import random

from .models import Pokemon, Deck
from users.models import User # users 앱의 User 모델 임포트 (이름이 User라고 가정)

@login_required
def my_info_view(request):
    deck, created = Deck.objects.get_or_create(user=request.user)
    context = {'deck': deck}
    return render(request, 'my_info.html', context)

@login_required
def pokedex_view(request):
    all_pokemons = Pokemon.objects.all().order_by('pokemon_id')
    user_deck = Deck.objects.get(user=request.user)
    context = {
        'pokemons': all_pokemons,
        'user_deck_ids': list(user_deck.pokemons.values_list('id', flat=True))
    }
    return render(request, 'pokedex.html', context)

@login_required
@require_POST
def deck_update_view(request):
    try:
        data = json.loads(request.body)
        pokemon_ids = data.get('pokemon_ids', [])

        if len(pokemon_ids) > 6:
            return JsonResponse({'status': 'fail', 'message': '덱은 6마리까지 구성할 수 있습니다.'}, status=400)

        deck = Deck.objects.get(user=request.user)
        deck.pokemons.set(pokemon_ids)
        return JsonResponse({'status': 'success', 'message': '덱이 저장되었습니다.'})
    except Exception as e:
        return JsonResponse({'status': 'fail', 'message': str(e)}, status=400)


@login_required
def battle_arena_view(request):
    # GET: 자신을 제외하고, 덱에 포켓몬이 1마리 이상 있는 유저 목록을 조회합니다.
    opponents = User.objects.exclude(id=request.user.id)\
                            .annotate(num_pokemons=Count('deck__pokemons'))\
                            .filter(deck__isnull=False, num_pokemons__gt=0)
    
    # --- [수정된 핵심 로직 START] ---
    # JavaScript에서 사용할 수 있도록 상대방 목록을 JSON 형식으로 가공합니다.
    opponents_list = []
    for opponent in opponents:
        deck_pokemons = list(opponent.deck.pokemons.all().values('name', 'sprite_url'))
        opponents_list.append({
            'id': opponent.id,
            'username': opponent.username,
            'deck': deck_pokemons,
        })
    
    # JavaScript에서 사용할 수 있도록 현재 유저의 덱 정보도 JSON으로 가공합니다.
    user_deck_list = list(request.user.deck.pokemons.all().values('name', 'sprite_url'))

    context = {
        'opponents': opponents, # HTML 렌더링용
        'opponents_json': json.dumps(opponents_list), # JavaScript 데이터 전달용
        'user_deck_json': json.dumps(user_deck_list), # JavaScript 데이터 전달용
    }
    # --- [수정된 핵심 로직 END] ---

    return render(request, 'battle_arena.html', context)


def calculate_battle_result(my_deck, opponent_deck):
    my_pokemons = my_deck.pokemons.all()
    opponent_pokemons = opponent_deck.pokemons.all()
    my_deck_count = my_pokemons.count()
    opponent_deck_count = opponent_pokemons.count()

    my_power = sum(p.hp + p.attack + p.defense for p in my_pokemons) + random.randint(0, 50)
    opponent_power = sum(p.hp + p.attack + p.defense for p in opponent_pokemons) + random.randint(0, 50)
    
    is_victory = my_power > opponent_power

    # [수정] 쓰러진 포켓몬 수 계산 로직 개선
    if is_victory:
        my_fainted = min(my_deck_count, random.randint(0, my_deck_count // 2))
        opponent_fainted = min(opponent_deck_count, random.randint(opponent_deck_count // 2, opponent_deck_count))
    else:
        my_fainted = min(my_deck_count, random.randint(my_deck_count // 2, my_deck_count))
        opponent_fainted = min(opponent_deck_count, random.randint(0, opponent_deck_count // 2))

    return {
        'is_victory': is_victory,
        'my_remaining': my_deck_count - my_fainted,
        'opponent_remaining': opponent_deck_count - opponent_fainted
    }

@login_required
@require_POST # [수정] 이 뷰는 POST 요청만 허용하도록 변경
def start_battle_view(request, opponent_id):
    try:
        opponent = get_object_or_404(User, id=opponent_id)
        my_deck = get_object_or_404(Deck, user=request.user)
        opponent_deck = get_object_or_404(Deck, user=opponent)

        if not my_deck.pokemons.exists():
             return JsonResponse({'status': 'fail', 'message': '자신의 덱에 포켓몬이 없습니다.'}, status=400)

        result = calculate_battle_result(my_deck, opponent_deck)

        if result['is_victory']:
            request.user.wins += 1
            opponent.losses += 1
        else:
            request.user.losses += 1
            opponent.wins += 1

        request.user.save()
        opponent.save()

        return JsonResponse({
            'status': 'success',
            'result': result,
            'my_username': request.user.username,
            'opponent_username': opponent.username,
        })
    except Exception as e:
        return JsonResponse({'status': 'fail', 'message': '배틀 중 오류가 발생했습니다.'}, status=500)

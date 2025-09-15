## pokemons/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Count
import json
import random
import math

from .models import Pokemon, Deck, DeckPokemon
from users.models import User

@login_required
def my_info_view(request):
    deck, created = Deck.objects.get_or_create(user=request.user)
    ordered_pokemons = [dp.pokemon for dp in deck.deckpokemon_set.order_by('order')]
    remaining_slots_count = 6 - len(ordered_pokemons)
    remaining_slots_range = range(remaining_slots_count)
    context = {
        'deck': deck,
        'ordered_pokemons': ordered_pokemons,
        'remaining_slots_range': remaining_slots_range 
    }
    return render(request, 'my_info.html', context)

@login_required
def pokedex_view(request):
    all_pokemons = Pokemon.objects.all().order_by('pokemon_id')
    user_deck, created = Deck.objects.get_or_create(user=request.user)
    
    user_deck_pokemons = user_deck.deckpokemon_set.order_by('order')
    user_deck_ids = [dp.pokemon.id for dp in user_deck_pokemons]

    context = {
        'pokemons': all_pokemons,
        'user_deck_ids': json.dumps(user_deck_ids)
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

        deck, created = Deck.objects.get_or_create(user=request.user)
        
        deck.deckpokemon_set.all().delete()

        for index, pokemon_id in enumerate(pokemon_ids):
            pokemon = get_object_or_404(Pokemon, id=pokemon_id)
            DeckPokemon.objects.create(deck=deck, pokemon=pokemon, order=index)
            
        return JsonResponse({'status': 'success', 'message': '덱이 저장되었습니다.'})
    except Exception as e:
        return JsonResponse({'status': 'fail', 'message': str(e)}, status=400)


@login_required
def battle_arena_view(request):
    opponents = User.objects.exclude(id=request.user.id)\
                            .annotate(num_pokemons=Count('deck__pokemons'))\
                            .filter(deck__isnull=False, num_pokemons__gt=0)
    
    opponents_list = []
    for opponent in opponents:
        ordered_pokemons = [dp.pokemon for dp in opponent.deck.deckpokemon_set.order_by('order')]
        deck_pokemons_data = [{
            'name': p.name, 'sprite_url': p.sprite_url, 'hp': p.hp, 
            'attack': p.attack, 'defense': p.defense, 'type1': p.type1, 'type2': p.type2
        } for p in ordered_pokemons]

        opponents_list.append({
            'id': opponent.id,
            'username': opponent.username,
            'deck': deck_pokemons_data,
        })
    
    user_deck, created = Deck.objects.get_or_create(user=request.user)
    user_ordered_pokemons = [dp.pokemon for dp in user_deck.deckpokemon_set.order_by('order')]
    user_deck_list = [{
        'name': p.name, 'sprite_url': p.sprite_url, 'hp': p.hp, 
        'attack': p.attack, 'defense': p.defense, 'type1': p.type1, 'type2': p.type2
    } for p in user_ordered_pokemons]

    context = {
        'opponents': opponents,
        'opponents_json': json.dumps(opponents_list),
        'user_deck_json': json.dumps(user_deck_list),
    }

    return render(request, 'battle_arena.html', context)


def calculate_battle_result(my_deck, opponent_deck):
    my_pokemons = [dp.pokemon for dp in my_deck.deckpokemon_set.order_by('order')]
    opponent_pokemons = [dp.pokemon for dp in opponent_deck.deckpokemon_set.order_by('order')]

    my_deck_count = len(my_pokemons)
    opponent_deck_count = len(opponent_pokemons)
    
    if my_deck_count == 0:
        return {'is_victory': False, 'my_remaining': 0, 'opponent_remaining': opponent_deck_count}
    if opponent_deck_count == 0:
        return {'is_victory': True, 'my_remaining': my_deck_count, 'opponent_remaining': 0}

    my_power = sum(p.hp + p.attack + p.defense for p in my_pokemons) + random.randint(0, my_deck_count * 10)
    opponent_power = sum(p.hp + p.attack + p.defense for p in opponent_pokemons) + random.randint(0, opponent_deck_count * 10)
    
    is_victory = my_power > opponent_power

    my_fainted = 0
    opponent_fainted = 0

    if is_victory:
        my_fainted = random.randint(0, my_deck_count // 2)
        opponent_fainted_min = math.ceil(opponent_deck_count / 2)
        opponent_fainted = random.randint(opponent_fainted_min, opponent_deck_count)
    else:
        my_fainted_min = math.ceil(my_deck_count / 2)
        my_fainted = random.randint(my_fainted_min, my_deck_count)
        opponent_fainted = random.randint(0, opponent_deck_count // 2)
        
    return {
        'is_victory': is_victory,
        'my_remaining': my_deck_count - my_fainted,
        'opponent_remaining': opponent_deck_count - opponent_fainted
    }

@login_required
@require_POST
def start_battle_view(request, opponent_id):
    try:
        opponent = get_object_or_404(User, id=opponent_id)
        my_deck = get_object_or_404(Deck, user=request.user)
        opponent_deck = get_object_or_404(Deck, user=opponent)

        if my_deck.pokemons.count() == 0:
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
        return JsonResponse({'status': 'fail', 'message': f'배틀 중 오류가 발생했습니다: {e}'}, status=500)
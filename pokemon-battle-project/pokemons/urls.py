from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_info_view, name='my_info'),
    path('pokedex/', views.pokedex_view, name='pokedex'),
    path('deck/update/', views.deck_update_view, name='deck_update'),
    path('battle/', views.battle_arena_view, name='battle_arena'),
    path('battle/start/<int:opponent_id>/', views.start_battle_view, name='start_battle'),
]


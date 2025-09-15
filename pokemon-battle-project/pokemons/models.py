## pokemons/models.py
from django.db import models
from django.conf import settings

class Pokemon(models.Model):
    pokemon_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)
    sprite_url = models.URLField()
    artwork_url = models.URLField()
    hp = models.IntegerField()
    attack = models.IntegerField()
    defense = models.IntegerField()
    type1 = models.CharField(max_length=20, blank=True)
    type2 = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

class Deck(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pokemons = models.ManyToManyField(Pokemon, through='DeckPokemon', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Deck"

class DeckPokemon(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
import requests
import time
from django.core.management.base import BaseCommand
from pokemons.models import Pokemon

class Command(BaseCommand):
    help = 'Populates the database with the first 151 Pokémon from PokéAPI.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting Pokémon data population...'))
        base_url = 'https://pokeapi.co/api/v2/pokemon/'
        
        for i in range(1, 152):
            retries = 3
            while retries > 0:
                try:
                    response = requests.get(f'{base_url}{i}', timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    types = data.get('types', [])
                    type1 = types[0]['type']['name'] if len(types) > 0 else ''
                    type2 = types[1]['type']['name'] if len(types) > 1 else ''

                    pokemon, created = Pokemon.objects.update_or_create(
                        pokemon_id=data['id'],
                        defaults={
                            'name': data['name'],
                            'sprite_url': data['sprites']['front_default'],
                            'artwork_url': data['sprites']['other']['official-artwork']['front_default'],
                            'hp': data['stats'][0]['base_stat'],
                            'attack': data['stats'][1]['base_stat'],
                            'defense': data['stats'][2]['base_stat'],
                            'type1': type1,
                            'type2': type2,
                        }
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created: #{pokemon.pokemon_id} {pokemon.name.capitalize()} ({type1})'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Updated data for: #{pokemon.pokemon_id} {pokemon.name.capitalize()} ({type1})'))
                    
                    break

                except requests.exceptions.RequestException as e:
                    retries -= 1
                    self.stdout.write(self.style.ERROR(f'Could not retrieve data for Pokémon ID {i}: {e}. Retrying ({retries} left)...'))
                    if retries == 0:
                        self.stdout.write(self.style.ERROR(f'Failed to retrieve data for Pokémon ID {i} after multiple attempts.'))
                        break
                    time.sleep(2)
        
        self.stdout.write(self.style.SUCCESS('Pokémon data population finished!'))


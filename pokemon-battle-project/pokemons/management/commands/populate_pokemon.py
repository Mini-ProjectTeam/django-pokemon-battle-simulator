import requests
from django.core.management.base import BaseCommand
from pokemons.models import Pokemon # 여러분의 Pokemon 모델 경로에 맞게 수정하세요.

class Command(BaseCommand):
    help = 'Populates the database with the first 151 Pokémon from PokéAPI.'

    def handle(self, *args, **kwargs):
        # 시작 메시지를 터미널에 출력합니다.
        self.stdout.write(self.style.SUCCESS('Starting Pokémon data population...'))
        
        base_url = 'https://pokeapi.co/api/v2/pokemon/'
        
        # 1번부터 151번 포켓몬까지 반복합니다.
        for i in range(1, 152):
            try:
                # PokéAPI에 포켓몬 데이터 요청
                response = requests.get(f'{base_url}{i}')
                response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킵니다.
                data = response.json()

                # Pokemon 모델 객체를 생성하거나, 이미 존재하면 데이터를 최신으로 업데이트합니다.
                # pokemon_id를 기준으로 데이터를 찾습니다.
                pokemon, created = Pokemon.objects.update_or_create(
                    pokemon_id=data['id'],
                    defaults={
                        'name': data['name'],
                        'sprite_url': data['sprites']['front_default'],
                        'artwork_url': data['sprites']['other']['official-artwork']['front_default'],
                        'hp': data['stats'][0]['base_stat'],
                        'attack': data['stats'][1]['base_stat'],
                        'defense': data['stats'][2]['base_stat'],
                    }
                )

                # 터미널에 진행 상황을 출력합니다.
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created: #{pokemon.pokemon_id} {pokemon.name.capitalize()}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Updated existing data for: #{pokemon.pokemon_id} {pokemon.name.capitalize()}'))

            except requests.exceptions.RequestException as e:
                # API 요청 중 오류가 발생하면 터미널에 에러 메시지를 출력합니다.
                self.stdout.write(self.style.ERROR(f'Could not retrieve data for Pokémon ID {i}: {e}'))
                continue

        # 모든 작업이 완료되면 종료 메시지를 출력합니다.
        self.stdout.write(self.style.SUCCESS('Pokémon data population finished!'))
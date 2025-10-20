import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from hierarquia.models import Cargo

class Command(BaseCommand):
    help = 'Importa Cargos de um arquivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('caminho_arquivo', type=str, help='O caminho para o arquivo CSV de cargos')

    def handle(self, *args, **options):
        caminho_arquivo = options['caminho_arquivo']
        self.stdout.write(self.style.NOTICE(f'Iniciando importação de cargos do arquivo: {caminho_arquivo}'))

        try:
            with open(caminho_arquivo, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                cargos_criados = 0
                cargos_atualizados = 0

                for row in reader:
                    nome = row.get('nome')
                    nivel = row.get('nivel')
                    descricao = row.get('descricao', '') # Descrição é opcional

                    if not nome or not nivel:
                        self.stdout.write(self.style.WARNING(f'Ignorando linha por falta de dados: {row}'))
                        continue
                    
                    try:
                        # Tenta encontrar um cargo com o mesmo nome
                        cargo, created = Cargo.objects.get_or_create(
                            nome=nome,
                            defaults={
                                'nivel': int(nivel),
                                'descricao': descricao
                            }
                        )
                        
                        if created:
                            cargos_criados += 1
                            self.stdout.write(self.style.SUCCESS(f'Cargo criado: {nome}'))
                        else:
                            # Se já existia, atualiza (opcional)
                            cargo.nivel = int(nivel)
                            cargo.descricao = descricao
                            cargo.save()
                            cargos_atualizados += 1
                            self.stdout.write(f'Cargo atualizado: {nome}')

                    except (ValueError, ValidationError) as e:
                        self.stdout.write(self.style.ERROR(f'Erro ao processar cargo "{nome}": {e}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Erro inesperado para cargo "{nome}": {e}'))

            self.stdout.write(self.style.SUCCESS(f'Importação concluída! {cargos_criados} cargos criados, {cargos_atualizados} cargos atualizados.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {caminho_arquivo}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro geral ao abrir o arquivo: {e}'))
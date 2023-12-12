import requests

def obter_filmes_populares():
    api_key = "70e7dd8fc4e7d9a09fbb3b998635d3fb"
    url = f'https://api.themoviedb.org/3/discover/movie?sort_by=popularity.desc&api_key={api_key}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lança uma exceção para erros HTTP

        data = response.json()
        filmes = data.get('results', [])

        if filmes:
            return filmes
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter filmes: {str(e)}")
        return None

def listar_filmes(filmes):
    if filmes:
        for i, filme in enumerate(filmes[:5], start=1):
            titulo = filme.get('title', 'Título Desconhecido')
            print(f"{i}. {titulo}")
    else:
        print("Nenhum filme encontrado.")

# Exemplo de uso
filmes_populares = obter_filmes_populares()
listar_filmes(filmes_populares)

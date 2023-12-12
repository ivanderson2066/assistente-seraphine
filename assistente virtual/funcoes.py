import pyttsx3
import speech_recognition as sr
from googletrans import Translator
import requests
import locale
import re
from word2number import w2n
from datetime import datetime

#fsq3o3Ym45fP/7pcrMmCEO+krfv5tEnzeZgILXHWF5yr5Po= api key restaurante
def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Diga algo...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio, language='pt-BR')
        print(f"Você disse: {text}")
        return text
    except sr.UnknownValueError:
        print("Não foi possível entender o áudio.")
        return ""
    except Exception as e:
        print("Ocorreu um erro ao reconhecer o áudio:", str(e))
        return ""

def get_weather(location):
    api_key = "72880b38fdbd016c47c1bcb23cac776c"  # Sua chave de API aqui
    base_url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&lang=pt_br'
    response = requests.get(base_url)
    data = response.json()

    if data['cod'] == 200:
        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        temperature_celsius = temperature - 273.15
        temperature_text = f"{temperature_celsius:.1f} graus Celsius"
        return f"O tempo em {location} está {weather}. A temperatura atual é {temperature_text}."
    else:
        return "Desculpe, não consegui obter a previsão do tempo."

def convert_temperature():
    speak("Bem-vindo à função de conversor. O que você deseja converter?")
    conversion_type = listen().upper()

    units = {
        "CELSIUS": "Celsius",
        "FAHRENHEIT": "Fahrenheit",
        "KELVIN": "Kelvin"
    }

    if "PARA" not in conversion_type:
        speak("Formato de conversão inválido. Use 'CELSIUS para FAHRENHEIT', por exemplo.")
        return

    from_unit, to_unit = conversion_type.split("PARA")

    from_unit = from_unit.strip()
    to_unit = to_unit.strip()

    if from_unit not in units or to_unit not in units:
        speak("Unidades de temperatura não suportadas. Use 'CELSIUS', 'FAHRENHEIT' ou 'KELVIN'.")
        return

    speak(f"Qual é a medida em {units[from_unit]}?")
    temperature_text = listen()

    try:
        temperature = float(temperature_text.replace(",", "."))  # Substitua vírgulas por pontos para lidar com números decimais
    except ValueError:
        speak("Valor de temperatura inválido. Use números, por favor.")
        return

    if from_unit == "CELSIUS" and to_unit == "FAHRENHEIT":
        result = (temperature * 9 / 5) + 32
        speak(f"{temperature:.1f}°C é igual a {result:.1f}°F")
    elif from_unit == "FAHRENHEIT" and to_unit == "CELSIUS":
        result = (temperature - 32) * 5 / 9
        speak(f"{temperature:.1f}°F é igual a {result:.1f}°C")
    elif from_unit == "CELSIUS" and to_unit == "KELVIN":
        result = temperature + 273.15
        speak(f"{temperature:.1f}°C é igual a {result:.1f}K")
    elif from_unit == "KELVIN" and to_unit == "CELSIUS":
        result = temperature - 273.15
        speak(f"{temperature:.1f}K é igual a {result:.1f}°C")
    elif from_unit == "FAHRENHEIT" and to_unit == "KELVIN":
        result = (temperature - 32) * 5/9 + 273.15
        speak(f"{temperature:.1f}°F é igual a {result:.1f}K")
    else:
        speak("Conversão não suportada")


##tradutor


def translate_text():
    translator = Translator()

    language_names_to_codes = {
        "inglês": "en",
        "português": "pt",
        "espanhol": "es",
        # Adicione mais mapeamentos aqui
    }

    speak("Por favor, diga a frase que você deseja traduzir.")
    text = listen()

    if text:
        detected_language = translator.detect(text)
        detected_language_code = detected_language.lang

        speak("Para qual idioma você deseja traduzir?")
        target_language_name = listen()

        target_language_code = language_names_to_codes.get(target_language_name.lower())

        if target_language_code:
            translation = translator.translate(text, src=detected_language_code, dest=target_language_code)
            translated_text = translation.text
            speak(f"A tradução para o idioma {target_language_name} é: {translated_text}")
        else:
            speak("Desculpe, não entendi o idioma de destino.")
    else:
        speak("Desculpe, não entendi a frase para traduzir.")



##calculo



def calc():
    speak("Fale o comando de matemática...")

    try:
        audio = listen()
        command = audio.lower()

        match = re.search(r'(\d+)\s?[+\-*/xX]\s?(\d+)', command)
        if match:
            num1 = int(match.group(1))
            operator = re.findall(r'[+\-*/xX]', command)[0]
            num2 = int(match.group(2))

            if operator == '+':
                result = num1 + num2
            elif operator == '-':
                result = num1 - num2
            elif operator == '*' or operator == 'x' or operator == 'X':
                result = num1 * num2
            elif operator == '/':
                if num2 != 0:
                    result = num1 / num2
                else:
                    speak("Desculpe, divisão por zero não é permitida.")
                    return

            speak(f"O resultado da operação é {result}")
        else:
            speak("Comando de matemática não reconhecido.")
    except Exception as e:
        speak(f"Ocorreu um erro: {str(e)}")




# Função para converter altura em centímetros diretamente
def parse_height_input(input_str):
    try:
        # Substitui vírgula por ponto e converte para float
        height_parts = [float(part) for part in input_str.replace(',', '.').split('.')]

        # Se houver apenas uma parte, considera metros
        if len(height_parts) == 1:
            height_m = height_parts[0]
            height_cm = height_m * 100
        # Se houver duas partes, considera metros e centímetros
        elif len(height_parts) == 2:
            height_m, height_cm = height_parts
            height_cm += height_m * 100  # Adiciona a parte em metros convertida para centímetros
        else:
            raise ValueError("Formato de altura inválido")

        # Validando a altura
        if height_cm <= 0 or height_cm > 300:  # Supondo uma altura razoável em centímetros
            raise ValueError("Altura fora da faixa razoável")

        return height_cm
    except ValueError:
        return 0  # Se não for possível converter, retorna 0

# Função para calcular IMC
def calculate_bmi():
    speak("Vamos calcular o seu Índice de Massa Corporal (IMC).")

    try:
        # Solicita ao usuário o peso
        speak("Por favor, me diga o seu peso em quilogramas.")
        weight = float(listen())

        # Validar peso
        if weight <= 0:
            speak("O peso deve ser um valor positivo. Por favor, tente novamente.")
            return

        # Solicita ao usuário a altura
        speak("Agora, por favor, me diga a sua altura em metros e centímetros.")
        height_input = listen().replace(',', '.')

        # Convertendo palavras para números e removendo unidades
        height_cm = parse_height_input(height_input)

        # Validando a altura
        if height_cm <= 0 or height_cm > 300:  # Altura em centímetros, considerando uma faixa razoável
            speak("A altura deve estar em uma faixa razoável. Por favor, tente novamente.")
            return

        # Convertendo altura para metros
        height_m = height_cm / 100

        # Calcula o IMC (IMC = peso / altura^2)
        bmi = weight / (height_m ** 2)

        # Fornece a resposta ao usuário
        speak(f"Seu Índice de Massa Corporal (IMC) é {bmi:.2f}.")

        # Avaliação do IMC
        if bmi < 18.5:
            speak("Você está abaixo do peso. Consulte um profissional de saúde para orientação.")
        elif 18.5 <= bmi < 24.9:
            speak("Seu peso está dentro da faixa saudável. Continue assim!")
        elif 25 <= bmi < 29.9:
            speak("Você está com sobrepeso. Considere adotar hábitos mais saudáveis.")
        else:
            speak("Você está em uma faixa de peso que indica obesidade. Consulte um profissional de saúde para orientação.")

    except ValueError:
        speak("Desculpe, não consegui entender o seu peso ou altura. Certifique-se de fornecer valores numéricos válidos.")


##dia de hoje


def obter_dia_atual():
    # Obter a data atual
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
    data_atual = datetime.now()

    # Mapear o número do dia da semana para o nome do dia
    dias_da_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    nome_do_dia = dias_da_semana[data_atual.weekday()]

    # Formatando a data
    data_formatada = data_atual.strftime("%d de %B")

    # Imprimindo a resposta
    resposta = f'hoje é {nome_do_dia}, {data_formatada}'
    speak(resposta)



##data de hoje


def falar_data_atual():
    # Definir o idioma para português brasileiro
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')

    # Obter a data atual
    data_atual = datetime.now()

    # Mapear o número do mês para o nome do mês
    meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    nome_do_mes = meses[data_atual.month - 1]

    # Formatando a data
    data_formatada = data_atual.strftime("%d de %B de %Y")

    # Construir a resposta
    resposta = f"a data de hoje é {data_formatada}"

    # Falar a resposta
    speak(resposta)


##hora de  agora

def falar_hora_atual():
    # Obter a hora atual
    hora_atual = datetime.now().strftime("%H:%M")

    # Construir a resposta
    resposta = f"Agora são {hora_atual} horas."

    # Falar a resposta
    speak(resposta)



##pesquisar



def pesquisar_no_google(query):
    api_key = "AIzaSyArAP0wDneuNJDAijMxy7wzpUNZZha8DeQ"
    cx = "81260142d4a044762"  # Você precisa criar um mecanismo de pesquisa personalizado (CX) no Console do Google para obter este valor

    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cx}"

    try:
        response = requests.get(url)
        data = response.json()

        if "items" in data:
            # Retornar os resultados da pesquisa
            return data["items"]
        else:
            return []

    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")
        return []
    

##filmes

def obter_filmes_populares(numero_filmes=5):
    api_key = "70e7dd8fc4e7d9a09fbb3b998635d3fb"
    url = f'https://api.themoviedb.org/3/discover/movie?sort_by=popularity.desc&api_key={api_key}'
    params = {
        'api_key': api_key,
        'language': 'pt-BR'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        filmes = data.get('results', [])

        if filmes:
            for i, filme in enumerate(filmes[:numero_filmes], start=1):
                detalhes_filme(filme, i)
        else:
            speak("Nenhum filme encontrado.")

    except requests.exceptions.RequestException as e:
        speak(f"Erro ao obter filmes: {str(e)}")

def detalhes_filme(filme, numero):
    titulo = filme.get('title', 'Título Desconhecido')
    descricao = filme.get('overview', 'Descrição não disponível')
    data_lancamento = filme.get('release_date', 'Data de lançamento desconhecida')
    popularidade = filme.get('popularity', 'Popularidade desconhecida')

    speak(f"\nDetalhes do Filme {numero} - '{titulo}':")
    speak(f"Descrição: {descricao}")
    speak(f"Data de Lançamento: {data_lancamento}")
    speak(f"Popularidade: {popularidade}")


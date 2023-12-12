from funcoes import speak, listen, get_weather, convert_temperature, translate_text, calculate_bmi, calc, obter_dia_atual, falar_data_atual, falar_hora_atual,pesquisar_no_google,obter_filmes_populares
import pyttsx3
class SeraphineAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', self.voices[0].id)

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def run(self):
        self.speak("Olá, me chamo Seraphine, como posso te ajudar?")
        while True:  # Loop principal para aguardar novos comandos
            command = listen()  # Chame a função listen diretamente
            if command:
                tokens = command.split()
                keywords = ['IMC','previsão','pesquisar','dia','Dia','filmes','filme','horas','hora','Hora', 'tempo','data', 'Data', 'recomendar', 'restaurante','traduza', 'imc','traduzir', 'converter', 'conversão', 'calcule', 'calcular','cálculo']
                intent = None
                for keyword in keywords:
                    if keyword in tokens:
                        intent = keyword
                        break

                if intent == 'previsão' and 'tempo' in tokens:
                    self.speak("Por favor, diga-me a cidade para a qual você deseja saber a previsão do tempo.")
                    city = listen()  # Chame a função listen diretamente
                    if city:
                        weather_info = get_weather(city)  # Chame a função get_weather diretamente
                        self.speak(weather_info)
                elif intent == 'recomendar' and 'restaurante' in tokens:
                    self.speak("Recomendo o restaurante XYZ, localizado próximo à sua localização.")
                elif intent in ['traduzir', 'traduza']:
                    translate_text()
                elif intent in ['calcular', 'cálculo','calcule']:
                    calc()  # Chame a função calc diretamente
                elif intent in ['converter', 'conversão']:
                    convert_temperature()  # Chame a função convert_temperature diretamente
                elif intent in ['imc', 'IMC']:
                    calculate_bmi()
                elif intent in ['dia', 'Dia']:
                    obter_dia_atual()
                elif intent in ['data', 'Data']:
                    falar_data_atual()
                elif intent in ['Hora', 'hora', 'horas']:
                    falar_hora_atual()
                elif intent in ['pesquisar']:
                    self.speak("O que você gostaria de pesquisar no Google?")
                    query = listen()
                    if query:
                        resultados = pesquisar_no_google(query)
                        for i, item in enumerate(resultados):
                            title = item["title"]
                            link = item["link"]
                            snippet = item["snippet"]
                            self.speak(f"Resultado {i + 1}:\nTítulo: {title}\nLink: {link}\nSnippet: {snippet}\n")
                    else:
                        self.speak("Consulta inválida.")
      
                elif intent in [ 'filme', 'filmes']:
                    obter_filmes_populares()
                elif "encerrar" in command:
                    self.speak("Encerrando a assistência.")
                    break  # Sai do loop principal se "encerrar" for detectado
                else:
                    self.speak("Desculpe, não entendi o comando.")
if __name__ == "__main__":
    assistant = SeraphineAssistant()
    assistant.run()

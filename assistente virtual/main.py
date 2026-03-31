from funcoes import listen, get_weather, convert_temperature, translate_text, calculate_bmi, calc, obter_dia_atual, falar_data_atual, falar_hora_atual, obter_filmes_populares, responder_com_base_na_internet, normalize_text, abrir_destino, executar_rotina, descrever_nucleo, registrar_interacao, registrar_feedback, gerar_autoavaliacao, resumo_aprendizado, explicar_como_aprende_programacao, explicar_onde_aprende_a_se_programar, gerar_propostas_de_autoaprimoramento, preparar_base_de_treinamento, inferir_intencao_treinada, avancar_treinamento_local, descrever_status_treinamento
import pyttsx3


class SeraphineCore:
    def __init__(self, speaker):
        self.speak = speaker
        self.last_subject = ""
        self.last_action = ""
        self.training_state = preparar_base_de_treinamento()

    def detect_intent(self, command):
        normalized = normalize_text(command)
        trained_intent = inferir_intencao_treinada(command)

        if any(term in normalized for term in ['encerrar', 'sair', 'fechar', 'parar']):
            return 'exit'
        if any(term in normalized for term in ['iniciar treinamento', 'treinar agora', 'treinar comandos', 'iniciar treino']):
            return 'training_bootstrap'
        if any(term in normalized for term in ['avancar treinamento', 'proximo nivel de treinamento', 'continue o treinamento', 'suba o nivel do treinamento']):
            return 'training_advance'
        if any(term in normalized for term in ['status do treinamento', 'como esta o treinamento', 'resumo do treinamento']):
            return 'training_status'
        if any(term in normalized for term in ['deu certo', 'funcionou', 'isso ajudou', 'bom trabalho', 'voce acertou']):
            return 'positive_feedback'
        if any(term in normalized for term in ['deu errado', 'nao funcionou', 'isso nao ajudou', 'voce errou', 'falhou']):
            return 'negative_feedback'
        if any(term in normalized for term in ['autoavaliacao', 'se avalie', 'como voce esta evoluindo', 'o que voce aprendeu', 'como voce aprendeu']):
            return 'self_review'
        if any(term in normalized for term in ['status de aprendizado', 'resumo do aprendizado', 'como esta seu aprendizado']):
            return 'learning_status'
        if any(term in normalized for term in ['como aprender sintaxe', 'como voce aprende sintaxe', 'como aprender a se programar', 'como voce aprende a se programar']):
            return 'coding_learning'
        if any(term in normalized for term in ['onde voce aprende a se programar', 'onde aprende programacao', 'onde aprende sintaxe']):
            return 'coding_source'
        if any(term in normalized for term in ['proponha melhorias no codigo', 'como pode se aprimorar no codigo', 'propostas de autoaprimoramento', 'melhorias no proprio codigo']):
            return 'coding_proposals'
        if normalized in ['continue', 'continuar', 'me fale mais', 'fale mais'] and self.last_subject:
            return 'continue'
        if trained_intent:
            return trained_intent
        if any(normalized.startswith(prefix) for prefix in ['abrir', 'abra', 'acessar', 'acesse', 'iniciar', 'inicie', 'executar', 'execute', 'entre no', 'entre na']):
            return 'open'
        if 'rotina' in normalized or any(term in normalized for term in ['modo trabalho', 'modo estudo', 'modo desenvolvimento', 'modo pesquisa']):
            return 'routine'
        if any(term in normalized for term in ['nucleo', 'capacidades', 'o que voce consegue fazer']):
            return 'core_help'
        if ('previsao' in normalized and 'tempo' in normalized) or 'clima' in normalized:
            return 'weather'
        if 'recomendar' in normalized and 'restaurante' in normalized:
            return 'restaurant'
        if any(term in normalized for term in ['traduzir', 'traduza']):
            return 'translate'
        if any(term in normalized for term in ['calcular', 'calculo', 'calcule']):
            return 'calculate'
        if any(term in normalized for term in ['converter', 'conversao']):
            return 'convert'
        if 'imc' in normalized:
            return 'bmi'
        if 'dia' in normalized and 'hoje' in normalized:
            return 'day'
        if 'data' in normalized:
            return 'date'
        if any(term in normalized for term in ['hora', 'horas']):
            return 'time'
        if any(term in normalized for term in ['filme', 'filmes']):
            return 'movies'
        if any(normalized.startswith(prefix) for prefix in ['pesquisar', 'pesquise', 'buscar', 'busque', 'procure']):
            return 'search'
        if any(term in normalized for term in ['quem e', 'o que e', 'me fale sobre', 'me diga sobre', 'me explique']):
            return 'search'

        return 'web_fallback'

    def _remove_prefix(self, text, prefixes):
        normalized = normalize_text(text)
        for prefix in sorted(prefixes, key=len, reverse=True):
            if normalized.startswith(prefix):
                return normalized[len(prefix):].strip(" ?")
        return normalized.strip(" ?")

    def extract_search_query(self, command):
        return self._remove_prefix(
            command,
            ['pesquisar', 'pesquise', 'buscar', 'busque', 'procure', 'me fale sobre', 'me diga sobre', 'me explique', 'quem e', 'o que e']
        )

    def extract_open_target(self, command):
        return self._remove_prefix(
            command,
            ['abrir', 'abra', 'acessar', 'acesse', 'iniciar', 'inicie', 'executar', 'execute', 'entre no', 'entre na']
        )

    def extract_routine_name(self, command):
        normalized = normalize_text(command)
        for term in ['modo trabalho', 'modo estudo', 'modo desenvolvimento', 'modo pesquisa']:
            if term in normalized:
                return term.replace('modo ', '')

        routine_name = self._remove_prefix(command, ['executar rotina', 'rodar rotina', 'iniciar rotina', 'rotina de', 'rotina do', 'rotina da', 'rotina'])
        for prefix in ['de ', 'do ', 'da ']:
            if routine_name.startswith(prefix):
                return routine_name[len(prefix):].strip()
        return routine_name

    def answer_from_internet(self, query):
        cleaned_query = query.strip()
        if not cleaned_query:
            self.speak("Não consegui identificar o assunto da pesquisa.")
            registrar_interacao(query, "search", "search", "", False, "consulta vazia")
            return

        self.last_subject = cleaned_query
        self.last_action = "search"
        self.speak("Vou consultar a internet e resumir a melhor resposta para você.")
        answer, results = responder_com_base_na_internet(cleaned_query)

        print(f"Consulta web: {cleaned_query}")
        for index, item in enumerate(results[:3], start=1):
            print(f"{index}. {item['title']} - {item['link']}")

        self.speak(answer)
        registrar_interacao(
            cleaned_query,
            "search",
            "search",
            cleaned_query,
            bool(results),
            answer
        )

    def open_target(self, target):
        result = abrir_destino(target)
        self.last_subject = target
        self.last_action = "open"
        self.speak(result["message"])
        registrar_interacao(
            target,
            "open",
            "open",
            target,
            result.get("success"),
            result.get("message", "")
        )
        return result

    def run_routine(self, routine_name):
        result = executar_rotina(routine_name)
        self.last_subject = routine_name
        self.last_action = "routine"
        self.speak(result["message"])
        registrar_interacao(
            routine_name,
            "routine",
            "routine",
            routine_name,
            result.get("success"),
            result.get("message", "")
        )
        return result

    def record_basic_action(self, command, intent, success=True, subject=""):
        registrar_interacao(command, intent, intent, subject or command, success, "")

    def process_feedback(self, command, positive=True):
        message = registrar_feedback(command, positive=positive)
        self.speak(message)
        return message

    def reflect_on_progress(self):
        reflection = gerar_autoavaliacao()
        self.speak(reflection["summary"])
        return reflection

    def describe_learning(self):
        summary = resumo_aprendizado()
        self.speak(summary)
        return summary

    def explain_coding_learning(self):
        summary = explicar_como_aprende_programacao()
        self.speak(summary)
        return summary

    def explain_coding_source(self):
        summary = explicar_onde_aprende_a_se_programar()
        self.speak(summary)
        return summary

    def propose_code_improvements(self):
        payload = gerar_propostas_de_autoaprimoramento()
        proposals = payload.get("proposals", [])
        if not proposals:
            message = "Ainda não tenho propostas de código suficientes."
        else:
            message = f"Minhas próximas propostas de evolução são: {'; '.join(proposals[:3])}."
        self.speak(message)
        return payload

    def bootstrap_training(self):
        payload = preparar_base_de_treinamento()
        self.speak(payload["message"])
        return payload

    def advance_training(self):
        payload = avancar_treinamento_local()
        self.speak(payload["message"])
        return payload

    def describe_training(self):
        message = descrever_status_treinamento()
        self.speak(message)
        return message


class SeraphineAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', self.voices[0].id)
        self.core = SeraphineCore(self.speak)

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def run(self):
        self.speak("Olá, me chamo Seraphine, como posso te ajudar?")
        while True:
            command = listen()
            if command:
                intent = self.core.detect_intent(command)

                if intent == 'weather':
                    self.speak("Por favor, diga-me a cidade para a qual você deseja saber a previsão do tempo.")
                    city = listen()
                    if city:
                        weather_info = get_weather(city)
                        self.speak(weather_info)
                        self.core.record_basic_action(command, intent, True, city)
                elif intent == 'restaurant':
                    self.speak("Recomendo o restaurante XYZ, localizado próximo à sua localização.")
                    self.core.record_basic_action(command, intent, True, "restaurante")
                elif intent == 'translate':
                    translate_text()
                    self.core.record_basic_action(command, intent, True)
                elif intent == 'calculate':
                    calc()
                    self.core.record_basic_action(command, intent, True)
                elif intent == 'convert':
                    convert_temperature()
                    self.core.record_basic_action(command, intent, True)
                elif intent == 'bmi':
                    calculate_bmi()
                    self.core.record_basic_action(command, intent, True)
                elif intent == 'day':
                    obter_dia_atual()
                    self.core.record_basic_action(command, intent, True)
                elif intent == 'date':
                    falar_data_atual()
                    self.core.record_basic_action(command, intent, True)
                elif intent == 'time':
                    falar_hora_atual()
                    self.core.record_basic_action(command, intent, True)
                elif intent == 'open':
                    target = self.core.extract_open_target(command)
                    if not target:
                        self.speak("O que você quer que eu abra?")
                        target = listen()
                    self.core.open_target(target)
                elif intent == 'routine':
                    routine_name = self.core.extract_routine_name(command)
                    if not routine_name:
                        self.speak("Qual rotina você quer executar?")
                        routine_name = listen()
                    self.core.run_routine(routine_name)
                elif intent == 'core_help':
                    self.speak(descrever_nucleo())
                    self.core.record_basic_action(command, intent, True, "nucleo")
                elif intent == 'training_bootstrap':
                    self.core.bootstrap_training()
                elif intent == 'training_advance':
                    self.core.advance_training()
                elif intent == 'training_status':
                    self.core.describe_training()
                elif intent == 'positive_feedback':
                    self.core.process_feedback(command, positive=True)
                elif intent == 'negative_feedback':
                    self.core.process_feedback(command, positive=False)
                elif intent == 'self_review':
                    self.core.reflect_on_progress()
                elif intent == 'learning_status':
                    self.core.describe_learning()
                elif intent == 'coding_learning':
                    self.core.explain_coding_learning()
                elif intent == 'coding_source':
                    self.core.explain_coding_source()
                elif intent == 'coding_proposals':
                    self.core.propose_code_improvements()
                elif intent == 'search':
                    query = self.core.extract_search_query(command)
                    if query in ['pesquisar', 'pesquise', 'buscar', 'busque', 'procure']:
                        self.speak("O que você gostaria de pesquisar na internet?")
                        query = listen()
                    self.core.answer_from_internet(query)
                elif intent == 'continue':
                    self.core.answer_from_internet(self.core.last_subject)
                elif intent == 'movies':
                    obter_filmes_populares()
                elif intent == 'exit':
                    self.speak("Encerrando a assistência.")
                    break
                else:
                    self.core.answer_from_internet(command)


if __name__ == "__main__":
    assistant = SeraphineAssistant()
    assistant.run()

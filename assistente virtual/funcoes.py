import pyttsx3
import speech_recognition as sr
from googletrans import Translator
import requests
import locale
import re
import ast
import os
import json
import webbrowser
import unicodedata
from word2number import w2n
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


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
        audio = r.listen(source, timeout=5, phrase_time_limit=12)

    try:
        text = r.recognize_google(audio, language='pt-BR')
        print(f"Você disse: {text}")
        return text
    except sr.WaitTimeoutError:
        print("Tempo de espera excedido.")
        return ""
    except sr.UnknownValueError:
        print("Não foi possível entender o áudio.")
        return ""
    except Exception as e:
        print("Ocorreu um erro ao reconhecer o áudio:", str(e))
        return ""


def normalize_text(text):
    normalized = unicodedata.normalize('NFKD', text or "")
    normalized = ''.join(char for char in normalized if not unicodedata.combining(char))
    return normalized.lower().strip()


MEMORY_FILE = Path(__file__).with_name("seraphine_memory.json")


def _default_sites():
    return {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "google agenda": "https://calendar.google.com",
        "agenda": "https://calendar.google.com",
        "google drive": "https://drive.google.com",
        "drive": "https://drive.google.com",
        "wikipedia": "https://pt.wikipedia.org",
        "github": "https://github.com",
        "chatgpt": "https://chat.openai.com",
        "whatsapp": "https://web.whatsapp.com",
        "whatsapp web": "https://web.whatsapp.com",
        "spotify": "https://open.spotify.com",
        "netflix": "https://www.netflix.com",
        "linkedin": "https://www.linkedin.com",
        "google docs": "https://docs.google.com",
        "google planilhas": "https://sheets.google.com"
    }


def _default_routines():
    return {
        "trabalho": ["gmail", "google agenda", "google drive", "whatsapp"],
        "estudo": ["youtube", "google", "wikipedia"],
        "desenvolvimento": ["visual studio code", "github", "chatgpt"],
        "pesquisa": ["google", "youtube", "wikipedia"]
    }


def load_seraphine_memory():
    memory = {
        "learned_targets": {},
        "routines": _default_routines(),
        "interactions": [],
        "action_stats": {},
        "reflections": [],
        "coding_knowledge": {},
        "rewrite_proposals": [],
        "training_sources": [],
        "intent_examples": {},
        "training_progress": {"completed_levels": []}
    }

    if not MEMORY_FILE.exists():
        return memory

    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            persisted = json.load(file)
    except (OSError, json.JSONDecodeError):
        return memory

    memory["learned_targets"].update(persisted.get("learned_targets", {}))
    memory["routines"].update(persisted.get("routines", {}))
    memory["interactions"] = persisted.get("interactions", [])[-200:]
    memory["action_stats"].update(persisted.get("action_stats", {}))
    memory["reflections"] = persisted.get("reflections", [])[-50:]
    memory["coding_knowledge"].update(persisted.get("coding_knowledge", {}))
    memory["rewrite_proposals"] = persisted.get("rewrite_proposals", [])[-50:]
    memory["training_sources"] = persisted.get("training_sources", [])
    memory["intent_examples"].update(persisted.get("intent_examples", {}))
    memory["training_progress"].update(persisted.get("training_progress", {}))
    return memory


def save_seraphine_memory(memory):
    try:
        with MEMORY_FILE.open("w", encoding="utf-8") as file:
            json.dump(memory, file, ensure_ascii=False, indent=2)
    except OSError:
        return False
    return True


def remember_target(target, resource_type, value):
    key = normalize_text(target)
    memory = load_seraphine_memory()
    memory["learned_targets"][key] = {
        "type": resource_type,
        "value": value,
        "updated_at": datetime.now().isoformat(),
        "successes": memory["learned_targets"].get(key, {}).get("successes", 0),
        "failures": memory["learned_targets"].get(key, {}).get("failures", 0)
    }
    save_seraphine_memory(memory)


def _ensure_action_stats(memory, action_name):
    if action_name not in memory["action_stats"]:
        memory["action_stats"][action_name] = {
            "successes": 0,
            "failures": 0,
            "last_subject": "",
            "last_result": "",
            "updated_at": ""
        }
    return memory["action_stats"][action_name]


def registrar_interacao(command, intent, action_name="", subject="", success=None, result_message=""):
    memory = load_seraphine_memory()
    timestamp = datetime.now().isoformat()

    interaction = {
        "timestamp": timestamp,
        "command": command,
        "intent": intent,
        "action_name": action_name,
        "subject": subject,
        "success": success,
        "result_message": result_message,
        "feedback": ""
    }
    memory["interactions"].append(interaction)
    memory["interactions"] = memory["interactions"][-200:]

    if action_name:
        stats = _ensure_action_stats(memory, action_name)
        if success is True:
            stats["successes"] += 1
        elif success is False:
            stats["failures"] += 1
        stats["last_subject"] = subject
        stats["last_result"] = result_message
        stats["updated_at"] = timestamp

    target_key = normalize_text(subject)
    if target_key and target_key in memory["learned_targets"] and success is not None:
        if success:
            memory["learned_targets"][target_key]["successes"] = memory["learned_targets"][target_key].get("successes", 0) + 1
        else:
            memory["learned_targets"][target_key]["failures"] = memory["learned_targets"][target_key].get("failures", 0) + 1
        memory["learned_targets"][target_key]["updated_at"] = timestamp

    save_seraphine_memory(memory)
    return interaction


def registrar_feedback(feedback_text, positive=True):
    memory = load_seraphine_memory()
    if not memory["interactions"]:
        return "Ainda não tenho uma ação recente para aprender com esse feedback."

    feedback = "positivo" if positive else "negativo"
    last_interaction = memory["interactions"][-1]
    last_interaction["feedback"] = feedback
    last_interaction["feedback_text"] = feedback_text
    last_interaction["feedback_at"] = datetime.now().isoformat()

    action_name = last_interaction.get("action_name", "")
    if action_name:
        stats = _ensure_action_stats(memory, action_name)
        if positive:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
        stats["updated_at"] = datetime.now().isoformat()

    subject_key = normalize_text(last_interaction.get("subject", ""))
    if subject_key and subject_key in memory["learned_targets"]:
        target = memory["learned_targets"][subject_key]
        field = "successes" if positive else "failures"
        target[field] = target.get(field, 0) + 1
        target["updated_at"] = datetime.now().isoformat()

    save_seraphine_memory(memory)
    if positive:
        return "Aprendi com seu feedback positivo e reforcei esse caminho."
    return "Aprendi com seu feedback negativo e vou reduzir a confiança nesse caminho."


def gerar_autoavaliacao():
    memory = load_seraphine_memory()
    interactions = memory.get("interactions", [])
    action_stats = memory.get("action_stats", {})

    total = len(interactions)
    successes = len([item for item in interactions if item.get("success") is True])
    failures = len([item for item in interactions if item.get("success") is False])

    ranked_actions = []
    for action_name, stats in action_stats.items():
        action_successes = stats.get("successes", 0)
        action_failures = stats.get("failures", 0)
        volume = action_successes + action_failures
        score = action_successes - action_failures
        ranked_actions.append((score, volume, action_name, stats))

    ranked_actions.sort(reverse=True)
    best_action = ranked_actions[0][2] if ranked_actions else "nenhuma"
    weakest_action = ranked_actions[-1][2] if ranked_actions else "nenhuma"

    suggestions = []
    if failures > successes:
        suggestions.append("preciso pedir mais confirmações antes de agir")
    if "open" in action_stats and action_stats["open"].get("failures", 0) > action_stats["open"].get("successes", 0):
        suggestions.append("preciso aprender mais caminhos locais de aplicativos e atalhos")
    if "search" in action_stats and action_stats["search"].get("successes", 0) < 3:
        suggestions.append("preciso melhorar a pesquisa e o resumo de respostas vindas da internet")
    if not suggestions:
        suggestions.append("meu próximo passo é ampliar memória, ranking de preferências e validação por feedback")

    summary = (
        f"Já registrei {total} interação(ões). "
        f"Acertos observados: {successes}. "
        f"Falhas observadas: {failures}. "
        f"Minha ação mais forte agora é {best_action}. "
        f"A mais fraca é {weakest_action}. "
        f"Próximo foco: {suggestions[0]}."
    )

    reflection = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "suggestions": suggestions
    }
    memory["reflections"].append(reflection)
    memory["reflections"] = memory["reflections"][-50:]
    save_seraphine_memory(memory)

    return reflection


def resumo_aprendizado():
    memory = load_seraphine_memory()
    interactions = len(memory.get("interactions", []))
    reflections = len(memory.get("reflections", []))
    ranked_targets = sorted(
        memory.get("learned_targets", {}).items(),
        key=lambda item: item[1].get("successes", 0) - item[1].get("failures", 0),
        reverse=True
    )
    top_target = ranked_targets[0][0] if ranked_targets else "nenhum ainda"
    return (
        f"Tenho {interactions} interações registradas, {reflections} autoavaliações salvas "
        f"e meu alvo mais confiável no momento é {top_target}."
    )


def _listar_arquivos_python_projeto():
    project_dir = Path(__file__).parent
    return sorted(
        [
            file_path for file_path in project_dir.glob("*.py")
            if file_path.name != Path(__file__).name + ".tmp"
        ],
        key=lambda item: item.name
    )


def _analisar_arquivo_python(file_path):
    try:
        source = file_path.read_text(encoding="utf-8")
    except OSError:
        return None

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {
            "file": file_path.name,
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "assignments": 0,
            "calls": 0,
            "syntax_error": True
        }

    functions = len([node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))])
    classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
    imports = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
    assignments = len([node for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AnnAssign))])
    calls = len([node for node in ast.walk(tree) if isinstance(node, ast.Call)])

    return {
        "file": file_path.name,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "assignments": assignments,
        "calls": calls,
        "syntax_error": False
    }


def aprender_sintaxe_local():
    analyses = []
    for file_path in _listar_arquivos_python_projeto():
        analysis = _analisar_arquivo_python(file_path)
        if analysis:
            analyses.append(analysis)

    total_functions = sum(item["functions"] for item in analyses)
    total_classes = sum(item["classes"] for item in analyses)
    total_imports = sum(item["imports"] for item in analyses)
    syntax_errors = len([item for item in analyses if item.get("syntax_error")])

    knowledge = {
        "timestamp": datetime.now().isoformat(),
        "files_analyzed": len(analyses),
        "total_functions": total_functions,
        "total_classes": total_classes,
        "total_imports": total_imports,
        "syntax_errors": syntax_errors,
        "files": analyses
    }

    memory = load_seraphine_memory()
    memory["coding_knowledge"]["latest"] = knowledge
    save_seraphine_memory(memory)
    return knowledge


def explicar_como_aprende_programacao():
    knowledge = aprender_sintaxe_local()
    return (
        f"Eu aprendo sintaxe lendo o próprio projeto Python, observando imports, funções, classes e chamadas. "
        f"Neste momento analisei {knowledge['files_analyzed']} arquivo(s), com {knowledge['total_functions']} função(ões), "
        f"{knowledge['total_classes']} classe(s) e {knowledge['total_imports']} importação(ões). "
        f"Meu caminho seguro para aprender a me programar é: estudar o código atual, medir erros e acertos, "
        f"gerar propostas de melhoria e só então aplicar mudanças validadas."
    )


def gerar_propostas_de_autoaprimoramento():
    knowledge = aprender_sintaxe_local()
    memory = load_seraphine_memory()
    action_stats = memory.get("action_stats", {})

    proposals = []

    if knowledge["total_functions"] < 20:
        proposals.append("criar mais módulos especializados para separar voz, memória, ferramentas e aprendizado")
    if knowledge["syntax_errors"] > 0:
        proposals.append("corrigir erros de sintaxe antes de tentar qualquer evolução mais profunda")
    if action_stats.get("search", {}).get("failures", 0) >= action_stats.get("search", {}).get("successes", 0):
        proposals.append("melhorar a estratégia de pesquisa e resumo antes de ampliar autonomia")
    if action_stats.get("open", {}).get("failures", 0) > 0:
        proposals.append("aprender mais aliases e caminhos locais para abertura de aplicativos")

    proposals.extend([
        "criar uma camada de propostas de código em vez de autoedição irrestrita",
        "usar testes automatizados como critério mínimo antes de aceitar mudanças próprias",
        "registrar padrões recorrentes do projeto para imitar sua própria sintaxe e estilo"
    ])

    unique_proposals = []
    for proposal in proposals:
        if proposal not in unique_proposals:
            unique_proposals.append(proposal)

    payload = {
        "timestamp": datetime.now().isoformat(),
        "proposals": unique_proposals[:6]
    }

    memory["rewrite_proposals"].append(payload)
    memory["rewrite_proposals"] = memory["rewrite_proposals"][-50:]
    save_seraphine_memory(memory)
    return payload


def explicar_onde_aprende_a_se_programar():
    proposal_payload = gerar_propostas_de_autoaprimoramento()
    latest = proposal_payload["proposals"][0] if proposal_payload["proposals"] else "continuar observando o próprio código"
    return (
        "Eu não devo aprender a me programar alterando meu código às cegas. "
        "Meu lugar de aprendizado é o próprio repositório, os testes, o histórico de interações e as avaliações de desempenho. "
        f"Hoje meu próximo passo seguro é {latest}."
    )


def _default_public_training_sources():
    return [
        {
            "name": "OHF-Voice/intents",
            "url": "https://github.com/OHF-Voice/intents",
            "focus": "dados de intents para controle por voz local"
        },
        {
            "name": "Fluent Speech Commands",
            "url": "https://picovoice.ai/blog/open-source-natural-language-understanding-data/",
            "focus": "comandos simples de assistente de voz"
        }
    ]


def _default_training_curriculum():
    return {
        "basic": {
            "open": [
                "abrir youtube",
                "abrir google",
                "abrir spotify",
                "abra o explorador de arquivos"
            ],
            "search": [
                "pesquisar clima hoje",
                "quem e alan turing",
                "me fale sobre python"
            ],
            "time": [
                "que horas sao",
                "me diga as horas"
            ],
            "date": [
                "qual a data de hoje",
                "me diga a data"
            ]
        },
        "intermediate": {
            "weather": [
                "como esta o clima",
                "previsao do tempo",
                "qual a previsao do tempo"
            ],
            "routine": [
                "modo trabalho",
                "rotina de estudo",
                "executar rotina de pesquisa"
            ],
            "translate": [
                "traduza uma frase",
                "quero traduzir um texto"
            ],
            "calculate": [
                "calcule 2 mais 2",
                "quero fazer uma conta"
            ]
        },
        "advanced": {
            "self_review": [
                "como voce esta evoluindo",
                "autoavaliacao"
            ],
            "learning_status": [
                "status de aprendizado",
                "resumo do aprendizado"
            ],
            "coding_learning": [
                "como aprender a se programar",
                "como voce aprende sintaxe"
            ],
            "coding_source": [
                "onde voce aprende a se programar",
                "onde aprende sintaxe"
            ],
            "coding_proposals": [
                "propostas de autoaprimoramento",
                "melhorias no proprio codigo"
            ],
            "positive_feedback": [
                "deu certo",
                "isso ajudou"
            ],
            "negative_feedback": [
                "deu errado",
                "isso nao ajudou"
            ]
        }
    }


def _store_intent_examples(memory, examples):
    for intent, phrases in examples.items():
        stored = memory["intent_examples"].setdefault(intent, [])
        for phrase in phrases:
            normalized_phrase = normalize_text(phrase)
            if normalized_phrase and normalized_phrase not in stored:
                stored.append(normalized_phrase)


def inicializar_fontes_de_treinamento():
    memory = load_seraphine_memory()
    if not memory["training_sources"]:
        memory["training_sources"] = _default_public_training_sources()
        save_seraphine_memory(memory)
    return memory["training_sources"]


def treinar_comandos_localmente(level="basic"):
    curriculum = _default_training_curriculum()
    ordered_levels = ["basic", "intermediate", "advanced"]
    if level == "all":
        selected_levels = ordered_levels
    elif level in curriculum:
        selected_levels = [level]
    else:
        selected_levels = ["basic"]

    memory = load_seraphine_memory()
    total_examples = 0
    for selected_level in selected_levels:
        examples = curriculum[selected_level]
        _store_intent_examples(memory, examples)
        total_examples += sum(len(item) for item in examples.values())
        completed_levels = memory["training_progress"].setdefault("completed_levels", [])
        if selected_level not in completed_levels:
            completed_levels.append(selected_level)

    memory["training_progress"]["last_training_at"] = datetime.now().isoformat()
    save_seraphine_memory(memory)

    return {
        "levels": selected_levels,
        "example_count": total_examples,
        "intent_count": len(memory["intent_examples"])
    }


def avancar_treinamento_local():
    curriculum = _default_training_curriculum()
    ordered_levels = ["basic", "intermediate", "advanced"]
    memory = load_seraphine_memory()
    completed = memory.get("training_progress", {}).get("completed_levels", [])

    next_level = ""
    for level in ordered_levels:
        if level not in completed:
            next_level = level
            break

    if not next_level:
        return {
            "level": "advanced",
            "message": "Todos os níveis do treinamento local já foram aplicados."
        }

    result = treinar_comandos_localmente(next_level)
    return {
        "level": next_level,
        "message": f"Treinamento local do nível {next_level} concluído com {result['example_count']} exemplo(s)."
    }


def preparar_base_de_treinamento():
    sources = inicializar_fontes_de_treinamento()
    memory = load_seraphine_memory()
    completed = memory.get("training_progress", {}).get("completed_levels", [])
    if not completed:
        result = treinar_comandos_localmente("basic")
        return {
            "sources": sources,
            "message": f"Base pública registrada e treinamento básico iniciado com {result['example_count']} exemplo(s)."
        }

    return {
        "sources": sources,
        "message": "A base pública já está registrada e o treinamento local já foi inicializado."
    }


def descrever_status_treinamento():
    memory = load_seraphine_memory()
    completed = memory.get("training_progress", {}).get("completed_levels", [])
    intent_examples = memory.get("intent_examples", {})
    total_examples = sum(len(item) for item in intent_examples.values())
    if not completed:
        return "Ainda não iniciei o treinamento local."
    return (
        f"Meu treinamento local já passou pelos níveis: {', '.join(completed)}. "
        f"Tenho {len(intent_examples)} intenção(ões) com {total_examples} exemplo(s) aprendidos."
    )


def inferir_intencao_treinada(command):
    memory = load_seraphine_memory()
    normalized_command = normalize_text(command)
    tokens = set(normalized_command.split())
    best_intent = ""
    best_score = 0.0

    for intent, phrases in memory.get("intent_examples", {}).items():
        for phrase in phrases:
            phrase_tokens = set(phrase.split())
            if not phrase_tokens:
                continue

            overlap = len(tokens.intersection(phrase_tokens)) / len(phrase_tokens)
            if normalized_command == phrase:
                overlap += 0.7
            elif phrase in normalized_command or normalized_command in phrase:
                overlap += 0.35

            if overlap > best_score:
                best_score = overlap
                best_intent = intent

    if best_score >= 0.6:
        return best_intent
    return ""


def _match_target(target, candidate):
    normalized_target = normalize_text(target)
    normalized_candidate = normalize_text(candidate)
    if not normalized_target or not normalized_candidate:
        return False
    if normalized_target == normalized_candidate:
        return True
    if len(normalized_target) >= 4 and normalized_target in normalized_candidate:
        return True
    if len(normalized_candidate) >= 4 and normalized_candidate in normalized_target:
        return True
    return False


def _remove_leading_terms(text, terms):
    result = text.strip()
    changed = True
    while changed and result:
        changed = False
        for term in terms:
            prefix = f"{term} "
            if result.startswith(prefix):
                result = result[len(prefix):].strip()
                changed = True
    return result


def _known_app_candidates():
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

    return {
        "google chrome": [
            os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe")
        ],
        "chrome": [
            os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe")
        ],
        "microsoft edge": [
            os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe")
        ],
        "edge": [
            os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe")
        ],
        "visual studio code": [
            os.path.join(local_app_data, "Programs", "Microsoft VS Code", "Code.exe"),
            os.path.join(program_files, "Microsoft VS Code", "Code.exe")
        ],
        "vs code": [
            os.path.join(local_app_data, "Programs", "Microsoft VS Code", "Code.exe"),
            os.path.join(program_files, "Microsoft VS Code", "Code.exe")
        ],
        "spotify": [
            os.path.join(local_app_data, "Microsoft", "WindowsApps", "Spotify.exe"),
            os.path.join(local_app_data, "Spotify", "Spotify.exe")
        ],
        "discord": [
            os.path.join(local_app_data, "Discord", "Update.exe")
        ],
        "steam": [
            os.path.join(program_files_x86, "Steam", "Steam.exe"),
            os.path.join(program_files, "Steam", "Steam.exe")
        ],
        "notepad": [
            r"C:\Windows\System32\notepad.exe"
        ],
        "bloco de notas": [
            r"C:\Windows\System32\notepad.exe"
        ],
        "calculadora": [
            r"C:\Windows\System32\calc.exe"
        ],
        "explorador de arquivos": [
            r"C:\Windows\explorer.exe"
        ],
        "explorer": [
            r"C:\Windows\explorer.exe"
        ]
    }


def _common_shortcut_dirs():
    paths = [
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.environ.get("PUBLIC", r"C:\Users\Public"), "Desktop")
    ]
    return [path for path in paths if path and os.path.exists(path)]


def _find_known_local_app(target):
    for alias, candidates in _known_app_candidates().items():
        if not _match_target(target, alias):
            continue

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
    return ""


def _find_shortcut(target):
    normalized_target = normalize_text(target)
    for directory in _common_shortcut_dirs():
        for root, _, files in os.walk(directory):
            for file_name in files:
                if not file_name.lower().endswith((".lnk", ".url", ".exe")):
                    continue

                stem = os.path.splitext(file_name)[0]
                if _match_target(normalized_target, stem):
                    return os.path.join(root, file_name)
    return ""


def _resolve_known_site(target):
    for alias, url in _default_sites().items():
        if _match_target(target, alias):
            return url
    return ""


def _open_resource(resource):
    try:
        if resource.startswith(("http://", "https://")):
            webbrowser.open(resource, new=2)
        else:
            os.startfile(resource)
        return True
    except OSError:
        return False


def abrir_destino(target):
    cleaned_target = _remove_leading_terms(
        normalize_text(target),
        ["o", "a", "os", "as", "site", "app", "aplicativo", "programa", "pagina"]
    )
    if not cleaned_target:
        return {
            "success": False,
            "message": "Não consegui identificar o que você quer abrir."
        }

    memory = load_seraphine_memory()
    learned = memory["learned_targets"].get(cleaned_target)
    if learned and _open_resource(learned.get("value", "")):
        return {
            "success": True,
            "message": f"Abrindo {cleaned_target} pelo caminho aprendido.",
            "resource": learned.get("value", ""),
            "resource_type": learned.get("type", "learned")
        }

    local_app = _find_known_local_app(cleaned_target)
    if local_app and _open_resource(local_app):
        remember_target(cleaned_target, "local_app", local_app)
        return {
            "success": True,
            "message": f"Encontrei {cleaned_target} no seu computador e já abri.",
            "resource": local_app,
            "resource_type": "local_app"
        }

    shortcut = _find_shortcut(cleaned_target)
    if shortcut and _open_resource(shortcut):
        remember_target(cleaned_target, "shortcut", shortcut)
        return {
            "success": True,
            "message": f"Encontrei um atalho local para {cleaned_target} e já abri.",
            "resource": shortcut,
            "resource_type": "shortcut"
        }

    known_site = _resolve_known_site(cleaned_target)
    if known_site and _open_resource(known_site):
        remember_target(cleaned_target, "site", known_site)
        return {
            "success": True,
            "message": f"Não achei {cleaned_target} instalado, então abri o site oficial.",
            "resource": known_site,
            "resource_type": "site"
        }

    search_url = f"https://www.google.com/search?q={quote(cleaned_target)}"
    if _open_resource(search_url):
        return {
            "success": True,
            "message": f"Não achei {cleaned_target} localmente. Abri uma busca no Google para continuar.",
            "resource": search_url,
            "resource_type": "search"
        }

    return {
        "success": False,
        "message": f"Não consegui abrir {cleaned_target}."
    }


def executar_rotina(nome):
    cleaned_name = _remove_leading_terms(
        normalize_text(nome),
        ["de", "do", "da", "modo", "rotina"]
    )
    memory = load_seraphine_memory()
    routines = memory.get("routines", _default_routines())

    selected_name = ""
    for routine_name in routines:
        if _match_target(cleaned_name, routine_name):
            selected_name = routine_name
            break

    if not selected_name:
        return {
            "success": False,
            "message": "Não encontrei essa rotina. As rotinas prontas são trabalho, estudo, desenvolvimento e pesquisa.",
            "results": []
        }

    results = []
    for target in routines[selected_name]:
        results.append(abrir_destino(target))

    success_count = len([item for item in results if item.get("success")])
    if success_count == 0:
        return {
            "success": False,
            "message": f"Tentei executar a rotina {selected_name}, mas nada foi aberto.",
            "results": results
        }

    return {
        "success": True,
        "message": f"Rotina {selected_name} executada com {success_count} abertura(s) concluída(s).",
        "results": results
    }


def descrever_nucleo():
    memory = load_seraphine_memory()
    routines = ", ".join(sorted(memory.get("routines", {}).keys()))
    return f"Posso abrir aplicativos e sites, procurar alvos no computador, cair para a web quando não encontro localmente e executar rotinas como: {routines}."

def get_weather(location):
    api_key = ""  # Sua chave de API aqui
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



def _adicionar_resultado(resultados, vistos, title, link, snippet, source):
    if not link or link in vistos:
        return

    snippet_limpo = re.sub(r'\s+', ' ', (snippet or "")).strip()
    resultados.append({
        "title": title or "Resultado sem título",
        "link": link,
        "snippet": snippet_limpo,
        "source": source
    })
    vistos.add(link)


def _buscar_wikipedia(query):
    headers = {"User-Agent": "SeraphineAssistant/1.0"}

    try:
        response = requests.get(
            "https://pt.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1
            },
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        search_results = response.json().get("query", {}).get("search", [])
        if not search_results:
            return []

        titulo = search_results[0].get("title")
        if not titulo:
            return []

        resumo = requests.get(
            f"https://pt.wikipedia.org/api/rest_v1/page/summary/{quote(titulo.replace(' ', '_'))}",
            headers=headers,
            timeout=10
        )
        resumo.raise_for_status()
        data = resumo.json()
        link = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        snippet = data.get("extract", "")

        if not snippet:
            return []

        return [{
            "title": titulo,
            "link": link,
            "snippet": snippet,
            "source": "wikipedia"
        }]
    except requests.RequestException:
        return []


def _expandir_topicos_duckduckgo(topicos):
    itens = []
    for topico in topicos:
        if isinstance(topico, dict) and "Topics" in topico:
            itens.extend(_expandir_topicos_duckduckgo(topico.get("Topics", [])))
        else:
            itens.append(topico)
    return itens


def _buscar_duckduckgo(query, limite=5):
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
                "kl": "br-pt"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return []

    resultados = []
    vistos = set()

    if data.get("AbstractText"):
        _adicionar_resultado(
            resultados,
            vistos,
            data.get("Heading") or query,
            data.get("AbstractURL") or f"https://duckduckgo.com/?q={quote(query)}",
            data.get("AbstractText"),
            "duckduckgo"
        )

    for item in _expandir_topicos_duckduckgo(data.get("RelatedTopics", [])):
        if len(resultados) >= limite:
            break
        if not isinstance(item, dict):
            continue
        titulo = item.get("Text", "").split(" - ")[0]
        _adicionar_resultado(
            resultados,
            vistos,
            titulo,
            item.get("FirstURL", ""),
            item.get("Text", ""),
            "duckduckgo"
        )

    return resultados[:limite]


def pesquisar_no_google(query, limite=5):
    resultados = []
    vistos = set()

    for item in _buscar_wikipedia(query):
        _adicionar_resultado(
            resultados,
            vistos,
            item.get("title"),
            item.get("link"),
            item.get("snippet"),
            item.get("source")
        )

    for item in _buscar_duckduckgo(query, limite=limite):
        _adicionar_resultado(
            resultados,
            vistos,
            item.get("title"),
            item.get("link"),
            item.get("snippet"),
            item.get("source")
        )

    return resultados[:limite]


def responder_com_base_na_internet(query, limite=3):
    resultados = pesquisar_no_google(query, limite=limite)
    if not resultados:
        return "Não encontrei uma resposta confiável na internet para esse pedido agora.", []

    resumos = []
    for item in resultados:
        snippet = item.get("snippet", "").strip()
        if snippet and snippet not in resumos:
            resumos.append(snippet)
        if len(resumos) == 2:
            break

    if not resumos:
        resposta = f"Encontrei resultados sobre {query}, mas sem um resumo claro para te responder agora."
    elif len(resumos) == 1:
        resposta = resumos[0]
    else:
        resposta = f"{resumos[0]} Também encontrei isto: {resumos[1]}"

    return resposta[:500], resultados
    

##filmes

def obter_filmes_populares(numero_filmes=5):
    api_key = ""#sua chave API aqui
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


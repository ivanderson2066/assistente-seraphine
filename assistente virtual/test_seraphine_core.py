import unittest
from unittest.mock import patch

from funcoes import abrir_destino, executar_rotina, normalize_text, registrar_interacao, resumo_aprendizado, explicar_como_aprende_programacao, explicar_onde_aprende_a_se_programar, gerar_propostas_de_autoaprimoramento, treinar_comandos_localmente, inferir_intencao_treinada, descrever_status_treinamento
from main import SeraphineCore


class SeraphineCoreTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.training_patch = patch("main.preparar_base_de_treinamento", return_value={"message": "ok"})
        self.training_patch.start()
        self.core = SeraphineCore(self.messages.append)

    def tearDown(self):
        self.training_patch.stop()

    def test_detect_intent_for_open_command(self):
        self.assertEqual(self.core.detect_intent("abrir youtube"), "open")

    def test_detect_intent_for_routine_command(self):
        self.assertEqual(self.core.detect_intent("modo trabalho"), "routine")

    def test_detect_intent_for_search_command(self):
        self.assertEqual(self.core.detect_intent("quem é alan turing"), "search")

    def test_detect_intent_for_positive_feedback(self):
        self.assertEqual(self.core.detect_intent("deu certo"), "positive_feedback")

    def test_detect_intent_for_self_review(self):
        self.assertEqual(self.core.detect_intent("como voce esta evoluindo"), "self_review")

    def test_detect_intent_for_coding_learning(self):
        self.assertEqual(self.core.detect_intent("como aprender a se programar"), "coding_learning")

    def test_detect_intent_for_coding_source(self):
        self.assertEqual(self.core.detect_intent("onde voce aprende a se programar"), "coding_source")

    @patch("main.inferir_intencao_treinada", return_value="training_status")
    def test_detect_intent_uses_trained_examples(self, trained_mock):
        self.assertEqual(self.core.detect_intent("status do treinamento"), "training_status")
        trained_mock.assert_called_once()

    def test_extract_open_target_removes_prefix(self):
        self.assertEqual(self.core.extract_open_target("abrir o youtube"), "o youtube")

    def test_extract_routine_name(self):
        self.assertEqual(self.core.extract_routine_name("executar rotina de trabalho"), "trabalho")

    def test_normalize_text_removes_accents(self):
        self.assertEqual(normalize_text("Computação Ágil"), "computacao agil")

    @patch("main.registrar_feedback", return_value="aprendi")
    def test_process_feedback_speaks_result(self, registrar_feedback_mock):
        result = self.core.process_feedback("deu certo", positive=True)

        self.assertEqual(result, "aprendi")
        self.assertEqual(self.messages[-1], "aprendi")
        registrar_feedback_mock.assert_called_once_with("deu certo", positive=True)

    @patch("main.gerar_autoavaliacao", return_value={"summary": "estou evoluindo", "suggestions": ["continuar"]})
    def test_reflect_on_progress(self, gerar_autoavaliacao_mock):
        reflection = self.core.reflect_on_progress()

        self.assertEqual(reflection["summary"], "estou evoluindo")
        self.assertEqual(self.messages[-1], "estou evoluindo")
        gerar_autoavaliacao_mock.assert_called_once()

    @patch("main.explicar_como_aprende_programacao", return_value="aprendo lendo o projeto")
    def test_explain_coding_learning(self, explain_mock):
        summary = self.core.explain_coding_learning()

        self.assertEqual(summary, "aprendo lendo o projeto")
        self.assertEqual(self.messages[-1], "aprendo lendo o projeto")
        explain_mock.assert_called_once()

    @patch("main.gerar_propostas_de_autoaprimoramento", return_value={"proposals": ["melhoria 1", "melhoria 2", "melhoria 3"]})
    def test_propose_code_improvements(self, propose_mock):
        payload = self.core.propose_code_improvements()

        self.assertEqual(payload["proposals"][0], "melhoria 1")
        self.assertIn("melhoria 1", self.messages[-1])
        propose_mock.assert_called_once()

    @patch("main.preparar_base_de_treinamento", return_value={"message": "treinamento iniciado"})
    def test_bootstrap_training(self, bootstrap_mock):
        summary = self.core.bootstrap_training()

        self.assertEqual(summary["message"], "treinamento iniciado")
        self.assertEqual(self.messages[-1], "treinamento iniciado")
        bootstrap_mock.assert_called_once()

    @patch("main.avancar_treinamento_local", return_value={"message": "nivel intermediate concluido"})
    def test_advance_training(self, advance_mock):
        summary = self.core.advance_training()

        self.assertEqual(summary["message"], "nivel intermediate concluido")
        self.assertEqual(self.messages[-1], "nivel intermediate concluido")
        advance_mock.assert_called_once()

    @patch("main.descrever_status_treinamento", return_value="treinamento basico concluido")
    def test_describe_training(self, describe_mock):
        summary = self.core.describe_training()

        self.assertEqual(summary, "treinamento basico concluido")
        self.assertEqual(self.messages[-1], "treinamento basico concluido")
        describe_mock.assert_called_once()

    @patch("funcoes._open_resource", return_value=True)
    @patch("funcoes._find_known_local_app", return_value=r"C:\Apps\Code.exe")
    @patch("funcoes.remember_target")
    def test_abrir_destino_prefers_local_app(self, remember_target, find_local, open_resource):
        result = abrir_destino("visual studio code")

        self.assertTrue(result["success"])
        self.assertEqual(result["resource_type"], "local_app")
        remember_target.assert_called_once()
        open_resource.assert_called_once_with(r"C:\Apps\Code.exe")
        find_local.assert_called_once()

    @patch("funcoes._open_resource", return_value=True)
    @patch("funcoes._find_known_local_app", return_value="")
    @patch("funcoes._find_shortcut", return_value="")
    def test_abrir_destino_uses_known_site_when_local_not_found(self, find_shortcut, find_local, open_resource):
        result = abrir_destino("youtube")

        self.assertTrue(result["success"])
        self.assertEqual(result["resource_type"], "site")
        self.assertEqual(result["resource"], "https://www.youtube.com")
        open_resource.assert_called_once_with("https://www.youtube.com")

    @patch("funcoes.abrir_destino")
    def test_executar_rotina_runs_all_targets(self, abrir):
        abrir.side_effect = [
            {"success": True, "message": "ok 1"},
            {"success": True, "message": "ok 2"},
            {"success": True, "message": "ok 3"},
            {"success": True, "message": "ok 4"},
        ]

        result = executar_rotina("trabalho")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 4)
        self.assertIn("executada", result["message"])
        self.assertEqual(abrir.call_count, 4)

    @patch("funcoes.save_seraphine_memory")
    @patch("funcoes.load_seraphine_memory")
    def test_registrar_interacao_updates_action_stats(self, load_memory_mock, save_memory_mock):
        memory = {
            "learned_targets": {},
            "routines": {},
            "interactions": [],
            "action_stats": {},
            "reflections": [],
            "coding_knowledge": {},
            "rewrite_proposals": [],
            "training_sources": [],
            "intent_examples": {},
            "training_progress": {"completed_levels": []}
        }
        load_memory_mock.return_value = memory

        registrar_interacao("abrir youtube", "open", "open", "youtube", True, "ok")

        self.assertEqual(memory["interactions"][-1]["intent"], "open")
        self.assertEqual(memory["action_stats"]["open"]["successes"], 1)
        save_memory_mock.assert_called_once()

    @patch("funcoes.load_seraphine_memory")
    def test_resumo_aprendizado(self, load_memory_mock):
        load_memory_mock.return_value = {
            "learned_targets": {
                "youtube": {"successes": 3, "failures": 0}
            },
            "routines": {},
            "interactions": [{"success": True}, {"success": False}],
            "action_stats": {},
            "reflections": [{"summary": "x"}],
            "coding_knowledge": {},
            "rewrite_proposals": [],
            "training_sources": [],
            "intent_examples": {},
            "training_progress": {"completed_levels": []}
        }

        summary = resumo_aprendizado()

        self.assertIn("2 interações", summary)
        self.assertIn("1 autoavaliações", summary)
        self.assertIn("youtube", summary)

    @patch("funcoes.aprender_sintaxe_local", return_value={
        "files_analyzed": 3,
        "total_functions": 10,
        "total_classes": 2,
        "total_imports": 5,
        "syntax_errors": 0
    })
    def test_explicar_como_aprende_programacao(self, aprender_mock):
        summary = explicar_como_aprende_programacao()

        self.assertIn("analisei 3 arquivo", summary)
        self.assertIn("10 função", summary)
        aprender_mock.assert_called_once()

    @patch("funcoes.gerar_propostas_de_autoaprimoramento", return_value={"proposals": ["criar uma camada de propostas de código"]})
    def test_explicar_onde_aprende_a_se_programar(self, gerar_mock):
        summary = explicar_onde_aprende_a_se_programar()

        self.assertIn("próximo passo seguro", summary)
        gerar_mock.assert_called_once()

    @patch("funcoes.save_seraphine_memory")
    @patch("funcoes.load_seraphine_memory")
    def test_treinar_comandos_localmente(self, load_memory_mock, save_memory_mock):
        memory = {
            "learned_targets": {},
            "routines": {},
            "interactions": [],
            "action_stats": {},
            "reflections": [],
            "coding_knowledge": {},
            "rewrite_proposals": [],
            "training_sources": [],
            "intent_examples": {},
            "training_progress": {"completed_levels": []}
        }
        load_memory_mock.return_value = memory

        result = treinar_comandos_localmente("basic")

        self.assertIn("open", memory["intent_examples"])
        self.assertIn("basic", memory["training_progress"]["completed_levels"])
        self.assertGreater(result["example_count"], 0)
        save_memory_mock.assert_called_once()

    @patch("funcoes.load_seraphine_memory")
    def test_inferir_intencao_treinada(self, load_memory_mock):
        load_memory_mock.return_value = {
            "learned_targets": {},
            "routines": {},
            "interactions": [],
            "action_stats": {},
            "reflections": [],
            "coding_knowledge": {},
            "rewrite_proposals": [],
            "training_sources": [],
            "intent_examples": {
                "open": ["abrir youtube", "abrir google"]
            },
            "training_progress": {"completed_levels": ["basic"]}
        }

        intent = inferir_intencao_treinada("abra o youtube")

        self.assertEqual(intent, "open")

    @patch("funcoes.load_seraphine_memory")
    def test_descrever_status_treinamento(self, load_memory_mock):
        load_memory_mock.return_value = {
            "learned_targets": {},
            "routines": {},
            "interactions": [],
            "action_stats": {},
            "reflections": [],
            "coding_knowledge": {},
            "rewrite_proposals": [],
            "training_sources": [],
            "intent_examples": {
                "open": ["abrir youtube"],
                "search": ["quem e alan turing"]
            },
            "training_progress": {"completed_levels": ["basic", "intermediate"]}
        }

        status = descrever_status_treinamento()

        self.assertIn("basic, intermediate", status)
        self.assertIn("2 intenção", status)


if __name__ == "__main__":
    unittest.main()

"""Tests for LLM agents — LLM client is always mocked so no real API calls are made."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.agents.codegen_agent import CodeGenerationAgent
from app.agents.openspec_agent import OpenSpecAgent, _OpenSpecLLMOutput
from app.agents.requirements_agent import RequirementsAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.main import app
from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile
from app.schemas.idea import IdeaRequest
from app.schemas.requirements import RequirementItem, RequirementsResponse, UserStory

client = TestClient(app)

IDEA = IdeaRequest(
    name="Reservas de clases",
    sector="Educación",
    problem="Gestionar reservas de clases particulares de forma manual",
    target_users="Academias y profesores particulares",
    core_features=["CRUD de profesores", "Reserva de clases"],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
)

IDEA_FEW_FEATURES = IdeaRequest(
    name="App simple",
    sector="Tech",
    problem="Problema que tiene al menos diez caracteres",
    target_users="Usuarios",
    core_features=["Solo una cosa"],
)

MOCK_REQUIREMENTS = RequirementsResponse(
    project_name="Reservas de clases",
    functional_requirements=[
        RequirementItem(id="RF-001", title="CRUD de profesores", description="Gestionar profesores."),
        RequirementItem(id="RF-002", title="Reserva de clases", description="Gestionar reservas."),
    ],
    non_functional_requirements=[
        RequirementItem(id="RNF-001", title="Seguridad", description="Proteger rutas privadas."),
    ],
    user_stories=[
        UserStory(id="US-001", actor="Profesor", goal="gestionar su agenda", benefit="ahorrar tiempo"),
    ],
)

MOCK_OPENSPEC_OUTPUT = _OpenSpecLLMOutput(
    project={"name": "Reservas de clases", "sector": "Educación", "targetUsers": "Academias"},
    requirements=[{"id": "RF-001", "title": "CRUD de profesores", "description": "Gestionar."}],
    constraints={"stack": ["React", "NestJS"], "delivery": "Docker"},
    modules=["Auth", "Profesores", "Reservas"],
)


# ── RequirementsAgent ─────────────────────────────────────────────────────────

class TestRequirementsAgent:
    def test_uses_llm_when_available(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = MOCK_REQUIREMENTS

        result = RequirementsAgent().generate(IDEA, llm=mock_llm)

        mock_llm.with_structured_output.assert_called_once_with(RequirementsResponse)
        assert result.project_name == "Reservas de clases"
        assert len(result.functional_requirements) == 2

    def test_falls_back_to_deterministic_when_llm_raises(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.side_effect = RuntimeError("LLM unreachable")

        result = RequirementsAgent().generate(IDEA, llm=mock_llm)

        # Should still return a valid response via fallback
        assert result.project_name == "Reservas de clases"
        assert len(result.functional_requirements) >= len(IDEA.core_features)

    def test_falls_back_when_no_llm(self) -> None:
        with patch("app.agents.requirements_agent.get_llm", return_value=None):
            result = RequirementsAgent().generate(IDEA)

        assert result.project_name == IDEA.name
        # Fallback generates one req per feature + auth + admin
        assert any(r.title == "Autenticación de usuarios" for r in result.functional_requirements)
        assert any(r.title == "Panel de administración" for r in result.functional_requirements)

    def test_deterministic_skips_auth_when_not_needed(self) -> None:
        idea_no_auth = IDEA.model_copy(update={"needs_auth": False, "needs_admin_panel": False})
        with patch("app.agents.requirements_agent.get_llm", return_value=None):
            result = RequirementsAgent().generate(idea_no_auth)

        titles = [r.title for r in result.functional_requirements]
        assert "Autenticación de usuarios" not in titles
        assert "Panel de administración" not in titles


# ── OpenSpecAgent ─────────────────────────────────────────────────────────────

class TestOpenSpecAgent:
    def test_uses_llm_when_available(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = MOCK_OPENSPEC_OUTPUT

        result = OpenSpecAgent().generate(IDEA, MOCK_REQUIREMENTS, llm=mock_llm)

        assert result.project_name == IDEA.name
        assert "project" in result.spec
        assert result.spec["modules"] == ["Auth", "Profesores", "Reservas"]

    def test_falls_back_when_llm_raises(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.side_effect = RuntimeError("timeout")

        result = OpenSpecAgent().generate(IDEA, MOCK_REQUIREMENTS, llm=mock_llm)

        assert result.project_name == IDEA.name
        assert "requirements" in result.spec

    def test_deterministic_includes_all_requirements(self) -> None:
        with patch("app.agents.openspec_agent.get_llm", return_value=None):
            result = OpenSpecAgent().generate(IDEA, MOCK_REQUIREMENTS)

        assert len(result.spec["requirements"]) == len(MOCK_REQUIREMENTS.functional_requirements)


# ── SupervisorAgent ───────────────────────────────────────────────────────────

class TestSupervisorAgent:
    def _mock_llm(self) -> MagicMock:
        mock_llm = MagicMock()
        req_structured = MagicMock()
        req_structured.invoke.return_value = MOCK_REQUIREMENTS
        spec_structured = MagicMock()
        spec_structured.invoke.return_value = MOCK_OPENSPEC_OUTPUT
        mock_llm.with_structured_output.side_effect = [req_structured, spec_structured]
        return mock_llm

    def test_full_pipeline_with_llm(self) -> None:
        result = SupervisorAgent().run(IDEA, llm=self._mock_llm())

        assert result["decision"] == "generate_requirements"
        assert result["requirements"] is not None
        assert result["openspec"] is not None
        assert result["openspec"].project_name == IDEA.name

    def test_asks_more_when_too_few_features(self) -> None:
        result = SupervisorAgent().run(IDEA_FEW_FEATURES, llm=MagicMock())

        assert result["decision"] == "ask_more_questions"
        assert result["openspec"] is None

    def test_pipeline_without_llm_uses_deterministic(self) -> None:
        with patch("app.agents.requirements_agent.get_llm", return_value=None), \
             patch("app.agents.openspec_agent.get_llm", return_value=None):
            result = SupervisorAgent().run(IDEA, llm=None)

        assert result["decision"] == "generate_requirements"
        assert result["openspec"] is not None


# ── HTTP endpoints ────────────────────────────────────────────────────────────

class TestGenerateOpenSpecEndpoint:
    def test_returns_openspec_with_mocked_llm(self) -> None:
        mock_llm = MagicMock()
        req_structured = MagicMock()
        req_structured.invoke.return_value = MOCK_REQUIREMENTS
        spec_structured = MagicMock()
        spec_structured.invoke.return_value = MOCK_OPENSPEC_OUTPUT
        mock_llm.with_structured_output.side_effect = [req_structured, spec_structured]

        with patch("app.agents.requirements_agent.get_llm", return_value=mock_llm), \
             patch("app.agents.openspec_agent.get_llm", return_value=mock_llm):
            response = client.post("/generate-openspec", json=IDEA.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert body["project_name"] == IDEA.name
        assert "spec" in body

    def test_returns_422_for_too_few_features(self) -> None:
        response = client.post("/generate-openspec", json=IDEA_FEW_FEATURES.model_dump())
        assert response.status_code == 422

    def test_generate_requirements_deterministic(self) -> None:
        with patch("app.agents.requirements_agent.get_llm", return_value=None):
            response = client.post("/generate-requirements", json=IDEA.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert body["project_name"] == IDEA.name
        assert len(body["functional_requirements"]) >= 2


CODEGEN_REQUEST = CodeGenerationRequest(
    project_name="Reservas de clases",
    sector="Educación",
    modules=["Auth", "Profesores", "Reservas"],
    requirements=[{"id": "RF-001", "title": "CRUD de profesores", "description": "Gestionar."}],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    stack=["React", "NestJS", "PostgreSQL", "Docker"],
)

MOCK_CODEGEN_RESPONSE = CodeGenerationResponse(
    project_name="Reservas de clases",
    files=[
        GeneratedFile(path="docker-compose.yml", language="yaml", content="services: {}"),
        GeneratedFile(path="README.md", language="markdown", content="# Reservas"),
        GeneratedFile(path="apps/api/src/app.module.ts", language="typescript", content="// app"),
    ],
)


# ── CodeGenerationAgent ───────────────────────────────────────────────────────

class TestCodeGenerationAgent:
    def test_uses_llm_when_available(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = MOCK_CODEGEN_RESPONSE

        result = CodeGenerationAgent().generate(CODEGEN_REQUEST, llm=mock_llm)

        mock_llm.with_structured_output.assert_called_once_with(CodeGenerationResponse)
        assert result.project_name == "Reservas de clases"
        assert len(result.files) == 3

    def test_falls_back_when_llm_raises(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.side_effect = RuntimeError("LLM timeout")

        result = CodeGenerationAgent().generate(CODEGEN_REQUEST, llm=mock_llm)

        assert result.project_name == "Reservas de clases"
        assert any(f.path == "docker-compose.yml" for f in result.files)
        assert any(f.path == "README.md" for f in result.files)

    def test_falls_back_when_no_llm(self) -> None:
        with patch("app.agents.codegen_agent.get_llm", return_value=None):
            result = CodeGenerationAgent().generate(CODEGEN_REQUEST)

        assert result.project_name == CODEGEN_REQUEST.project_name
        paths = [f.path for f in result.files]
        assert "docker-compose.yml" in paths
        assert "README.md" in paths
        assert "apps/api/src/app.module.ts" in paths
        assert "apps/api/prisma/schema.prisma" in paths

    def test_fallback_includes_auth_model_when_needed(self) -> None:
        with patch("app.agents.codegen_agent.get_llm", return_value=None):
            result = CodeGenerationAgent().generate(CODEGEN_REQUEST)

        schema_file = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model User" in schema_file.content

    def test_fallback_skips_auth_model_when_not_needed(self) -> None:
        req_no_auth = CODEGEN_REQUEST.model_copy(update={"needs_auth": False})
        with patch("app.agents.codegen_agent.get_llm", return_value=None):
            result = CodeGenerationAgent().generate(req_no_auth)

        schema_file = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model User" not in schema_file.content

    def test_endpoint_returns_generated_files(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = MOCK_CODEGEN_RESPONSE

        with patch("app.agents.codegen_agent.get_llm", return_value=mock_llm):
            response = client.post("/generate-code", json=CODEGEN_REQUEST.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert body["project_name"] == "Reservas de clases"
        assert len(body["files"]) == 3
        assert all("path" in f and "content" in f for f in body["files"])

    def test_endpoint_fallback_without_llm(self) -> None:
        with patch("app.agents.codegen_agent.get_llm", return_value=None):
            response = client.post("/generate-code", json=CODEGEN_REQUEST.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert len(body["files"]) >= 5

"""Tests for LLM agents — LLM client is always mocked so no real API calls are made."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.agents.architecture_agent import ArchitectureAgent
from app.agents.codegen_agent import CodeGenerationAgent
from app.agents.issue_generator_agent import IssueGeneratorAgent
from app.agents.openspec_agent import OpenSpecAgent, _OpenSpecLLMOutput
from app.agents.requirements_agent import RequirementsAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.tech_proposal_agent import (
    TechProposalAgent,
    _catalog_key,
    _django_is_justified,
)
from app.agents.fallback.shared.prisma import generate_prisma_schema
from app.agents.tutorial_agent import TutorialAgent
from app.main import app
from app.schemas.architecture import ArchitectureRequest
from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse, GeneratedFile
from app.schemas.idea import IdeaRequest
from app.schemas.issues import IssueGenerationRequest
from app.schemas.requirements import RequirementItem, RequirementsResponse, UserStory
from app.schemas.tutorial import TutorialRequest

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
    project_description="Sistema de reservas de clases para academias y profesores particulares.",
    requirements=[{"id": "RF-001", "title": "CRUD de profesores", "description": "Gestionar profesores.", "acceptance_criteria": ["El endpoint /profesores funciona."]}],
    user_stories=[{"id": "US-001", "actor": "Profesor", "goal": "gestionar su agenda", "benefit": "ahorrar tiempo"}],
    modules=["Auth", "Profesores", "Reservas"],
    milestones=[
        "Milestone 1: Setup y arquitectura",
        "Milestone 2: Modelos y base de datos",
        "Milestone 3: API y lógica de negocio",
        "Milestone 4: Frontend y UX",
        "Milestone 5: Testing y despliegue",
    ],
    delivery="MVP dockerizado",
    environments=["desarrollo", "producción"],
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
    def test_entity_names_ignore_generic_verbs_and_accents(self) -> None:
        assert OpenSpecAgent._entity_name_from_feature("Gestión de aulas") == "Aulas"
        assert OpenSpecAgent._entity_name_from_feature("Reserva de tutorías") == "ReservaTutorias"

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

    def test_deterministic_data_model_has_professional_constraints(self) -> None:
        with patch("app.agents.openspec_agent.get_llm", return_value=None):
            result = OpenSpecAgent().generate(IDEA, MOCK_REQUIREMENTS)

        data_model = result.spec["data_model"]
        entities = result.spec["data_entities"]
        domain_entity = next(
            entity for entity in entities
            if any(field.startswith("status:") for field in entity["fields"])
            and any(field.startswith("user_id:") for field in entity["fields"])
        )
        entity_names = {entity["name"] for entity in entities}

        assert {"User", "Role", "UserRole", "RefreshToken", "AuditLog"}.issubset(entity_names)
        assert data_model["relationships"]
        assert any("user_status" in index for index in data_model["indexes"])
        assert any("uq_user_roles_user_role" in index for index in data_model["indexes"])
        assert any("refresh_tokens_hash" in index for index in data_model["indexes"])
        assert data_model["constraints"]
        assert data_model["naming_conventions"]
        assert data_model["migration_strategy"]
        assert any(field.startswith("version:") for field in domain_entity["fields"])
        assert any(field.startswith("updated_at:") for field in domain_entity["fields"])
        assert any(field.startswith("deleted_at:") for field in domain_entity["fields"])
        assert any(field.startswith("metadata:") for field in domain_entity["fields"])


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
        assert result["product_analysis"] is not None
        assert "summary" in result["product_analysis"]
        assert result["requirements"] is not None
        assert result["openspec"] is not None
        assert result["openspec"].project_name == IDEA.name

    def test_asks_more_when_too_few_features(self) -> None:
        result = SupervisorAgent().run(IDEA_FEW_FEATURES, llm=MagicMock())

        assert result["decision"] == "ask_more_questions"
        assert result["product_analysis"] is None
        assert result["openspec"] is None

    def test_pipeline_without_llm_uses_deterministic(self) -> None:
        with patch("app.agents.requirements_agent.get_llm", return_value=None), \
             patch("app.agents.openspec_agent.get_llm", return_value=None):
            result = SupervisorAgent().run(IDEA, llm=None)

        assert result["decision"] == "generate_requirements"
        assert result["product_analysis"] is not None
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

# Neutral sector that doesn't trigger any sector template (uses generic DDD scaffold)
CODEGEN_REQUEST_NEUTRAL = CODEGEN_REQUEST.model_copy(update={"sector": "Gestión de proyectos"})

MOCK_CODEGEN_RESPONSE = CodeGenerationResponse(
    project_name="Reservas de clases",
    files=[
        GeneratedFile(path="docker-compose.yml", language="yaml", content="services: {}"),
        GeneratedFile(path="README.md", language="markdown", content="# Reservas"),
        GeneratedFile(path="apps/api/src/app.module.ts", language="typescript", content="// app"),
    ],
)


# ── IssueGeneratorAgent ───────────────────────────────────────────────────────

ISSUE_REQUEST_NESTJS = IssueGenerationRequest(
    project_name="Reservas de clases",
    sector="Educación",
    openspec={
        "requirements": [
            {"id": "RF-001", "title": "CRUD de profesores", "description": "Gestionar profesores.", "acceptance_criteria": ["Endpoint /profesores funciona"]},
            {"id": "RF-002", "title": "Reserva de clases", "description": "Gestionar reservas.", "acceptance_criteria": ["El alumno puede reservar"]},
        ],
        "user_stories": [
            {"id": "US-001", "actor": "Profesor", "goal": "gestionar su agenda", "benefit": "ahorrar tiempo"},
        ],
        "modules": ["Auth", "Profesores", "Reservas", "Calendario"],
        "milestones": [
            "Milestone 1: Setup y arquitectura",
            "Milestone 2: Modelos y base de datos",
            "Milestone 3: API y lógica de negocio",
            "Milestone 4: Frontend y UX",
            "Milestone 5: Testing y despliegue",
        ],
        "architecture": {"type": "NESTJS_REACT"},
    },
)

ISSUE_REQUEST_DJANGO = ISSUE_REQUEST_NESTJS.model_copy(
    update={"openspec": {**ISSUE_REQUEST_NESTJS.openspec, "architecture": {"type": "DJANGO_REST"}}}
)

ISSUE_REQUEST_LARAVEL = ISSUE_REQUEST_NESTJS.model_copy(
    update={"openspec": {**ISSUE_REQUEST_NESTJS.openspec, "architecture": {"type": "LARAVEL_MONOLITH"}}}
)


class TestIssueGeneratorAgent:
    def test_deterministic_returns_issues(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            result = IssueGeneratorAgent().generate(ISSUE_REQUEST_NESTJS)

        assert result.project_name == "Reservas de clases"
        assert result.total == len(result.issues)
        assert result.total >= 5

    def test_issues_have_required_fields(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            result = IssueGeneratorAgent().generate(ISSUE_REQUEST_NESTJS)

        for issue in result.issues:
            assert issue.title, "Issue title must not be empty"
            assert issue.body, "Issue body must not be empty"
            assert issue.priority in {"high", "medium", "low"}, f"Invalid priority: {issue.priority}"
            assert isinstance(issue.labels, list)

    def test_requirements_become_issues(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            result = IssueGeneratorAgent().generate(ISSUE_REQUEST_NESTJS)

        titles = [i.title for i in result.issues]
        assert any("RF-001" in t or "CRUD de profesores" in t for t in titles)

    def test_milestones_are_propagated(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            result = IssueGeneratorAgent().generate(ISSUE_REQUEST_NESTJS)

        assert len(result.milestones) >= 3
        assert any("Setup" in m or "arquitectura" in m for m in result.milestones)

    def test_nestjs_setup_issue_is_generated(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            result = IssueGeneratorAgent().generate(ISSUE_REQUEST_NESTJS)

        titles = [i.title for i in result.issues]
        assert any("NestJS" in t or "Prisma" in t or "módulo" in t.lower() for t in titles)

    def test_django_setup_issue_is_generated(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            result = IssueGeneratorAgent().generate(ISSUE_REQUEST_DJANGO)

        titles = [i.title for i in result.issues]
        assert any("Django" in t or "migración" in t.lower() or "migrate" in t.lower() for t in titles)

    def test_laravel_setup_issue_is_generated(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            result = IssueGeneratorAgent().generate(ISSUE_REQUEST_LARAVEL)

        titles = [i.title for i in result.issues]
        assert any("Laravel" in t or "Eloquent" in t or "Sanctum" in t for t in titles)

    def test_testing_and_deployment_issues_always_present(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            result = IssueGeneratorAgent().generate(ISSUE_REQUEST_NESTJS)

        titles = " ".join(i.title.lower() for i in result.issues)
        assert "test" in titles or "testing" in titles
        assert "docker" in titles or "despliegue" in titles or "deploy" in titles

    def test_endpoint_returns_issues(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            response = client.post("/generate-issues", json=ISSUE_REQUEST_NESTJS.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert body["project_name"] == "Reservas de clases"
        assert body["total"] >= 5
        assert len(body["issues"]) == body["total"]
        assert all(i["title"] for i in body["issues"])

    def test_total_matches_issues_length(self) -> None:
        with patch("app.agents.issue_generator_agent.get_llm", return_value=None):
            result = IssueGeneratorAgent().generate(ISSUE_REQUEST_NESTJS)

        assert result.total == len(result.issues)


# ── CodeGenerationAgent ───────────────────────────────────────────────────────

class TestCodeGenerationAgent:
    def test_uses_llm_when_available(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = MOCK_CODEGEN_RESPONSE

        # Use neutral sector so LLM is not bypassed by a sector template
        result = CodeGenerationAgent().generate(CODEGEN_REQUEST_NEUTRAL, llm=mock_llm)

        mock_llm.with_structured_output.assert_called_once_with(CodeGenerationResponse)
        assert result.project_name == "Reservas de clases"
        paths = {file.path for file in result.files}
        assert {
            "docker-compose.yml",
            "README.md",
            "apps/api/src/app.module.ts",
        } <= paths
        assert "sdd/constitution.md" in paths

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
        # Neutral sector → generic DDD scaffold (tRPC + Prisma)
        with patch("app.agents.codegen_agent.get_llm_candidates", return_value=[]):
            result = CodeGenerationAgent().generate(CODEGEN_REQUEST_NEUTRAL)

        assert result.project_name == CODEGEN_REQUEST_NEUTRAL.project_name
        paths = [f.path for f in result.files]
        assert "docker-compose.yml" in paths
        assert "package.json" in paths
        assert "src/auth/auth.module.ts" in paths
        assert "prisma/schema.prisma" in paths

    def test_fallback_includes_auth_model_when_needed(self) -> None:
        with patch("app.agents.codegen_agent.get_llm_candidates", return_value=[]):
            result = CodeGenerationAgent().generate(CODEGEN_REQUEST)

        schema_file = next(f for f in result.files if f.path == "prisma/schema.prisma")
        assert "model User" in schema_file.content

    def test_fallback_skips_auth_model_when_not_needed(self) -> None:
        req_no_auth = CODEGEN_REQUEST_NEUTRAL.model_copy(update={"needs_auth": False})
        with patch("app.agents.codegen_agent.get_llm_candidates", return_value=[]):
            result = CodeGenerationAgent().generate(req_no_auth)

        schema_file = next(f for f in result.files if f.path == "prisma/schema.prisma")
        assert "model User" not in schema_file.content

    def test_endpoint_returns_generated_files(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = MOCK_CODEGEN_RESPONSE

        # Neutral sector ensures the LLM path is taken (no template bypass)
        with patch("app.agents.codegen_agent.get_llm_candidates", return_value=[mock_llm]):
            response = client.post("/generate-code", json=CODEGEN_REQUEST_NEUTRAL.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert body["project_name"] == "Reservas de clases"
        paths = {file["path"] for file in body["files"]}
        assert {
            "docker-compose.yml",
            "README.md",
            "apps/api/src/app.module.ts",
        } <= paths
        assert "sdd/constitution.md" in paths
        assert all("path" in f and "content" in f for f in body["files"])

    def test_endpoint_fallback_without_llm(self) -> None:
        with patch("app.agents.codegen_agent.get_llm_candidates", return_value=[]):
            response = client.post("/generate-code", json=CODEGEN_REQUEST.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert len(body["files"]) >= 5

    # ── BEGINNER template tests ───────────────────────────────────────────────

    def test_beginner_routes_to_express_template(self) -> None:
        req = CODEGEN_REQUEST_NEUTRAL.model_copy(update={"technical_level": "BEGINNER"})
        result = CodeGenerationAgent().generate(req, llm=None)

        paths = [f.path for f in result.files]
        assert "src/index.ts" in paths
        assert "src/services/prisma.service.ts" in paths
        assert "prisma/schema.prisma" in paths

    def test_beginner_bypasses_sector_templates(self) -> None:
        req = CODEGEN_REQUEST.model_copy(update={"technical_level": "BEGINNER"})
        result = CodeGenerationAgent().generate(req, llm=None)

        paths = [f.path for f in result.files]
        # Should use Express, not academia tRPC template
        assert "src/index.ts" in paths
        assert not any("trpc" in p for p in paths)

    def test_beginner_with_auth_includes_auth_routes(self) -> None:
        req = CODEGEN_REQUEST_NEUTRAL.model_copy(update={"technical_level": "BEGINNER", "needs_auth": True})
        result = CodeGenerationAgent().generate(req, llm=None)

        paths = [f.path for f in result.files]
        assert "src/routes/auth.routes.ts" in paths
        assert "src/middleware/auth.ts" in paths

    def test_beginner_without_auth_excludes_auth_middleware(self) -> None:
        req = CODEGEN_REQUEST_NEUTRAL.model_copy(update={"technical_level": "BEGINNER", "needs_auth": False})
        result = CodeGenerationAgent().generate(req, llm=None)

        paths = [f.path for f in result.files]
        # auth middleware is the definitive signal — only added when needs_auth=True
        assert "src/middleware/auth.ts" not in paths

    def test_intermediate_still_uses_ddd_scaffold(self) -> None:
        req = CODEGEN_REQUEST_NEUTRAL.model_copy(update={"technical_level": "INTERMEDIATE"})
        result = CodeGenerationAgent().generate(req, llm=None)

        paths = [f.path for f in result.files]
        # INTERMEDIATE uses tRPC generic scaffold
        assert any("prisma" in p for p in paths)
        assert "src/index.ts" not in paths

    def test_beginner_no_duplicate_paths(self) -> None:
        req = CODEGEN_REQUEST_NEUTRAL.model_copy(update={"technical_level": "BEGINNER"})
        result = CodeGenerationAgent().generate(req, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), f"Duplicate paths: {[p for p in paths if paths.count(p) > 1]}"


# ── TutorialAgent ─────────────────────────────────────────────────────────────

TUTORIAL_REQUEST_DJANGO = TutorialRequest(
    project_name="Reservas de clases",
    sector="Educación",
    architecture_type="DJANGO_REST",
    stack=["Python", "Django", "PostgreSQL", "Docker"],
    modules=["Auth", "Profesores", "Reservas"],
    requirements=[{"id": "RF-001", "title": "CRUD de profesores", "description": "Gestionar profesores."}],
    needs_auth=True,
    needs_admin_panel=True,
)

TUTORIAL_REQUEST_NEXTJS = TUTORIAL_REQUEST_DJANGO.model_copy(
    update={"architecture_type": "NEXTJS_APP", "stack": ["Next.js", "TypeScript", "Prisma", "PostgreSQL"]}
)

TUTORIAL_REQUEST_LARAVEL = TUTORIAL_REQUEST_DJANGO.model_copy(
    update={"architecture_type": "LARAVEL_MONOLITH", "stack": ["PHP", "Laravel", "PostgreSQL"]}
)

TUTORIAL_REQUEST_UNKNOWN = TUTORIAL_REQUEST_DJANGO.model_copy(
    update={"architecture_type": "UNKNOWN_ARCH", "stack": []}
)


class TestTutorialAgent:
    def test_django_deterministic_returns_phases(self) -> None:
        result = TutorialAgent().generate(TUTORIAL_REQUEST_DJANGO)

        assert result.project_name == "Reservas de clases"
        assert result.architecture_type == "DJANGO_REST"
        assert len(result.phases) >= 5
        assert result.total_steps == sum(len(p.steps) for p in result.phases)

    def test_django_has_migrate_command(self) -> None:
        result = TutorialAgent().generate(TUTORIAL_REQUEST_DJANGO)

        all_commands = [s.command for p in result.phases for s in p.steps if s.command]
        assert any("migrate" in cmd for cmd in all_commands)

    def test_django_has_admin_phase(self) -> None:
        result = TutorialAgent().generate(TUTORIAL_REQUEST_DJANGO)

        titles = [p.title for p in result.phases]
        assert any("Admin" in t for t in titles)

    def test_nextjs_has_prisma_command(self) -> None:
        result = TutorialAgent().generate(TUTORIAL_REQUEST_NEXTJS)

        all_commands = [s.command for p in result.phases for s in p.steps if s.command]
        assert any("prisma" in cmd for cmd in all_commands)

    def test_laravel_has_artisan_command(self) -> None:
        result = TutorialAgent().generate(TUTORIAL_REQUEST_LARAVEL)

        all_commands = [s.command for p in result.phases for s in p.steps if s.command]
        assert any("artisan" in cmd for cmd in all_commands)

    def test_unknown_arch_llm_fallback_then_generic(self) -> None:
        with patch("app.agents.tutorial_agent.get_llm", return_value=None):
            result = TutorialAgent().generate(TUTORIAL_REQUEST_UNKNOWN)

        assert result.project_name == "Reservas de clases"
        assert len(result.phases) >= 3

    def test_total_steps_matches_sum(self) -> None:
        for req in [TUTORIAL_REQUEST_DJANGO, TUTORIAL_REQUEST_NEXTJS, TUTORIAL_REQUEST_LARAVEL]:
            result = TutorialAgent().generate(req)
            assert result.total_steps == sum(len(p.steps) for p in result.phases)

    def test_endpoint_returns_tutorial(self) -> None:
        response = client.post("/generate-tutorial", json=TUTORIAL_REQUEST_DJANGO.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert body["project_name"] == "Reservas de clases"
        assert body["architecture_type"] == "DJANGO_REST"
        assert len(body["phases"]) >= 5
        assert body["total_steps"] > 0

    def test_endpoint_unknown_arch_uses_generic_fallback(self) -> None:
        with patch("app.agents.tutorial_agent.get_llm", return_value=None):
            response = client.post("/generate-tutorial", json=TUTORIAL_REQUEST_UNKNOWN.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert len(body["phases"]) >= 3


# ── ArchitectureAgent ─────────────────────────────────────────────────────────

ARCH_REQUEST = ArchitectureRequest(
    project_name="Reservas de clases",
    sector="Educación",
    problem="Gestionar reservas de clases particulares de forma manual",
    target_users="Academias y profesores particulares",
    key_features=["CRUD de profesores", "Reserva de clases", "Panel admin", "Calendario", "Notificaciones", "Pagos", "Reportes"],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    preferred_stack="",
)

ARCH_REQUEST_LARAVEL = ARCH_REQUEST.model_copy(update={"preferred_stack": "laravel"})
ARCH_REQUEST_NEXTJS  = ARCH_REQUEST.model_copy(update={"preferred_stack": "nextjs"})
ARCH_REQUEST_DJANGO  = ARCH_REQUEST.model_copy(update={"preferred_stack": "django"})
ARCH_REQUEST_AI      = ARCH_REQUEST.model_copy(update={"needs_ai": True, "preferred_stack": ""})


class TestArchitectureAgent:
    def test_rule_based_returns_learning_path(self) -> None:
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(ARCH_REQUEST)

        assert len(result.learning_path) > 0
        assert all(r.title and r.url and r.type and r.level for r in result.learning_path)

    def test_rule_based_returns_when_to_upgrade(self) -> None:
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(ARCH_REQUEST)

        assert len(result.when_to_upgrade) > 0
        assert all(s.signal and s.reason and s.next_step for s in result.when_to_upgrade)

    def test_laravel_has_bootcamp_resource(self) -> None:
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(ARCH_REQUEST_LARAVEL)

        assert result.architecture_type == "LARAVEL_MONOLITH"
        urls = [r.url for r in result.learning_path]
        assert any("bootcamp.laravel.com" in u for u in urls)

    def test_nextjs_has_learn_resource(self) -> None:
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(ARCH_REQUEST_NEXTJS)

        assert result.architecture_type == "NEXTJS_APP"
        urls = [r.url for r in result.learning_path]
        assert any("nextjs.org/learn" in u for u in urls)

    def test_django_has_djangogirls_resource(self) -> None:
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(ARCH_REQUEST_DJANGO)

        assert result.architecture_type == "DJANGO_REST"
        urls = [r.url for r in result.learning_path]
        assert any("djangogirls" in u for u in urls)

    def test_fastapi_ai_recommended_for_ai_projects(self) -> None:
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(ARCH_REQUEST_AI)

        assert result.architecture_type == "FASTAPI_AI"
        assert len(result.learning_path) > 0
        assert len(result.when_to_upgrade) > 0

    def test_learning_path_levels_are_valid(self) -> None:
        valid_levels = {"BEGINNER", "INTERMEDIATE", "ADVANCED"}
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(ARCH_REQUEST)

        assert all(r.level in valid_levels for r in result.learning_path)

    def test_upgrade_signals_have_all_fields(self) -> None:
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            for req in [ARCH_REQUEST_LARAVEL, ARCH_REQUEST_NEXTJS, ARCH_REQUEST_DJANGO, ARCH_REQUEST_AI]:
                result = ArchitectureAgent().recommend(req)
                for sig in result.when_to_upgrade:
                    assert sig.signal, f"Missing signal in {result.architecture_type}"
                    assert sig.reason, f"Missing reason in {result.architecture_type}"
                    assert sig.next_step, f"Missing next_step in {result.architecture_type}"

    def test_endpoint_includes_new_fields(self) -> None:
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            response = client.post("/recommend-architecture", json=ARCH_REQUEST.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert "learning_path" in body
        assert "when_to_upgrade" in body
        assert len(body["learning_path"]) > 0
        assert len(body["when_to_upgrade"]) > 0
        assert all(k in body["learning_path"][0] for k in ("title", "url", "type", "level"))
        assert all(k in body["when_to_upgrade"][0] for k in ("signal", "reason", "next_step"))

    def test_inertia_react_rule_based(self) -> None:
        req = ARCH_REQUEST.model_copy(update={"preferred_stack": "inertia react"})
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(req)

        assert result.architecture_type == "LARAVEL_INERTIA_REACT"
        assert result.name  # name is populated
        assert len(result.first_steps) > 0
        assert len(result.learning_path) > 0

    def test_inertia_vue_rule_based(self) -> None:
        req = ARCH_REQUEST.model_copy(update={"preferred_stack": "inertia vue"})
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(req)

        assert result.architecture_type == "LARAVEL_INERTIA_VUE"
        assert len(result.first_steps) > 0

    def test_react_express_rule_based(self) -> None:
        req = ARCH_REQUEST.model_copy(update={"preferred_stack": "express"})
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(req)

        assert result.architecture_type == "REACT_EXPRESS"
        assert any("express" in step.lower() for step in result.first_steps)

    def test_laravel_inertia_react_first_steps_contain_composer(self) -> None:
        req = ARCH_REQUEST.model_copy(update={"preferred_stack": "laravel react"})
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(req)

        assert result.architecture_type == "LARAVEL_INERTIA_REACT"
        assert any("composer" in step.lower() for step in result.first_steps)

    def test_react_express_first_steps_contain_npm(self) -> None:
        req = ARCH_REQUEST.model_copy(update={"preferred_stack": "react express"})
        with patch("app.agents.architecture_agent.get_llm", return_value=None):
            result = ArchitectureAgent().recommend(req)

        assert result.architecture_type == "REACT_EXPRESS"
        assert any("npm" in step.lower() for step in result.first_steps)


# ── CodeGenerationAgent — sector templates (Sprint 0009) ────────────────────

CODEGEN_RRHH = CodeGenerationRequest(
    project_name="Portal RRHH",
    sector="RRHH y empresas",
    modules=["Empleados", "Departamentos", "Ausencias"],
    requirements=[{"id": "RF-001", "title": "Gestión de empleados", "description": "CRUD empleados."}],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)

CODEGEN_SALUD = CodeGenerationRequest(
    project_name="Clinica Digital",
    sector="Salud y bienestar",
    modules=["Pacientes", "Doctores", "Citas"],
    requirements=[{"id": "RF-001", "title": "Gestión de pacientes", "description": "CRUD pacientes."}],
    needs_auth=True,
    needs_admin_panel=False,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)

CODEGEN_HORECA = CodeGenerationRequest(
    project_name="El Rincón",
    sector="Restaurante y hostelería",
    modules=["Carta", "Mesas", "Reservas", "Comandas"],
    requirements=[{"id": "RF-001", "title": "Gestión de comandas", "description": "CRUD comandas."}],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)

CODEGEN_INMO = CodeGenerationRequest(
    project_name="Pisos ya",
    sector="Agencia inmobiliaria",
    modules=["Propiedades", "Clientes", "Visitas", "Contratos"],
    requirements=[{"id": "RF-001", "title": "Gestión de propiedades", "description": "CRUD propiedades."}],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)

CODEGEN_ECOMMERCE = CodeGenerationRequest(
    project_name="MiTienda",
    sector="Ecommerce y venta online",
    modules=["Productos", "Carrito", "Pedidos"],
    requirements=[{"id": "RF-001", "title": "Catálogo de productos", "description": "Listar productos."}],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)

CODEGEN_LOGISTICA = CodeGenerationRequest(
    project_name="TransExpress",
    sector="Logística y transporte",
    modules=["Envíos", "Rutas", "Flota"],
    requirements=[{"id": "RF-001", "title": "Gestión de envíos", "description": "CRUD envíos."}],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)


@pytest.mark.skip(reason="Sector templates were replaced by stack-based fallback scaffolds in 1e9ce17")
class TestSectorTemplates:
    def test_rrhh_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_RRHH, llm=None)

        assert result.project_name == "Portal RRHH"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_rrhh_schema_has_employee_model(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_RRHH, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Employee" in schema.content
        assert "model Department" in schema.content
        assert "model LeaveRequest" in schema.content

    def test_rrhh_schema_has_leave_request_model(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_RRHH, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "LeaveType" in schema.content
        assert "LeaveStatus" in schema.content

    def test_salud_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_SALUD, llm=None)

        assert result.project_name == "Clinica Digital"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "apps/web/src/app/citas/page.tsx" in paths

    def test_salud_schema_has_medical_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_SALUD, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Patient" in schema.content
        assert "model Doctor" in schema.content
        assert "model Appointment" in schema.content
        assert "model MedicalRecord" in schema.content

    def test_salud_has_appointments_page(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_SALUD, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/citas/page.tsx" in paths
        assert "apps/web/src/app/pacientes/page.tsx" in paths

    def test_rrhh_triggered_by_keyword_in_sector(self) -> None:
        req = CODEGEN_RRHH.model_copy(update={"sector": "recursos humanos"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Employee" in schema.content

    def test_salud_triggered_by_clinica_keyword(self) -> None:
        req = CODEGEN_SALUD.model_copy(update={"sector": "clinica medica"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Patient" in schema.content

    def test_rrhh_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_RRHH, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in RRHH template"

    def test_salud_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_SALUD, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in SALUD template"

    # ── HORECA ──────────────────────────────────────────────────────────────

    def test_horeca_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_HORECA, llm=None)

        assert result.project_name == "El Rincón"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_horeca_schema_has_restaurant_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_HORECA, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model MenuItem" in schema.content
        assert "model Table" in schema.content
        assert "model Reservation" in schema.content
        assert "model Order" in schema.content

    def test_horeca_schema_has_order_line(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_HORECA, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model OrderLine" in schema.content
        assert "enum MenuCategory" in schema.content
        assert "enum OrderStatus" in schema.content

    def test_horeca_has_comanda_and_reservas_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_HORECA, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/reservas/page.tsx" in paths
        assert "apps/web/src/app/comandas/page.tsx" in paths
        assert "apps/web/src/app/carta/page.tsx" in paths

    def test_horeca_triggered_by_restaurante_keyword(self) -> None:
        req = CODEGEN_HORECA.model_copy(update={"sector": "gestión de restaurante"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model MenuItem" in schema.content

    def test_horeca_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_HORECA, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in HORECA template"

    # ── INMOBILIARIA ─────────────────────────────────────────────────────────

    def test_inmobiliaria_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_INMO, llm=None)

        assert result.project_name == "Pisos ya"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_inmobiliaria_schema_has_real_estate_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_INMO, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Property" in schema.content
        assert "model Client" in schema.content
        assert "model Visit" in schema.content
        assert "model Contract" in schema.content

    def test_inmobiliaria_schema_has_lead_pipeline(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_INMO, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "enum LeadStatus" in schema.content
        assert "enum PropertyType" in schema.content
        assert "enum ContractType" in schema.content

    def test_inmobiliaria_has_propiedades_and_visitas_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_INMO, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/propiedades/page.tsx" in paths
        assert "apps/web/src/app/clientes/page.tsx" in paths
        assert "apps/web/src/app/visitas/page.tsx" in paths

    def test_inmobiliaria_triggered_by_inmobiliaria_keyword(self) -> None:
        req = CODEGEN_INMO.model_copy(update={"sector": "agencia inmobiliaria"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Property" in schema.content

    def test_inmobiliaria_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_INMO, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in INMOBILIARIA template"

    # ── ECOMMERCE ────────────────────────────────────────────────────────────

    def test_ecommerce_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ECOMMERCE, llm=None)

        assert result.project_name == "MiTienda"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_ecommerce_schema_has_shop_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ECOMMERCE, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Product" in schema.content
        assert "model Cart" in schema.content
        assert "model CartItem" in schema.content
        assert "model Order" in schema.content
        assert "model OrderItem" in schema.content

    def test_ecommerce_schema_has_category_and_address(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ECOMMERCE, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Category" in schema.content
        assert "model Address" in schema.content
        assert "enum OrderStatus" in schema.content

    def test_ecommerce_has_shop_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ECOMMERCE, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/productos/page.tsx" in paths
        assert "apps/web/src/app/carrito/page.tsx" in paths
        assert "apps/web/src/app/pedidos/page.tsx" in paths

    def test_ecommerce_triggered_by_tienda_online_keyword(self) -> None:
        req = CODEGEN_ECOMMERCE.model_copy(update={"sector": "tienda online de ropa"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Product" in schema.content

    def test_ecommerce_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ECOMMERCE, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in ECOMMERCE template"

    # ── LOGISTICA ────────────────────────────────────────────────────────────

    def test_logistica_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_LOGISTICA, llm=None)

        assert result.project_name == "TransExpress"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_logistica_schema_has_logistics_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_LOGISTICA, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Shipment" in schema.content
        assert "model Vehicle" in schema.content
        assert "model Driver" in schema.content
        assert "model Route" in schema.content

    def test_logistica_schema_has_tracking_events(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_LOGISTICA, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model TrackingEvent" in schema.content
        assert "model RouteItem" in schema.content
        assert "enum ShipmentStatus" in schema.content

    def test_logistica_has_tracking_and_fleet_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_LOGISTICA, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/tracking/page.tsx" in paths
        assert "apps/web/src/app/envios/page.tsx" in paths
        assert "apps/web/src/app/flota/page.tsx" in paths

    def test_logistica_triggered_by_envio_keyword(self) -> None:
        req = CODEGEN_LOGISTICA.model_copy(update={"sector": "empresa de envíos y mensajería"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Shipment" in schema.content

    def test_logistica_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_LOGISTICA, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in LOGISTICA template"


CODEGEN_FINTECH = CodeGenerationRequest(
    project_name="MiFinanzas",
    sector="Fintech y gestión financiera",
    modules=["Cuentas", "Transacciones", "Presupuesto", "Metas"],
    requirements=[{"id": "RF-001", "title": "Control de gastos", "description": "Registrar ingresos y gastos."}],
    needs_auth=True,
    needs_admin_panel=False,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)

CODEGEN_EVENTOS = CodeGenerationRequest(
    project_name="EventPass",
    sector="Eventos y venta de entradas",
    modules=["Eventos", "Entradas", "Check-in"],
    requirements=[{"id": "RF-001", "title": "Compra de entradas", "description": "Reservar entradas."}],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)


@pytest.mark.skip(reason="Sector templates were replaced by stack-based fallback scaffolds in 1e9ce17")
class TestFintechTemplate:
    def test_fintech_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FINTECH, llm=None)

        assert result.project_name == "MiFinanzas"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_fintech_schema_has_financial_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FINTECH, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Account" in schema.content
        assert "model Transaction" in schema.content
        assert "model Budget" in schema.content
        assert "model Goal" in schema.content

    def test_fintech_schema_has_account_types_and_enums(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FINTECH, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "enum AccountType" in schema.content
        assert "enum TransactionType" in schema.content
        assert "CHECKING" in schema.content
        assert "SAVINGS" in schema.content

    def test_fintech_has_finance_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FINTECH, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/transacciones/page.tsx" in paths
        assert "apps/web/src/app/presupuesto/page.tsx" in paths
        assert "apps/web/src/app/metas/page.tsx" in paths

    def test_fintech_triggered_by_finanzas_keyword(self) -> None:
        req = CODEGEN_FINTECH.model_copy(update={"sector": "control de finanzas personales"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Account" in schema.content

    def test_fintech_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FINTECH, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in FINTECH template"


@pytest.mark.skip(reason="Sector templates were replaced by stack-based fallback scaffolds in 1e9ce17")
class TestEventosTemplate:
    def test_eventos_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_EVENTOS, llm=None)

        assert result.project_name == "EventPass"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_eventos_schema_has_event_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_EVENTOS, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Event" in schema.content
        assert "model TicketType" in schema.content
        assert "model Order" in schema.content
        assert "model Attendee" in schema.content

    def test_eventos_schema_has_venue_and_checkin(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_EVENTOS, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Venue" in schema.content
        assert "model OrderItem" in schema.content
        assert "checkedIn" in schema.content

    def test_eventos_has_event_and_checkin_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_EVENTOS, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/eventos/page.tsx" in paths
        assert "apps/web/src/app/mis-entradas/page.tsx" in paths
        assert "apps/web/src/app/checkin/page.tsx" in paths

    def test_eventos_triggered_by_concierto_keyword(self) -> None:
        req = CODEGEN_EVENTOS.model_copy(update={"sector": "plataforma de conciertos y festivales"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Event" in schema.content

    def test_eventos_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_EVENTOS, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in EVENTOS template"


CODEGEN_VETERINARIA = CodeGenerationRequest(
    project_name="VetClinica",
    sector="Clínica veterinaria",
    modules=["Mascotas", "Citas", "Historia clínica"],
    requirements=[{"id": "RF-001", "title": "Registro de mascotas", "description": "CRUD mascotas y propietarios."}],
    needs_auth=True,
    needs_admin_panel=False,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)

CODEGEN_GYM = CodeGenerationRequest(
    project_name="FitZone",
    sector="Gimnasio y fitness",
    modules=["Membresías", "Clases", "Reservas"],
    requirements=[{"id": "RF-001", "title": "Gestión de membresías", "description": "Planes y suscripciones."}],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)


@pytest.mark.skip(reason="Sector templates were replaced by stack-based fallback scaffolds in 1e9ce17")
class TestVeterinariaTemplate:
    def test_veterinaria_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_VETERINARIA, llm=None)

        assert result.project_name == "VetClinica"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_veterinaria_schema_has_clinic_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_VETERINARIA, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Owner" in schema.content
        assert "model Pet" in schema.content
        assert "model Appointment" in schema.content
        assert "model MedicalRecord" in schema.content

    def test_veterinaria_schema_has_vaccine_and_enums(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_VETERINARIA, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Vaccine" in schema.content
        assert "enum Species" in schema.content
        assert "enum AppointmentType" in schema.content
        assert "enum VetRole" in schema.content

    def test_veterinaria_has_clinic_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_VETERINARIA, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/mascotas/page.tsx" in paths
        assert "apps/web/src/app/citas/page.tsx" in paths
        assert "apps/web/src/app/historia/page.tsx" in paths

    def test_veterinaria_triggered_by_mascota_keyword(self) -> None:
        req = CODEGEN_VETERINARIA.model_copy(update={"sector": "clínica para mascotas y animales"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Pet" in schema.content

    def test_veterinaria_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_VETERINARIA, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in VETERINARIA template"


@pytest.mark.skip(reason="Sector templates were replaced by stack-based fallback scaffolds in 1e9ce17")
class TestGymTemplate:
    def test_gym_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_GYM, llm=None)

        assert result.project_name == "FitZone"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_gym_schema_has_gym_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_GYM, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model MembershipPlan" in schema.content
        assert "model Membership" in schema.content
        assert "model GymClass" in schema.content
        assert "model ClassSession" in schema.content
        assert "model ClassBooking" in schema.content

    def test_gym_schema_has_trainer_and_enums(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_GYM, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Trainer" in schema.content
        assert "enum ClassType" in schema.content
        assert "enum DayOfWeek" in schema.content
        assert "enum MembershipStatus" in schema.content

    def test_gym_has_gym_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_GYM, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/clases/page.tsx" in paths
        assert "apps/web/src/app/reservas/page.tsx" in paths
        assert "apps/web/src/app/membresia/page.tsx" in paths

    def test_gym_triggered_by_gimnasio_keyword(self) -> None:
        req = CODEGEN_GYM.model_copy(update={"sector": "gestión de gimnasio y membresías"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model GymClass" in schema.content

    def test_gym_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_GYM, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in GYM template"


CODEGEN_FARMACIA = CodeGenerationRequest(
    project_name="FarmaPlus",
    sector="Farmacia y dispensario",
    modules=["Inventario", "Ventas", "Recetas"],
    requirements=[{"id": "RF-001", "title": "Punto de venta", "description": "Dispensar medicamentos."}],
    needs_auth=True,
    needs_admin_panel=False,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)

CODEGEN_ABOGADOS = CodeGenerationRequest(
    project_name="LexDesk",
    sector="Despacho de abogados y bufete jurídico",
    modules=["Expedientes", "Clientes", "Facturación"],
    requirements=[{"id": "RF-001", "title": "Gestión de expedientes", "description": "CRUD casos legales."}],
    needs_auth=True,
    needs_admin_panel=True,
    needs_ai=False,
    stack=["Next.js", "tRPC", "Prisma", "PostgreSQL"],
)


@pytest.mark.skip(reason="Sector templates were replaced by stack-based fallback scaffolds in 1e9ce17")
class TestFarmaciaTemplate:
    def test_farmacia_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FARMACIA, llm=None)

        assert result.project_name == "FarmaPlus"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_farmacia_schema_has_pharmacy_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FARMACIA, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Product" in schema.content
        assert "model Sale" in schema.content
        assert "model SaleItem" in schema.content
        assert "model Prescription" in schema.content

    def test_farmacia_schema_has_enums_and_fields(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FARMACIA, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "enum PharmRole" in schema.content
        assert "enum SaleStatus" in schema.content
        assert "requiresPrescription" in schema.content
        assert "minStock" in schema.content

    def test_farmacia_has_pharmacy_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FARMACIA, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/inventario/page.tsx" in paths
        assert "apps/web/src/app/recetas/page.tsx" in paths
        assert "apps/web/src/app/ventas/page.tsx" in paths

    def test_farmacia_triggered_by_farmacia_keyword(self) -> None:
        req = CODEGEN_FARMACIA.model_copy(update={"sector": "gestión de farmacia y botica"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Prescription" in schema.content

    def test_farmacia_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_FARMACIA, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in FARMACIA template"


@pytest.mark.skip(reason="Sector templates were replaced by stack-based fallback scaffolds in 1e9ce17")
class TestAbogadosTemplate:
    def test_abogados_template_generates_files(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ABOGADOS, llm=None)

        assert result.project_name == "LexDesk"
        paths = [f.path for f in result.files]
        assert "apps/api/prisma/schema.prisma" in paths
        assert "docker-compose.yml" in paths

    def test_abogados_schema_has_legal_models(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ABOGADOS, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model LegalClient" in schema.content
        assert "model Matter" in schema.content
        assert "model Hearing" in schema.content
        assert "model TimeEntry" in schema.content
        assert "model Invoice" in schema.content

    def test_abogados_schema_has_legal_enums(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ABOGADOS, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "enum LegalRole" in schema.content
        assert "enum CaseType" in schema.content
        assert "enum CaseStatus" in schema.content
        assert "enum InvoiceStatus" in schema.content

    def test_abogados_has_legal_pages(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ABOGADOS, llm=None)

        paths = [f.path for f in result.files]
        assert "apps/web/src/app/expedientes/page.tsx" in paths
        assert "apps/web/src/app/clientes/page.tsx" in paths
        assert "apps/web/src/app/agenda/page.tsx" in paths
        assert "apps/web/src/app/facturacion/page.tsx" in paths

    def test_abogados_triggered_by_bufete_keyword(self) -> None:
        req = CODEGEN_ABOGADOS.model_copy(update={"sector": "software para bufete de abogados"})
        result = CodeGenerationAgent().generate(req, llm=None)

        schema = next(f for f in result.files if f.path == "apps/api/prisma/schema.prisma")
        assert "model Matter" in schema.content

    def test_abogados_no_duplicate_paths(self) -> None:
        result = CodeGenerationAgent().generate(CODEGEN_ABOGADOS, llm=None)

        paths = [f.path for f in result.files]
        assert len(paths) == len(set(paths)), "Duplicate file paths in ABOGADOS template"


# ── TechProposalAgent ─────────────────────────────────────────────────────────

from app.schemas.tech_proposal import TechProposalRequest, TechProposalResponse  # noqa: E402

_TECH_REQ_BEGINNER_SINGLE = TechProposalRequest(
    name="Mi App",
    sector="Educación",
    level="BEGINNER",
    product_type="web",
    main_objective="mvp",
    architecture_style="single",
    data_needs=[],
    ai_needs="none",
    deployment_target="docker_local",
    core_features=["CRUD básico", "Login"],
)

_TECH_REQ_BEGINNER_FRONTEND_API = _TECH_REQ_BEGINNER_SINGLE.model_copy(
    update={"architecture_style": "frontend_api"}
)

_TECH_REQ_INTERMEDIATE_FRONTEND_API = _TECH_REQ_BEGINNER_SINGLE.model_copy(
    update={"level": "INTERMEDIATE", "architecture_style": "frontend_api"}
)

_TECH_REQ_INTERMEDIATE_AI = _TECH_REQ_BEGINNER_SINGLE.model_copy(
    update={"level": "INTERMEDIATE", "architecture_style": "frontend_api", "ai_needs": "chat_assistant"}
)

_TECH_REQ_INTERMEDIATE_SINGLE = _TECH_REQ_BEGINNER_SINGLE.model_copy(
    update={"level": "INTERMEDIATE", "architecture_style": "single"}
)

_TECH_REQ_BEGINNER_AI = _TECH_REQ_BEGINNER_SINGLE.model_copy(
    update={"ai_needs": "chat_assistant"}
)

_TECH_REQ_BEGINNER_MOBILE = _TECH_REQ_BEGINNER_SINGLE.model_copy(
    update={"product_type": "mobile", "architecture_style": "mobile_api"}
)

_TECH_REQ_BEGINNER_DESKTOP = _TECH_REQ_BEGINNER_SINGLE.model_copy(
    update={"product_type": "desktop", "architecture_style": "desktop_api"}
)

_TECH_REQ_INTERMEDIATE_MOBILE = _TECH_REQ_BEGINNER_SINGLE.model_copy(
    update={"level": "INTERMEDIATE", "product_type": "mobile", "architecture_style": "mobile_api"}
)

_TECH_REQ_INTERMEDIATE_DESKTOP = _TECH_REQ_BEGINNER_SINGLE.model_copy(
    update={"level": "INTERMEDIATE", "product_type": "desktop", "architecture_style": "desktop_api"}
)


class TestCatalogKey:
    def test_beginner_single_key(self) -> None:
        assert _catalog_key(_TECH_REQ_BEGINNER_SINGLE) == "BEGINNER_single"

    def test_beginner_frontend_api_key(self) -> None:
        assert _catalog_key(_TECH_REQ_BEGINNER_FRONTEND_API) == "BEGINNER_frontend_api"

    def test_beginner_ai_overrides_to_ai_service(self) -> None:
        assert _catalog_key(_TECH_REQ_BEGINNER_AI) == "BEGINNER_ai_service"

    def test_beginner_mobile_key(self) -> None:
        assert _catalog_key(_TECH_REQ_BEGINNER_MOBILE) == "BEGINNER_mobile"

    def test_beginner_desktop_key(self) -> None:
        assert _catalog_key(_TECH_REQ_BEGINNER_DESKTOP) == "BEGINNER_desktop"

    def test_intermediate_frontend_api_key(self) -> None:
        assert _catalog_key(_TECH_REQ_INTERMEDIATE_FRONTEND_API) == "INTERMEDIATE_frontend_api"

    def test_intermediate_ai_overrides_arch(self) -> None:
        assert _catalog_key(_TECH_REQ_INTERMEDIATE_AI) == "INTERMEDIATE_ai_service"

    def test_intermediate_single_key(self) -> None:
        assert _catalog_key(_TECH_REQ_INTERMEDIATE_SINGLE) == "INTERMEDIATE_single"

    def test_intermediate_mobile_key(self) -> None:
        assert _catalog_key(_TECH_REQ_INTERMEDIATE_MOBILE) == "INTERMEDIATE_mobile"

    def test_intermediate_desktop_key(self) -> None:
        assert _catalog_key(_TECH_REQ_INTERMEDIATE_DESKTOP) == "INTERMEDIATE_desktop"

    def test_ai_none_does_not_trigger_ai_service(self) -> None:
        req = _TECH_REQ_INTERMEDIATE_FRONTEND_API.model_copy(update={"ai_needs": "none"})
        assert _catalog_key(req) != "INTERMEDIATE_ai_service"

    def test_ai_recommendation_does_not_trigger_ai_service(self) -> None:
        req = _TECH_REQ_INTERMEDIATE_FRONTEND_API.model_copy(update={"ai_needs": "recommendation"})
        assert _catalog_key(req) != "INTERMEDIATE_ai_service"

    def test_beginner_ai_produces_beginner_ai_service(self) -> None:
        req = _TECH_REQ_BEGINNER_SINGLE.model_copy(update={"ai_needs": "chat_assistant"})
        key = _catalog_key(req)
        assert key == "BEGINNER_ai_service"
        assert key != "INTERMEDIATE_ai_service"

    def test_mobile_api_normalized_to_mobile(self) -> None:
        req = _TECH_REQ_INTERMEDIATE_FRONTEND_API.model_copy(update={"architecture_style": "mobile_api"})
        assert _catalog_key(req) == "INTERMEDIATE_mobile"

    def test_desktop_api_normalized_to_desktop(self) -> None:
        req = _TECH_REQ_INTERMEDIATE_FRONTEND_API.model_copy(update={"architecture_style": "desktop_api"})
        assert _catalog_key(req) == "INTERMEDIATE_desktop"

    def test_unknown_arch_defaults_to_frontend_api(self) -> None:
        req = _TECH_REQ_INTERMEDIATE_FRONTEND_API.model_copy(update={"architecture_style": "unknown_xyz"})
        assert _catalog_key(req) == "INTERMEDIATE_frontend_api"

    def test_mobile_with_ai_stays_mobile(self) -> None:
        req = _TECH_REQ_INTERMEDIATE_MOBILE.model_copy(update={"ai_needs": "chat_assistant"})
        assert _catalog_key(req) == "INTERMEDIATE_mobile"

    def test_desktop_with_ai_stays_desktop(self) -> None:
        req = _TECH_REQ_INTERMEDIATE_DESKTOP.model_copy(update={"ai_needs": "agents"})
        assert _catalog_key(req) == "INTERMEDIATE_desktop"


class TestTechProposalAgent:
    def test_all_catalog_variants_return_three_proposals(self) -> None:
        for req in [
            _TECH_REQ_BEGINNER_SINGLE,
            _TECH_REQ_BEGINNER_FRONTEND_API,
            _TECH_REQ_BEGINNER_AI,
            _TECH_REQ_BEGINNER_MOBILE,
            _TECH_REQ_BEGINNER_DESKTOP,
            _TECH_REQ_INTERMEDIATE_FRONTEND_API,
            _TECH_REQ_INTERMEDIATE_AI,
            _TECH_REQ_INTERMEDIATE_SINGLE,
            _TECH_REQ_INTERMEDIATE_MOBILE,
            _TECH_REQ_INTERMEDIATE_DESKTOP,
        ]:
            with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
                result = TechProposalAgent().propose(req)
            assert len(result.proposals) == 3, f"Expected 3 proposals for {_catalog_key(req)}, got {len(result.proposals)}"

    def test_proposals_have_sequential_ids(self) -> None:
        with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
            result = TechProposalAgent().propose(_TECH_REQ_BEGINNER_SINGLE)

        ids = [p.id for p in result.proposals]
        assert ids == [1, 2, 3]

    def test_recommended_id_in_range(self) -> None:
        for req in [_TECH_REQ_BEGINNER_SINGLE, _TECH_REQ_INTERMEDIATE_AI, _TECH_REQ_INTERMEDIATE_SINGLE]:
            with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
                result = TechProposalAgent().propose(req)
            assert result.recommended_id in {p.id for p in result.proposals}

    def test_recommendation_reason_not_empty(self) -> None:
        with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
            result = TechProposalAgent().propose(_TECH_REQ_INTERMEDIATE_AI)

        assert len(result.recommendation_reason) > 0

    def test_each_proposal_has_required_fields(self) -> None:
        with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
            result = TechProposalAgent().propose(_TECH_REQ_INTERMEDIATE_FRONTEND_API)

        for p in result.proposals:
            assert p.name, "name must not be empty"
            assert p.tagline, "tagline must not be empty"
            assert len(p.stack) >= 2, "stack must have at least 2 entries"
            assert len(p.advantages) >= 1, "advantages must not be empty"
            assert len(p.limitations) >= 1, "limitations must not be empty"
            assert len(p.learning_outcomes) >= 1, "learning_outcomes must not be empty"
            assert p.estimated_setup_minutes > 0

    def test_ai_service_variant_has_ai_ready_proposals(self) -> None:
        with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
            result = TechProposalAgent().propose(_TECH_REQ_INTERMEDIATE_AI)

        assert all(p.ai_ready for p in result.proposals), "All INTERMEDIATE_ai_service proposals must be ai_ready"

    def test_regular_web_catalog_does_not_offer_django(self) -> None:
        for req in (
            _TECH_REQ_BEGINNER_SINGLE,
            _TECH_REQ_BEGINNER_AI,
            _TECH_REQ_INTERMEDIATE_SINGLE,
            _TECH_REQ_INTERMEDIATE_FRONTEND_API,
        ):
            with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
                result = TechProposalAgent().propose(req)
            stacks = [" ".join(proposal.stack).lower() for proposal in result.proposals]
            assert all("django" not in stack for stack in stacks)

    def test_heavy_data_project_gets_exactly_one_django_alternative(self) -> None:
        req = _TECH_REQ_INTERMEDIATE_SINGLE.model_copy(update={
            "sector": "Finanzas",
            "main_objective": "ERP con reporting, auditoría y aprobaciones",
            "data_needs": ["datos relacionales", "histórico", "reporting"],
            "core_features": [
                "Contabilidad", "Facturación", "Inventario", "Aprobaciones",
                "Auditoría", "Reporting", "Permisos",
            ],
        })
        assert _django_is_justified(req)

        with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
            result = TechProposalAgent().propose(req)

        django_proposals = [
            proposal for proposal in result.proposals
            if "django" in " ".join(proposal.stack).lower()
        ]
        assert len(django_proposals) == 1
        assert django_proposals[0].id == 3

    def test_unjustified_django_llm_response_falls_back_to_catalog(self) -> None:
        from app.schemas.tech_proposal import TechProposal as TP
        django_response = TechProposalResponse(
            proposals=[
                TP(id=1, name="Django A", tagline="Django", stack=["Django 5", "PostgreSQL"],
                   difficulty="Principiante", description="d", advantages=["a"], limitations=["l"],
                   recommended_for="r", learning_outcomes=["o"], docker_ready=True,
                   ai_ready=False, estimated_setup_minutes=10),
                TP(id=2, name="Django B", tagline="DRF", stack=["Django REST Framework", "React"],
                   difficulty="Principiante", description="d", advantages=["a"], limitations=["l"],
                   recommended_for="r", learning_outcomes=["o"], docker_ready=True,
                   ai_ready=False, estimated_setup_minutes=10),
            ],
            recommended_id=1,
            recommendation_reason="Django everywhere",
        )
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = django_response

        result = TechProposalAgent().propose(_TECH_REQ_BEGINNER_SINGLE, llm=mock_llm)

        assert len(result.proposals) == 3
        assert all("django" not in " ".join(p.stack).lower() for p in result.proposals)

    def test_prisma_schema_includes_relations_indexes_and_table_mapping(self) -> None:
        generated = generate_prisma_schema(
            modules=["Bookings"],
            needs_auth=True,
            data_entities=[
                {
                    "name": "Booking",
                    "fields": [
                        "id: UUID PRIMARY KEY",
                        "user_id: UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE",
                        "status: VARCHAR(30) NOT NULL DEFAULT 'active'",
                        "created_at: TIMESTAMPTZ NOT NULL DEFAULT now()",
                        "updated_at: TIMESTAMPTZ NOT NULL DEFAULT now()",
                    ],
                    "relations": ["belongs_to User"],
                }
            ],
        )

        assert "userId" in generated.content
        assert "@relation(fields: [userId], references: [id], onDelete: Cascade)" in generated.content
        assert "bookings" in generated.content
        assert "@@index([userId, status])" in generated.content
        assert '@@map("bookings")' in generated.content
        booking_model = generated.content.split("model Booking {", 1)[1]
        assert booking_model.count("\n  id ") == 1

    def test_complete_auth_schema_supports_multiple_user_relations(self) -> None:
        with patch("app.agents.openspec_agent.get_llm", return_value=None):
            openspec = OpenSpecAgent().generate(IDEA, MOCK_REQUIREMENTS)

        generated = generate_prisma_schema(
            modules=openspec.spec["modules"],
            needs_auth=True,
            data_entities=openspec.spec["data_entities"],
        )

        for model in ("User", "Role", "UserRole", "RefreshToken", "AuditLog"):
            assert f"model {model} {{" in generated.content
        assert "UserRoleUser" in generated.content
        assert "UserRoleAssignedByUser" in generated.content
        assert "onDelete: SetNull" in generated.content

    def test_uses_llm_when_available(self) -> None:
        from app.schemas.tech_proposal import TechProposal as TP
        mock_response = TechProposalResponse(
            proposals=[
                TP(id=1, name="A", tagline="t", stack=["X"], difficulty="Principiante",
                   description="d", advantages=["a"], limitations=["l"],
                   recommended_for="r", learning_outcomes=["o"],
                   docker_ready=True, ai_ready=False, estimated_setup_minutes=10),
                TP(id=2, name="B", tagline="t", stack=["Y"], difficulty="Principiante",
                   description="d", advantages=["a"], limitations=["l"],
                   recommended_for="r", learning_outcomes=["o"],
                   docker_ready=True, ai_ready=False, estimated_setup_minutes=10),
            ],
            recommended_id=1,
            recommendation_reason="LLM reason",
        )
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = mock_response

        result = TechProposalAgent().propose(_TECH_REQ_BEGINNER_SINGLE, llm=mock_llm)

        mock_llm.with_structured_output.assert_called_once_with(TechProposalResponse)
        assert result.recommendation_reason == "LLM reason"

    def test_falls_back_when_llm_raises(self) -> None:
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.side_effect = RuntimeError("LLM timeout")

        result = TechProposalAgent().propose(_TECH_REQ_BEGINNER_SINGLE, llm=mock_llm)

        assert len(result.proposals) == 3

    def test_tries_next_ai_before_catalog_fallback(self) -> None:
        from app.schemas.tech_proposal import TechProposal as TP

        failing_llm = MagicMock()
        failing_llm.with_structured_output.return_value.invoke.side_effect = RuntimeError(
            "first model unavailable"
        )
        successful_response = TechProposalResponse(
            proposals=[
                TP(id=1, name="AI A", tagline="t", stack=["React", "NestJS"],
                   difficulty="Intermedio", description="d", advantages=["a"], limitations=["l"],
                   recommended_for="r", learning_outcomes=["o"], docker_ready=True,
                   ai_ready=True, estimated_setup_minutes=20),
                TP(id=2, name="AI B", tagline="t", stack=["Vue", "FastAPI"],
                   difficulty="Intermedio", description="d", advantages=["a"], limitations=["l"],
                   recommended_for="r", learning_outcomes=["o"], docker_ready=True,
                   ai_ready=True, estimated_setup_minutes=20),
            ],
            recommended_id=2,
            recommendation_reason="Generated by the second AI",
        )
        successful_llm = MagicMock()
        successful_llm.with_structured_output.return_value.invoke.return_value = successful_response

        with patch(
            "app.agents.tech_proposal_agent.get_llm_candidates",
            return_value=[failing_llm, successful_llm],
        ):
            result = TechProposalAgent().propose(_TECH_REQ_INTERMEDIATE_FRONTEND_API)

        assert result.recommendation_reason == "Generated by the second AI"

    def test_mobile_proposals_use_ai_when_valid(self) -> None:
        from app.schemas.tech_proposal import TechProposal as TP

        response = TechProposalResponse(
            proposals=[
                TP(id=1, name="Flutter AI", tagline="Flutter + FastAPI",
                   stack=["Flutter", "FastAPI"], difficulty="Intermedio", description="d",
                   advantages=["a"], limitations=["l"], recommended_for="r",
                   learning_outcomes=["o"], docker_ready=True, ai_ready=True,
                   estimated_setup_minutes=20),
                TP(id=2, name="Expo AI", tagline="React Native + Expo + NestJS",
                   stack=["React Native", "Expo", "NestJS"], difficulty="Intermedio",
                   description="d", advantages=["a"], limitations=["l"], recommended_for="r",
                   learning_outcomes=["o"], docker_ready=True, ai_ready=True,
                   estimated_setup_minutes=20),
            ],
            recommended_id=1,
            recommendation_reason="Mobile AI proposal",
        )
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = response

        result = TechProposalAgent().propose(_TECH_REQ_INTERMEDIATE_MOBILE, llm=mock_llm)

        assert result.recommendation_reason == "Mobile AI proposal"

    def test_falls_back_when_llm_returns_too_few_proposals(self) -> None:
        from app.schemas.tech_proposal import TechProposal as TP
        short_response = TechProposalResponse(
            proposals=[
                TP(id=1, name="A", tagline="t", stack=["X"], difficulty="Principiante",
                   description="d", advantages=["a"], limitations=["l"],
                   recommended_for="r", learning_outcomes=["o"],
                   docker_ready=True, ai_ready=False, estimated_setup_minutes=10),
            ],
            recommended_id=1,
            recommendation_reason="only one",
        )
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = short_response

        result = TechProposalAgent().propose(_TECH_REQ_BEGINNER_SINGLE, llm=mock_llm)

        assert len(result.proposals) == 3

    def test_endpoint_propose_tech_returns_valid_response(self) -> None:
        with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
            response = client.post("/propose-tech", json=_TECH_REQ_BEGINNER_SINGLE.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert len(body["proposals"]) == 3
        assert body["recommended_id"] in {p["id"] for p in body["proposals"]}
        assert body["recommendation_reason"]

    def test_endpoint_intermediate_ai_returns_ai_ready_stacks(self) -> None:
        with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
            response = client.post("/propose-tech", json=_TECH_REQ_INTERMEDIATE_AI.model_dump())

        assert response.status_code == 200
        body = response.json()
        assert all(p["ai_ready"] for p in body["proposals"])

    def test_endpoint_proposal_fields_complete(self) -> None:
        with patch("app.agents.tech_proposal_agent.get_llm_candidates", return_value=[]):
            response = client.post("/propose-tech", json=_TECH_REQ_INTERMEDIATE_FRONTEND_API.model_dump())

        assert response.status_code == 200
        for p in response.json()["proposals"]:
            assert all(k in p for k in ("id", "name", "tagline", "stack", "difficulty",
                                        "description", "advantages", "limitations",
                                        "recommended_for", "learning_outcomes",
                                        "docker_ready", "ai_ready", "estimated_setup_minutes"))

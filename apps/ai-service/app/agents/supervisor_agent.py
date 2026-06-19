from typing import Annotated, TypedDict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph

from app.core.llm import get_llm
from app.schemas.idea import IdeaRequest
from app.schemas.openspec import OpenSpecResponse
from app.schemas.requirements import RequirementsResponse


class PipelineState(TypedDict):
    idea: IdeaRequest
    # Optional single-LLM override (used in tests; None = let each node pick its own)
    llm: BaseChatModel | None
    product_analysis: Annotated[dict[str, object] | None, "product analysis result"]
    requirements: Annotated[RequirementsResponse | None, "generated requirements"]
    openspec: Annotated[OpenSpecResponse | None, "generated openspec"]
    decision: str


def _supervisor_node(state: PipelineState) -> PipelineState:
    idea = state["idea"]
    decision = "generate_requirements" if len(idea.core_features) >= 2 else "ask_more_questions"
    return {**state, "decision": decision}


def _product_node(state: PipelineState) -> PipelineState:
    from app.agents.product_agent import ProductAgent
    analysis = ProductAgent().analyze(state["idea"])
    return {**state, "product_analysis": analysis}


def _requirements_node(state: PipelineState) -> PipelineState:
    from app.agents.requirements_agent import RequirementsAgent
    llm_override = state["llm"]
    task_llm = llm_override if llm_override is not None else get_llm("reasoning")
    requirements = RequirementsAgent().generate(state["idea"], task_llm)
    return {**state, "requirements": requirements}


def _openspec_node(state: PipelineState) -> PipelineState:
    from app.agents.openspec_agent import OpenSpecAgent
    assert state["requirements"] is not None
    llm_override = state["llm"]
    task_llm = llm_override if llm_override is not None else get_llm("spec")
    openspec = OpenSpecAgent().generate(state["idea"], state["requirements"], task_llm)
    return {**state, "openspec": openspec}


def _route_after_supervisor(state: PipelineState) -> str:
    return state["decision"]


def _build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)
    graph.add_node("supervisor", _supervisor_node)
    graph.add_node("analyze_product", _product_node)
    graph.add_node("generate_requirements", _requirements_node)
    graph.add_node("generate_openspec", _openspec_node)
    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "generate_requirements": "analyze_product",
            "ask_more_questions": END,
        },
    )
    graph.add_edge("analyze_product", "generate_requirements")
    graph.add_edge("generate_requirements", "generate_openspec")
    graph.add_edge("generate_openspec", END)
    return graph


_compiled_graph = _build_graph().compile()


class SupervisorAgent:
    def run(self, idea: IdeaRequest, llm: BaseChatModel | None = None) -> PipelineState:
        """Run the full pipeline: supervisor → product_analysis → requirements → openspec.

        Pass llm= to inject a mock in tests. In production leave it None
        so each node resolves the best available model for its task.
        """
        initial_state: PipelineState = {
            "idea": idea,
            "llm": llm,
            "product_analysis": None,
            "requirements": None,
            "openspec": None,
            "decision": "",
        }
        return _compiled_graph.invoke(initial_state)

    def next_step(self, idea: IdeaRequest) -> str:
        """Backwards-compatibility shim."""
        if len(idea.core_features) < 2:
            return "ask_more_questions"
        return "generate_requirements"

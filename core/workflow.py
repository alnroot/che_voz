from typing import TypedDict, Annotated, Sequence
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator


class WorkflowState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_step: str
    result: dict
    error: str | None


class BaseWorkflow:
    def __init__(self):
        self.graph = StateGraph(WorkflowState)
        self._build_graph()
        self.workflow = self.graph.compile()
    
    def _build_graph(self):
        self.graph.add_node("process_input", self._process_input)
        self.graph.add_node("analyze", self._analyze)
        self.graph.add_node("generate_response", self._generate_response)
        
        self.graph.set_entry_point("process_input")
        self.graph.add_edge("process_input", "analyze")
        self.graph.add_edge("analyze", "generate_response")
        self.graph.set_finish_point("generate_response")
    
    def _process_input(self, state: WorkflowState) -> WorkflowState:
        state["current_step"] = "processing_input"
        return state
    
    def _analyze(self, state: WorkflowState) -> WorkflowState:
        state["current_step"] = "analyzing"
        messages = state.get("messages", [])
        if messages and isinstance(messages[-1], HumanMessage):
            analysis_result = {
                "input_length": len(messages[-1].content),
                "processed": True
            }
            state["result"] = analysis_result
        return state
    
    def _generate_response(self, state: WorkflowState) -> WorkflowState:
        state["current_step"] = "generating_response"
        messages = state.get("messages", [])
        if messages:
            response_content = f"Processed: {messages[-1].content}"
            state["messages"].append(AIMessage(content=response_content))
            state["result"]["response"] = response_content
        return state
    
    async def run(self, input_text: str) -> dict:
        initial_state = {
            "messages": [HumanMessage(content=input_text)],
            "current_step": "initialized",
            "result": {},
            "error": None
        }
        
        try:
            final_state = await self.workflow.ainvoke(initial_state)
            return {
                "success": True,
                "result": final_state.get("result", {}),
                "messages": [msg.content for msg in final_state.get("messages", [])]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
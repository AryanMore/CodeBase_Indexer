# graph/nodes/reasoning.py
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from graph.state import AgentState

llm = ChatOpenAI(temperature=0)

prompt = PromptTemplate(
    template=open("prompts/reasoning.txt").read(),
    input_variables=["context", "user_query"],
)


def reasoning_node(state: AgentState) -> AgentState:
    approved_chunks = (
        state["retrieved_chunks"]
        + state["expanded_chunks"]
        + state["file_chunks"]
    )

    context = "\n\n".join(
        f"[{c.file_path}:{c.start_line}-{c.end_line}]\n{c.content}"
        for c in approved_chunks
    )

    response = llm.predict(
        prompt.format(
            context=context,
            user_query=state["user_query"],
        )
    )

    state["explanation"] = response
    return state

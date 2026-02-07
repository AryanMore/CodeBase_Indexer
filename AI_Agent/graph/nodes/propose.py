# graph/nodes/propose.py
import uuid
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from schemas.diff import DiffBundle, FileDiff
from graph.state import AgentState

llm = ChatOpenAI(temperature=0)

prompt = PromptTemplate(
    template=open("prompts/propose.txt").read(),
    input_variables=["context", "goal"],
)


def propose_node(state: AgentState) -> AgentState:
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
            goal=state["user_query"],
        )
    )

    # ⚠️ In real usage, you would parse this response strictly.
    # For now, we store it as a single diff payload.
    bundle = DiffBundle(
        bundle_id=str(uuid.uuid4()),
        goal=state["user_query"],
        files=[
            FileDiff(
                file_path="MULTI_FILE",
                diff=response,
            )
        ],
        explanation="Generated from approved context only.",
    )

    state["proposed_diff_id"] = bundle.bundle_id
    return state

# graph/nodes/intent.py
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from schemas.intent import Intent
from graph.state import AgentState


llm = ChatOpenAI(temperature=0)

prompt = PromptTemplate(
    template=open("prompts/intent.txt").read(),
    input_variables=["user_query"],
)


def intent_node(state: AgentState) -> AgentState:
    response = llm.predict(
        prompt.format(user_query=state["user_query"])
    ).strip()

    state["intent"] = Intent(response)
    return state

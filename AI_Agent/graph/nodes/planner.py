# graph/nodes/planner.py
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from schemas.plan import Plan
from graph.state import AgentState


llm = ChatOpenAI(temperature=0)

prompt = PromptTemplate(
    template=open("prompts/planner.txt").read(),
    input_variables=["intent", "user_query"],
)


def planner_node(state: AgentState) -> AgentState:
    response = llm.predict(
        prompt.format(
            intent=state["intent"].value,
            user_query=state["user_query"],
        )
    )

    plan_data = json.loads(response)
    state["plan"] = Plan(**plan_data)

    return state

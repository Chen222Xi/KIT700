import random 
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission


@tool(name="test_1_cici_func",description="Tool which helps me qet a random and decide the mood of the agent", permission=ToolPermission.ADMIN)

def test_1_cici_func():
    return random.randint( 10,  20) 
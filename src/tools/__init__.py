class Tool:
    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict:
        return self._parameters

    def __init__(self, 
        name: str = None, 
        description: str = None, 
        parameters: dict = {}, 
        session = None
    ):
        self._name = name
        self._description = description
        self._parameters = parameters
        self._session = session

    def define(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    async def run(self, *args, **kwargs):
        if not self._session:
            return {}

        data = await self._session.call_tool(self.name, kwargs)
        if not data:
            return {}

        for tool_data in data:
            if tool_data[0] != "content":
                continue
            results = []
            for t in tool_data[1]:
                results.append({
                    "content": t.text,
                })
            return results
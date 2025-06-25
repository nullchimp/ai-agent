class Tool:
    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def source(self) -> str:
        return self._source

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict:
        return self._parameters

    def __init__(self, 
        name: str = None, 
        description: str = None, 
        parameters: dict = None, 
        session = None,
        source: str = None,
    ):
        self._name = name
        self._description = description
        self._parameters = parameters if parameters is not None else {}
        self._session = session
        self._source = source or "default"

        self._enabled = False

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

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

            return tool_data[1]
        
        return {}
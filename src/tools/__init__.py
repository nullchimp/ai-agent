class Tool:
    def __init__(self, name: str, description: str = None, parameters: dict = None, session = None):
        self.name = name
        self._structure = None
        if name and description and parameters:
            self._structure = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            }
        
        self._session = session

    def define(self):
        return self._structure

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
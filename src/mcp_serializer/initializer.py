class MCPInitializer:
    protocol_default_version = "2024-11-05"

    def __init__(self, protocol_version=None, instructions=None):
        self.protocol_version = protocol_version or self.protocol_default_version
        self.instructions = instructions or ""
        self.server_info = {}
        self.capabilities = {}
        self.result = {}

    def add_server_info(self, name, version, title=None):
        self.server_info = {"name": name, "version": version}
        if title:
            self.server_info["title"] = title
        return self

    def add_prompt(self, list_changed=False):
        self.capabilities["prompts"] = {"listChanged": list_changed}
        return self

    def add_resources(self, subscribe=False, list_changed=False):
        self.capabilities["resources"] = {
            "subscribe": subscribe,
            "listChanged": list_changed,
        }
        return self

    def add_tools(self, list_changed=False):
        self.capabilities["tools"] = {"listChanged": list_changed}
        return self

    def build_result(self, client_params: dict):
        self.result = {
            "protocolVersion": self.protocol_version,
            "capabilities": self.capabilities,
            "serverInfo": self.server_info,
        }
        if self.instructions:
            self.result["instructions"] = self.instructions
        return self.result

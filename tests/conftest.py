import sys
from unittest.mock import MagicMock


# Stub heavy agent-framework deps before agent modules are imported.
# Individual tests mock the specific objects they need; these stubs only
# prevent ImportError during collection in environments where crewai /
# google-genai are not installed.
def _make_tool_stub():
    """Return a @tool decorator stub that preserves the wrapped function as .func."""

    def tool_decorator_factory(name):
        def decorator(func):
            mock = MagicMock()
            mock.func = func
            mock.name = name
            return mock

        return decorator

    return tool_decorator_factory


_mock_crewai_tools = MagicMock()
_mock_crewai_tools.tool = _make_tool_stub()

_STUB_MODULES = {
    'crewai': MagicMock(),
    'crewai.process': MagicMock(),
    'crewai.tools': _mock_crewai_tools,
    'dotenv': MagicMock(),
    'google': MagicMock(),
    'google.genai': MagicMock(),
    'google.genai.types': MagicMock(),
}
for _mod, _stub in _STUB_MODULES.items():
    if _mod not in sys.modules:
        sys.modules[_mod] = _stub

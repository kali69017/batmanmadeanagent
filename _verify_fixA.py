"""Verify Fix A: overwrite=True is properly forwarded from LLM tool call to backend.
"""

import os, sys, tempfile, shutil
from unittest.mock import MagicMock

sys.path.insert(0, "D:\\Fasset")
import agents

agents._apply_monkey_patches()

from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.messages import ToolMessage

tmpdir = tempfile.mkdtemp()

# Use virtual paths (virtual_mode=True)
backend = FilesystemBackend(root_dir=tmpdir, virtual_mode=True)
mw = FilesystemMiddleware(backend=backend)
tool = mw._create_write_file_tool()

# --- Test 1: Schema ---
print("=== Test 1: Schema shows overwrite field ===")
assert "overwrite" in tool.args_schema.model_fields
print("  PASS")

# --- Test 2: _parse_input preserves overwrite=True ---
print("=== Test 2: _parse_input preserves overwrite=True ===")
parsed = tool._parse_input(
    {"file_path": "/test.txt", "content": "new", "overwrite": True}, "test-id"
)
assert parsed.get("overwrite") is True
print("  PASS")

# --- Test 3: _parse_input defaults overwrite=False ---
print("=== Test 3: _parse_input defaults overwrite=False ===")
parsed2 = tool._parse_input({"file_path": "/test.txt", "content": "new"}, "test-id")
assert parsed2.get("overwrite") is False
print("  PASS")

# --- Test 4: Backend without overwrite flag fails ---
print("=== Test 4: Backend without overwrite flag fails ===")
# Create the file via the backend first (virtual path)
res0 = backend.write("/test.txt", "original", overwrite=True)
assert res0.error is None

# Now try without overwrite
res1 = backend.write("/test.txt", "should fail")
assert res1.error and "already exists" in res1.error
print("  PASS")

# --- Test 5: Backend with overwrite=True succeeds ---
print("=== Test 5: Backend with overwrite=True succeeds ===")
res2 = backend.write("/test.txt", "overwritten", overwrite=True)
assert res2.error is None
resolved = os.path.join(tmpdir, "test.txt")
assert open(resolved).read() == "overwritten"
print("  PASS")

# --- Test 6: Backend via thread-local override ---
print("=== Test 6: Backend via thread-local override ===")
agents._write_tls.overwrite = True
try:
    res3 = backend.write("/test.txt", "via tls")  # no overwrite kwarg
    assert res3.error is None
    assert open(resolved).read() == "via tls"
finally:
    agents._write_tls.overwrite = None
print("  PASS")

# --- Test 7: Thread-local cleared, backend fails again ---
print("=== Test 7: Thread-local cleared, backend fails again ===")
res4 = backend.write("/test.txt", "should fail again")
assert res4.error and "already exists" in res4.error
print("  PASS")

# --- Test 8: Full wrapper dispatch with overwrite=True ---
print("=== Test 8: Full wrapper dispatch with overwrite=True ===")


class _FakeRuntime:
    tool_call_id = "test-123"
    state = {}
    config = None
    store = None
    context = None
    stream_writer = None


runtime = _FakeRuntime()

result = tool.func(
    file_path="/test.txt", content="wrapper ok", overwrite=True, runtime=runtime
)
assert isinstance(result, ToolMessage), f"Expected ToolMessage, got {type(result)}"
assert result.status == "success", f"Expected success, got {result.status}"
assert open(resolved).read() == "wrapper ok"
print("  PASS")

# --- Test 9: Wrapper without overwrite ---
print("=== Test 9: Wrapper without overwrite fails ===")
result = tool.func(file_path="/test.txt", content="should fail", runtime=runtime)
assert result.status == "error", "Should have failed"
assert "already exists" in result.content.lower()
print("  PASS")

# --- Test 10: Wrapper with overwrite=False ---
print("=== Test 10: Wrapper with overwrite=False fails ===")
result = tool.func(
    file_path="/test.txt", content="should fail", overwrite=False, runtime=runtime
)
assert result.status == "error"
assert "already exists" in result.content.lower()
print("  PASS")

shutil.rmtree(tmpdir)

print()
print("=" * 50)
print("ALL TESTS PASSED")
print("=" * 50)

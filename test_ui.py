"""Run the GUI flow regression suite explicitly."""
if __name__ == '__main__':
    import pytest
    raise SystemExit(pytest.main(['tests/test_ui_flow.py','-q']))

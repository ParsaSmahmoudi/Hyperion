"""Tests for Hyperion tools"""
import pytest
from hyperion.core.tools import CalculatorTool, CodeExecTool, CurrentTimeTool, ToolRegistry, extract_tool_calls


def test_calculator_basic():
    calc = CalculatorTool()
    assert "4" in calc.run("2+2")
    assert "144" in calc.run("12*12")
    assert "12" in calc.run("sqrt(144)")


def test_calculator_error():
    calc = CalculatorTool()
    result = calc.run("1/0")
    assert "Error" in result or "inf" in result.lower()


def test_code_exec():
    exec_tool = CodeExecTool()
    code = "print('hello world')\nprint(2+2)"
    result = exec_tool.run(code)
    assert "hello world" in result
    assert "4" in result


def test_code_exec_error():
    exec_tool = CodeExecTool()
    result = exec_tool.run("1/0")
    assert "Error" in result or "ZeroDivision" in result or "STDERR" in result


def test_current_time():
    t = CurrentTimeTool()
    result = t.run()
    assert len(result) >= 10
    assert "20" in result  # year


def test_tool_registry_defaults():
    reg = ToolRegistry()
    assert "calculator" in reg.list_tools()
    assert "code_exec" in reg.list_tools()
    assert "web_search" in reg.list_tools()
    assert "current_time" in reg.list_tools()


def test_extract_tool_calls():
    text = "Let me calculate.\nUSE_TOOL[calculator]\nexpression = 5*5\nThen I will continue."
    calls = extract_tool_calls(text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "calculator"
    assert calls[0]["kwargs"]["expression"] == "5*5"


def test_extract_tool_calls_multiple():
    text = "USE_TOOL[calculator]\nexpression = 1+1\nUSE_TOOL[code_exec]\ncode = print('hi')"
    calls = extract_tool_calls(text)
    assert len(calls) == 2
    assert calls[0]["tool"] == "calculator"
    assert calls[1]["tool"] == "code_exec"

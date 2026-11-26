"""
Recipe 01.1: Deep Bytecode Inspection & Opcode Decompiler Engine
File: recipe_01_1_bytecode_inspector.py
Python Version: 3.12+
"""

from __future__ import annotations
import dis
import inspect
import sys
import types
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class DecodedInstruction:
    offset: int
    opname: str
    opcode: int
    arg: Optional[int]
    argval: Any
    argrepr: str
    is_jump_target: bool
    starts_line: Optional[int]
    inline_cache_entries: int


@dataclass(frozen=True)
class CodeObjectTelemetry:
    function_name: str
    filename: str
    first_lineno: int
    stacksize: int
    flags: List[str]
    argcount: int
    posonlyargcount: int
    kwonlyargcount: int
    nlocals: int
    varnames: tuple[str, ...]
    constants: tuple[Any, ...]
    names: tuple[str, ...]
    freevars: tuple[str, ...]
    cellvars: tuple[str, ...]
    instructions: List[DecodedInstruction]


class BytecodeAnalysisEngine:
    """Production engine for reverse engineering and inspecting CPython code objects."""

    COMPILER_FLAGS: Dict[int, str] = {
        inspect.CO_OPTIMIZED: "OPTIMIZED (Fast Locals)",
        inspect.CO_NEWLOCALS: "NEWLOCALS",
        inspect.CO_VARARGS: "VARARGS (*args)",
        inspect.CO_VARKEYWORDS: "VARKEYWORDS (**kwargs)",
        inspect.CO_NESTED: "NESTED_SCOPE",
        inspect.CO_GENERATOR: "GENERATOR",
        inspect.CO_COROUTINE: "COROUTINE",
        inspect.CO_ITERABLE_COROUTINE: "ITERABLE_COROUTINE",
        inspect.CO_ASYNC_GENERATOR: "ASYNC_GENERATOR",
    }

    @classmethod
    def inspect_callable(cls, target: Callable[..., Any]) -> CodeObjectTelemetry:
        """Extracts and decodes complete virtual machine telemetry from a callable."""
        if not hasattr(target, "__code__"):
            raise TypeError(f"Target object {target!r} does not contain an accessible __code__ attribute.")

        code: types.CodeType = target.__code__
        active_flags = [
            desc for flag, desc in cls.COMPILER_FLAGS.items() if code.co_flags & flag
        ]

        # Analyze disassembly with inline caches
        instructions: List[DecodedInstruction] = []
        bytecode_iterator = dis.Bytecode(target, show_caches=True)

        for instr in bytecode_iterator:
            cache_units = 0
            # Identify CACHE opcodes following specialized instructions in 3.12+
            if instr.opname == "CACHE":
                continue

            instructions.append(
                DecodedInstruction(
                    offset=instr.offset,
                    opname=instr.opname,
                    opcode=instr.opcode,
                    arg=instr.arg,
                    argval=instr.argval,
                    argrepr=str(instr.argrepr),
                    is_jump_target=instr.is_jump_target,
                    starts_line=instr.starts_line,
                    inline_cache_entries=cache_units,
                )
            )

        return CodeObjectTelemetry(
            function_name=code.co_name,
            filename=code.co_filename,
            first_lineno=code.co_firstlineno,
            stacksize=code.co_stacksize,
            flags=active_flags,
            argcount=code.co_argcount,
            posonlyargcount=code.co_posonlyargcount,
            kwonlyargcount=code.co_kwonlyargcount,
            nlocals=code.co_nlocals,
            varnames=code.co_varnames,
            constants=code.co_consts,
            names=code.co_names,
            freevars=code.co_freevars,
            cellvars=code.co_cellvars,
            instructions=instructions,
        )

    @classmethod
    def print_telemetry_report(cls, telemetry: CodeObjectTelemetry) -> None:
        """Renders an enterprise audit report of the code object."""
        divider = "=" * 80
        print(divider)
        print(f"CPYTHON 3.12+ CODE OBJECT AUDIT: {telemetry.function_name}()")
        print(f"Location: {telemetry.filename}:{telemetry.first_lineno}")
        print(f"Max Stack Depth: {telemetry.stacksize} slots | Total Fast Locals: {telemetry.nlocals}")
        print(f"Compiler Flags: {', '.join(telemetry.flags) if telemetry.flags else 'None'}")
        print(f"Fast Local Slots: {telemetry.varnames}")
        print(f"Constant Pool: {telemetry.constants}")
        print(divider)
        print(f"{'OFFSET':<8} {'LINE':<6} {'OPCODE NAME':<26} {'ARG':<6} {'REPRESENTATION'}")
        print("-" * 80)
        for ins in telemetry.instructions:
            line_str = str(ins.starts_line) if ins.starts_line else ""
            jump_flag = ">>" if ins.is_jump_target else "  "
            arg_str = str(ins.arg) if ins.arg is not None else ""
            print(f"{jump_flag} {ins.offset:<6} {line_str:<6} {ins.opname:<26} {arg_str:<6} {ins.argrepr}")
        print(divider)


# Production Verification Driver
if __name__ == "__main__":
    def production_fee_calculator(base_amount: float, tier: int, is_vip: bool) -> float:
        """Sample financial transaction scoring function."""
        rate = 0.015 if not is_vip else 0.005
        surcharge = 5.0 if tier > 2 else 1.0
        return (base_amount * rate) + surcharge

    telemetry_data = BytecodeAnalysisEngine.inspect_callable(production_fee_calculator)
    BytecodeAnalysisEngine.print_telemetry_report(telemetry_data)

from typing import Optional, Set, Tuple, Dict
from dataclasses import dataclass
from kira import (ktokenize, 
                  AstNode, kparse, AstAssignment, AstWorkflow, 
                  kbuild_workflow, kbuild_expression, kbuild_assignment, 
                  KObject, KData, KLiteral, KNode, KNodeInstance)
from kira.klanguage.kast import AstExpression
from kproject.kevent import KEvent, KEventTypes
from kproject.kmanager import KManager
from kproject.kdependency_manager import find_dependencies

@dataclass
class VariableState:
    code: str
    ast: AstNode
    dependencies: Set[str]
    kobject: KNodeInstance

@dataclass
class WorkflowState:
    code: str
    ast: AstNode
    dependencies: Set[str]
    kobject: KNode

class KStateManager(KManager):
    """
    Manages the state of symbols using dataclass structures.
    """
    def __init__(self):
        self.variables: Dict[str, VariableState] = {}
        self.workflows: Dict[str, WorkflowState] = {}
        self.data_names: Set[str] = set()

    def process_event(self, event: KEvent):
        match event.type:
            case KEventTypes.AddVariable:
                self._add_variable(event)
            case KEventTypes.AddWorkflow:
                self._add_workflow(event)
            case KEventTypes.UpdateWorkflow:
                self._update_workflow(event)
            case KEventTypes.AddData:
                self._add_data(event)
            case KEventTypes.DeleteVariable:
                self._delete_variable(event)
            case KEventTypes.DeleteWorkflow:
                self._delete_workflow(event)
            case KEventTypes.DeleteData:
                self._delete_data(event)
            case KEventTypes.Store:
                pass
            case _ as v:
                raise TypeError(f"Unhandled event type: {v}")

    def _add_variable(self, event: KEvent):
        assert event.target not in self.variables, f"AddVariable: '{event.target}' already present"
        code = event.body
        tokens = [t for t in ktokenize(code) if t.token_type.name != "WHITESPACE"]
        ast = kparse(tokens)
        assert isinstance(ast, AstAssignment), "AddVariable: Expected AstAssignment"
        
        deps = find_dependencies(ast)
        kobj = kbuild_assignment(ast)

        assert isinstance(kobj, KNodeInstance), "AddVariable: Expected KNodeInstance"
        
        self.variables[event.target] = VariableState(
            code=code,
            ast=ast,
            dependencies=deps,
            kobject=kobj
        )

    def _add_workflow(self, event: KEvent):
        assert event.target not in self.workflows, f"AddWorkflow: '{event.target}' already present"
        code = event.body
        tokens = [t for t in ktokenize(code) if t.token_type.name != "WHITESPACE"]
        ast = kparse(tokens)
        assert isinstance(ast, AstWorkflow), "AddWorkflow: Expected AstWorkflow"
        
        deps = find_dependencies(ast)
        kobj = kbuild_workflow(ast)

        assert isinstance(kobj, KNode), "AddVariable: Expected KNode"
        
        self.workflows[event.target] = WorkflowState(
            code=code,
            ast=ast,
            dependencies=deps,
            kobject=kobj
        )

    def _update_workflow(self, event: KEvent):
        assert event.target in self.workflows, f"UpdateWorkflow: '{event.target}' not found"
        
        code = event.body
        tokens = [t for t in ktokenize(code) if t.token_type.name != "WHITESPACE"]
        ast = kparse(tokens)
        assert isinstance(ast, AstWorkflow), "UpdateWorkflow: Expected AstWorkflow"
        
        deps = find_dependencies(ast)
        kobj = kbuild_workflow(ast)

        assert isinstance(kobj, KNode), "UpdateWorkflow: Expected KNode"
        
        self.workflows[event.target] = WorkflowState(
            code=code,
            ast=ast,
            dependencies=deps,
            kobject=kobj
        )

    def _add_data(self, event: KEvent):
        assert event.target not in self.data_names, f"AddData: '{event.target}' already present"
        self.data_names.add(event.target)

    def _delete_variable(self, event: KEvent):
        assert event.target in self.variables, f"DeleteVariable: '{event.target}' not found"
        del self.variables[event.target]

    def _delete_workflow(self, event: KEvent):
        assert event.target in self.workflows, f"DeleteWorkflow: '{event.target}' not found"
        del self.workflows[event.target]

    def _delete_data(self, event: KEvent):
        assert event.target in self.data_names, f"DeleteData: '{event.target}' not found"
        self.data_names.remove(event.target)

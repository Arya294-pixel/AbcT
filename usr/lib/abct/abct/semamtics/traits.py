# semantics/traits.py
from ..abct_ast.node import (
    TemplateCapablity, ClassDef, 
    AnnAssign, Const, Name,
    Module, Array, TypeRef
)
class TraitError(RuntimeError): pass

class TraitAnalyser:
    def __init__(self):
        # The registry maps class names to their trait lists
        self.registry = {}

    def analyse(self, module: Module):
        """
        Search: Traverses the module for ClassDefs.
        Analyse: Validates the traits for each.
        """
        for stmt in module.stmts:
            if isinstance(stmt, ClassDef):
                self.registry[stmt.name.id] = self._get_traits(stmt)
        return self.registry

    def _get_traits(self, node: ClassDef) -> set[TemplateCapablity]:
        """Analysis logic for a single ClassDef."""
        for attr in node.public_attributes:
            if not isinstance(attr, AnnAssign):
                continue
            
            if attr.target.id != "__trait__":
                continue
            
            # Validation Protocol
            if self.verify_annotation(attr.annotation):
                raise TraitError(f"Protocol violation in {node.name.id}: Annotation mus be CompileTimeConst.")
            if not isinstance(attr.value, Array):
                raise TraitError(f"Protocol violation in {node.name.id}: Value must be an array literal of capability identifiers.")

            traits = set()
            for element in attr.value.elts:
                if not isinstance(element, Name):
                    raise TraitError(f"trait list must contain identifier. Got {type(element).__name__} object")
                try:
                    traits.add(TemplateCapablity[element.id.upper()])
                except KeyError:
                    raise TraitError(f"Unknown capability '{element.id}'")
            return traits
        # Handle implicit "ANY" if no __trait__ is defined
        return {TemplateCapablity.ANY}

    @staticmethod
    def verify_annotation(ann):
        return (
            isinstance(ann, TypeRef)
            and ann.name.id == "CompileTimeConst"
        )

class VerifyTrait:
    def __init__(self, registry: dict):
        self.registry = registry

    def verify(self, node: ClassDef):
        """
        Enforce business rules/constraints on the traits.
        e.g., If 'RUNTIME_CHECK' is present, 'NO_CHECK' is forbidden.
        """
        traits = self.registry.get(node.name.id, [])
        
        # Example Constraint: Mutually Exclusive Protocols
        if TemplateCapablity.RUNTIME_CHECK in traits and TemplateCapablity.NO_CHECK in traits:
            raise TraitError(f"Protocol Violation in {node.name.id}: Cannot have both RUNTIME_CHECK and NO_CHECK")
        
        # Example Constraint: Required pair
        if TemplateCapablity.RUNTIME_CHECK in traits and TemplateCapablity.INTEGER not in traits:
             raise TraitError(f"Protocol Violation in {node.name.id}: RUNTIME_CHECK requires INTEGER trait")

def verify(ast: Module) -> None:
    """
    The orchestrator that runs the verification pass.
    """
    analyser = TraitAnalyser()
    registry = analyser.analyse(ast)
    
    verifier = VerifyTrait(registry)
    for stmt in ast.stmts:
        if isinstance(stmt, ClassDef):
            verifier.verify(stmt)

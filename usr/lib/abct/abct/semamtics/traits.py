# semantics/traits.py
from ..abct_ast.node import (
    TemplateCapablity, ClassDef, 
    AnnAssign, Const, Name,
    Module
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

    def _get_traits(self, node: ClassDef) -> list[TemplateCapablity]:
        """Analysis logic for a single ClassDef."""
        for attr in node.public_attributes:
            if not isinstance(attr, AnnAssign):
                continue
            
            if attr.target != "__trait__":
                continue
            
            # Validation Protocol
            if attr.annotation != "CompileTimeConst":
                raise TraitError(f"Protocol Violation in {node.name.id}: Annotation must be 'CompileTimeConst'")
            
            if not isinstance(attr.value, Const):
                raise TraitError(f"Protocol Violation in {node.name.id}: Value must be a constant")
            
            return self.parse_trait(attr.value.value)

        # Handle implicit "ANY" if no __trait__ is defined
        return [TemplateCapablity.ANY]

    @staticmethod
    def parse_trait(trait_str: str) -> list[TemplateCapablity]:
        """
        Parses a string like "['INTEGER', 'COPYABLE']" into a list of Enums.
        """
        # 1. Clean the input string
        s = trait_str.strip().replace(" ", "").replace("'", '"')
        
        # 2. Basic Validation
        if not (s.startswith("[") and s.endswith("]")):
            raise TraitError(f"Trait declaration must be in format '[...]', got: {trait_str}")
        
        # 3. Extract items
        content = s[1:-1]
        if not content:
            return [TemplateCapablity.UNKNOWN]
        
        traits = set()
        items = content.split(",")
        
        for item in items:
            # Remove quotes and normalize to uppercase
            clean_item = item.replace('"', '').upper()
            
            # Lookup in Enum (defaults to UNKNOWN if not found)
            capability = getattr(TemplateCapablity, clean_item, TemplateCapablity.UNKNOWN)
            traits.add(capability)
            
        return list(sorted(traits, key=lambda x: x.value)) if traits else [TemplateCapablity.UNKNOWN]

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

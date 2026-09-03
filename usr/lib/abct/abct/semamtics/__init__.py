from ..abct_ast import Module
from .nameanalyser import SemanticAnalyser as NameAnalyser

def verify(ast:Module):
    NameAnalyser().verify(ast)
    return

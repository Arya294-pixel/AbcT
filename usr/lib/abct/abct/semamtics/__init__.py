from ..abct_ast import Module
from .nameanalyser import SemanticAnalyser as NameAnalyser
from .enum import verify as EnumVerify

def verify(ast:Module):
    NameAnalyser().verify(ast)
    EnumVerify(ast)
    return

from .traits import verify as TraitVerify, TraitAnalyser
from ..abct_ast import Module

def verify(ast:Module):
    TraitVerify(ast)
    return

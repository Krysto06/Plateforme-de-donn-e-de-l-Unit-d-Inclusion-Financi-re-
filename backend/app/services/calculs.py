"""KPI calculés à partir d'autres séries (ex. GEN-01 = USA-04[H] - USA-04[F]).

La formule est écrite dans la colonne « calcul » du référentiel : on peut donc la changer sans toucher au code.
Seuls les nombres, les références CODE[SEXE], + - * / et les parenthèses sont permis.
"""
import ast
import operator
import re

RE_REFERENCE = re.compile(r"([A-Z]{2,4}-[A-Z0-9]{1,4})\[(F|H|Total)\]")
_OPERATIONS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


class FormuleInvalide(ValueError):
    pass


def references(formule: str) -> list[tuple[str, str]]:
    refs = RE_REFERENCE.findall(formule)
    if not refs:
        raise FormuleInvalide(f"Aucune référence CODE[SEXE] dans « {formule} »")
    return refs


def _evaluer_noeud(noeud: ast.AST) -> float:
    if isinstance(noeud, ast.Expression):
        return _evaluer_noeud(noeud.body)
    if isinstance(noeud, ast.Constant) and isinstance(noeud.value, (int, float)):
        return float(noeud.value)
    if isinstance(noeud, ast.UnaryOp) and isinstance(noeud.op, ast.USub):
        return -_evaluer_noeud(noeud.operand)
    if isinstance(noeud, ast.BinOp) and type(noeud.op) in _OPERATIONS:
        return _OPERATIONS[type(noeud.op)](_evaluer_noeud(noeud.left), _evaluer_noeud(noeud.right))
    raise FormuleInvalide("Seuls les nombres, + - * / et les parenthèses sont permis")


def evaluer(formule: str, valeurs: dict[tuple[str, str], float]) -> float | None:
    """Remplace chaque CODE[SEXE] par sa valeur puis calcule. Rend None si une valeur manque ou division par zéro."""
    expression = formule
    for code, sexe in references(formule):
        if (code, sexe) not in valeurs:
            return None
        expression = expression.replace(f"{code}[{sexe}]", repr(float(valeurs[(code, sexe)])))
    try:
        return _evaluer_noeud(ast.parse(expression, mode="eval"))
    except ZeroDivisionError:
        return None
    except SyntaxError as exc:
        raise FormuleInvalide(f"Formule mal écrite : « {formule} »") from exc

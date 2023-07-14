import ast
import logging
from _ast import AST
from typing import Any, Dict, List


class Rewriter:
    def __init__(self, target_filename: str) -> None:
        self.filename = target_filename
        with open(target_filename, "r") as f:
            self.tree = ast.parse(f.read())
        # prepopulate function dict from the file from walking it up front, let's try to support both top-level funcs and
        # class methods
        mhv = MethodHierarchyVisitor()
        mhv.visit(self.tree)
        self.function_dict = mhv.function_dict

    def get_method(self, method_path: str) -> str:
        node = self.function_dict[method_path]
        return ast.unparse(node)

    def update_method(self, method_path: str, new_code: str) -> None:
        node = self.function_dict[method_path]
        new_node = ast.parse(new_code)
        # TODO: the agent has a habit of returning more than asked for so we should parse out just imports + method from the new code
        self.function_dict[method_path] = new_node  # type: ignore

    def rewrite_file(self) -> None:
        new_tree = MethodHierarchyTransformer(self.function_dict).visit(self.tree)
        self.tree = new_tree
        with open(self.filename, "w") as f:
            f.write(ast.unparse(new_tree))


class MethodHierarchyTransformer(ast.NodeTransformer):
    def __init__(self, function_dict: Dict[str, ast.FunctionDef]) -> None:
        self.class_path: List[str] = []
        self.function_dict = function_dict
        self.logger = logging.getLogger(MethodHierarchyVisitor.__name__)

    def generic_visit(self, node: AST) -> AST:
        self.logger.debug(f"Visiting {node} - with {self.class_path}")
        return super().generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        self.class_path.append(node.name)
        self.generic_visit(node)
        self.class_path.pop()
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # Note that for our code-editing purposes we don't need to fetch within-function nodes currently
        path = ".".join(self.class_path + [node.name])
        # TODO: clean up the logic around replacing; the way this is implemented currently doesn't actually require the up-front parse
        # TODO: we can probably clean this up at the same time as moving to LibCST or one of the other options mentioned at the bottom of
        # TODO: https://docs.python.org/3/library/ast.html to rewrite-in-place with disturbing the formatting less
        if path in self.function_dict:
            return self.function_dict[path]
        else:
            return node


class MethodHierarchyVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.class_path: List[str] = []
        self.function_dict: Dict[str, ast.FunctionDef] = {}
        self.logger = logging.getLogger(MethodHierarchyVisitor.__name__)

    def generic_visit(self, node: AST) -> Any:
        self.logger.debug(f"Visiting {node} - with {self.class_path}")
        super().generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_path.append(node.name)
        self.generic_visit(node)
        self.class_path.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Note that for our code-editing purposes we don't need to fetch within-function nodes currently
        path = ".".join(self.class_path + [node.name])
        self.function_dict[path] = node


if __name__ == "__main__":
    r = Rewriter("target.py")
    new_method_contents = """
def do_it(self) -> str:
    return 'yo'"""
    r.update_method("JobDoer.do_it", new_method_contents)
    r.rewrite_file()

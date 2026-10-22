"""Small source-declared preamble state, not package or macro execution.

Only positive definition facts and explicit newif assignments are usable.
Absence from this table NEVER means undefined in TeX's runtime.
"""
import re

from .tex_lexical import PRIMITIVES, structural

COMMAND = re.compile(r'\\([a-zA-Z]+)|\\.|[{}]')
TARGET = re.compile(r'\s*\\([a-zA-Z]+)(?![a-zA-Z])')
DEFINITIONS = {'def', 'gdef', 'edef', 'xdef', 'newcommand', 'renewcommand',
               'providecommand', 'DeclareRobustCommand'}


def group_end(code, start):
    depth = 0
    for match in COMMAND.finditer(code, start):
        if match[0] == '{':
            depth += 1
        elif match[0] == '}':
            depth -= 1
            if depth == 0:
                return match.end()
    raise ValueError('Unterminated preamble declaration')


class PreambleState:
    def __init__(self):
        self.defined = set()
        self.values = {}
        self.tainted = set()
        self.mutators = set()
        self.dependencies = {}
        self.calls = set()
        self.unsupported = False

    def finalize(self):
        while True:
            expanded = self.mutators | {name for name, refs in self.dependencies.items()
                                       if refs.intersection(self.mutators)}
            if expanded == self.mutators:
                break
            self.mutators = expanded
        if self.calls.intersection(self.mutators | self.defined):
            self.unsupported = True
            self.defined.clear()
            self.values.clear()

    def invalidate(self, name):
        if name in PRIMITIVES:
            self.unsupported = True
        self.defined.discard(name)
        self.values.pop(name, None)
        self.tainted.add(name)
        setter = re.fullmatch(r'([a-zA-Z]+)(true|false)', name)
        if setter:
            flag = 'if' + setter[1]
            if flag in self.values:
                self.values.pop(flag)
                self.tainted.add(flag)

    def read(self, text, include):
        """Follow direct preamble includes in order; skip macro replacement bodies.

        Unknown conditionals do not contribute state. Scoped declarations and
        unsupported mutations invalidate facts instead of inventing global state.
        """
        _, code, _ = structural(text)
        stack, cursor, depth = [], 0, 0
        for match in COMMAND.finditer(code):
            if match.start() < cursor:
                continue
            token, command = match[0], match[1]
            active = all(value is True for value, _ in stack)
            if (command and command not in PRIMITIVES and command not in self.values
                    and not (command in self.tainted and command.startswith('if'))
                    and all(value is not False for value, _ in stack)):
                self.calls.add(command)
            if command in ('begingroup', 'bgroup', 'endgroup', 'egroup'):
                depth += 1 if command in ('begingroup', 'bgroup') else -1
                if depth < 0:
                    raise ValueError('Unmatched preamble group')
                continue
            if token in ('{', '}'):
                depth += 1 if token == '{' else -1
                continue
            if command in ('input', 'include'):
                arg = re.match(r'\s*\{([^{}]+)\}', code[match.end():])
                if active and depth == 0:
                    if arg is None:
                        raise ValueError('Unsupported preamble include syntax')
                    include(arg[1], self)
                elif active or any(v is None for v, _ in stack):
                    self.unsupported = True
                    # Unknown branches and groups may load state-mutating files.
                    # Includes in a group could mutate flags with global assigns.
                    self.defined.clear()
                    self.values.clear()
                if arg:
                    cursor = match.end() + arg.end()
                continue
            if command in DEFINITIONS:
                pos = match.end()
                # LaTeX declarations may wrap the target control sequence.
                wrapper = re.match(r'\s*\{\s*\\([a-zA-Z]+)\s*\}', code[pos:])
                target = wrapper or TARGET.match(code, pos)
                if target is None:
                    self.defined.clear()
                    self.values.clear()
                    continue
                name = target[1]
                if name in PRIMITIVES:
                    self.unsupported = True
                pos = pos + wrapper.end() if wrapper else target.end()
                # Skip argument counts/defaults as syntax, not replacement
                # text. Unsupported nested defaults invalidate discovery.
                if command not in ('def', 'gdef', 'edef', 'xdef'):
                    pos += len(code[pos:]) - len(code[pos:].lstrip())
                    while pos < len(code) and code[pos] == '[':
                        option = re.match(r'\[[^\[\]]*\]\s*', code[pos:])
                        if option is None:
                            raise ValueError('Unsupported macro argument default')
                        pos += option.end()
                opening = code.find('{', pos)
                if opening < 0:
                    raise ValueError('Unsupported preamble declaration')
                cursor = group_end(code, opening)
                replacement = code[opening:cursor]
                self.dependencies[name] = set(re.findall(r'\\([a-zA-Z]+)', replacement))
                if re.search(r'\\(?:csname|catcode|unless|usepackage|documentclass|futurelet|input|include|newif|let|def|gdef|edef|xdef|newcommand|renewcommand|providecommand|DeclareRobustCommand|[A-Za-z]+true|[A-Za-z]+false)(?![A-Za-z])', replacement):
                    self.mutators.add(name)
                # No effects from definitions, inactive branches, or arguments.
                if active and depth == 0 and command in ('def', 'gdef', 'newcommand', 'renewcommand', 'DeclareRobustCommand'):
                    self.defined.add(name)
                elif active or any(v is None for v, _ in stack):
                    self.defined.discard(name)
                if name in self.values and (active or any(v is None for v, _ in stack)):
                    self.values.pop(name)
                    self.tainted.add(name)
                setter = re.fullmatch(r'([a-zA-Z]+)(true|false)', name)
                if setter and (active or any(v is None for v, _ in stack)):
                    self.invalidate('if' + setter[1])
                continue
            if command == 'newif':
                target = TARGET.match(code, match.end())
                if target is None or not target[1].startswith('if'):
                    raise ValueError('Unsupported newif declaration')
                cursor = target.end()
                name = target[1]
                if name in PRIMITIVES:
                    self.unsupported = True
                if active and depth == 0:
                    self.values[name] = False
                    self.defined.add(name)
                elif active or any(v is None for v, _ in stack):
                    self.values.pop(name, None)
                    self.tainted.add(name)
                continue
            if command in PRIMITIVES or command in self.values or (command in self.tainted and command.startswith('if')):
                value = {'iftrue': True, 'iffalse': False}.get(command, self.values.get(command))
                if command == 'ifdefined':
                    target = TARGET.match(code, match.end())
                    if target:
                        cursor = target.end()
                        value = True if target[1] in self.defined else None
                stack.append([value, False])
                continue
            if command == 'else':
                if not stack or stack[-1][1]:
                    raise ValueError('Unmatched preamble else')
                value, _ = stack[-1]
                stack[-1] = [not value if value is not None else None, True]
                continue
            if command == 'fi':
                if not stack:
                    raise ValueError('Unmatched preamble fi')
                stack.pop()
                continue
            setter = re.fullmatch(r'([a-zA-Z]+)(true|false)', command or '')
            if setter and 'if' + setter[1] in self.defined:
                name = 'if' + setter[1]
                if active and depth == 0 and name not in self.tainted:
                    self.values[name] = setter[2] == 'true'
                elif (not active and any(v is None for v, _ in stack)) or (active and depth):
                    self.values.pop(name, None)
                    self.tainted.add(name)
            elif command in ('let', 'futurelet'):
                target = TARGET.match(code, match.end())
                if target:
                    if active or any(v is None for v, _ in stack):
                        self.invalidate(target[1])
                    source = re.match(r'\s*=?\s*\\(?:[a-zA-Z@]+|.)', code[target.end():])
                    if source and (active or any(v is None for v, _ in stack)):
                        alias = re.search(r'\\([a-zA-Z]+)', source[0])
                        if alias:
                            self.dependencies[target[1]] = {alias[1]}
                            if alias[1] in {'input', 'include', 'csname', 'let', 'futurelet'}:
                                self.mutators.add(target[1])
                            if re.fullmatch(r'[a-zA-Z]+(?:true|false)', alias[1]):
                                self.invalidate(alias[1])
                    cursor = target.end() + (source.end() if source else 0)
            elif command in self.mutators or command in ('csname', 'unless', 'catcode', 'usepackage', 'documentclass'):
                if active or any(v is None for v, _ in stack):
                    self.defined.clear()
                    self.values.clear()
        if stack:
            raise ValueError('Unterminated preamble conditional')
        if depth:
            raise ValueError('Unterminated preamble group')

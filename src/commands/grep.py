from commands.cmd import Cmd
import re


class Grep(Cmd):
    def __init__(self, args, flags, options, stdin):
        super().__init__(args, flags, options, stdin)

        self.ignore_case = '-i' in flags
        self.count_only = '-c' in flags
        self.files_with_matches = '-l' in flags
        self.word_regexp = '-w' in flags
        self.after_context = 0

        for opt in options:
            if opt.startswith('-A'):
                try:
                    self.after_context = int(opt[2:])
                except ValueError:
                    pass

        self.pattern = args[0] if args else None
        self.files = args[1:] if len(args) > 1 else []

    def run(self):
        if not self.pattern:
            return "grep: missing pattern\n"

        regex_flags = re.IGNORECASE if self.ignore_case else 0
        pattern = r'\b{}\b'.format(re.escape(self.pattern)) if self.word_regexp else self.pattern

        try:
            compiled_pattern = re.compile(pattern, regex_flags)
        except re.error:
            return "grep: invalid pattern\n"

        if not self.files and not self.stdin:
            return "grep: missing file operand\n"

        matches = []

        def process_content(content, filename=None):
            lines = content.split('\n')
            result = []
            last_match_pos = -self.after_context - 2

            for i, line in enumerate(lines):
                if compiled_pattern.search(line):
                    if i - last_match_pos > self.after_context + 1 and result:
                        result.append("--")

                    result.append(f"{filename}:{line}" if filename else line)

                    for j in range(i + 1, min(i + 1 + self.after_context, len(lines))):
                        result.append(f"{filename}:{lines[j]}" if filename else lines[j])

                    last_match_pos = i

            return result

        if not self.files and self.stdin:
            result = process_content(self.stdin)
            if self.count_only:
                count = len([x for x in result if not x.startswith('--')])
                return f"{count}\n"
            elif self.files_with_matches:
                return ""
            return "\n".join(result) + "\n" if result else ""

        for file in self.files:
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    result = process_content(content, file)

                    if self.files_with_matches:
                        if any(not line.startswith('--') for line in result):
                            matches.append(file)
                    elif self.count_only:
                        count = len([x for x in result if not x.startswith('--')])
                        matches.append(f"{file}:{count}")
                    else:
                        matches.extend(result)
            except FileNotFoundError:
                matches.append(f"grep: {file}: No such file or directory")

        if self.files_with_matches:
            return "\n".join(matches) + "\n" if matches else ""
        elif self.count_only:
            return "\n".join(matches) + "\n" if matches else "0\n"
        else:
            return "\n".join(matches) + "\n" if matches else ""
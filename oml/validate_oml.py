import sys

import oml_lang

errors = oml_lang.analyze(open(sys.argv[1]).read()).errors()
for message in errors:
    start = message.start()
    print(f"{start.line() + 1}:{start.column() + 1} {message.message()}")
print(f"{len(errors)} error(s)")
sys.exit(1 if errors else 0)

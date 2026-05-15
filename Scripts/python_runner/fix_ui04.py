import pathlib

p = pathlib.Path('Scripts/python_runner/ui04_durchstich_sekretariat_anwalt_ruecklauf.py')
lines = p.read_text(encoding='utf-8').split('\n')

for i, line in enumerate(lines):
    if 'HTML_ESCAPE' in line:
        d = chr(34)
        s = chr(39)
        new_line = (
            'HTML_ESCAPE = str.maketrans({' + d + '&' + d + ': ' + d + '&' + d + ', '
            + d + '<' + d + ': ' + d + '<' + d + ', '
            + d + '>' + d + ': ' + d + '>' + d + ', '
            + s + d + s + ': ' + d + '"' + d + ', '
            + s + s + s + ': ' + d + ''' + d + '})'
        )
        lines[i] = new_line
        break

p.write_text('\n'.join(lines), encoding='utf-8')
print('Fixed HTML_ESCAPE')

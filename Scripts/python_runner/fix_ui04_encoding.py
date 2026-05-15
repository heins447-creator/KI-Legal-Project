import re

path = 'Scripts/python_runner/ui04_durchstich_sekretariat_anwalt_ruecklauf.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

c34 = chr(34)
c39 = chr(39)
c38 = chr(38)
c10 = chr(10)

new_line = (
    'HTML_ESCAPE = str.maketrans({' + c34 + '&' + c34 + ': ' + c34 + c38 + 'amp;' + c34 + ', ' +
    c34 + '<' + c34 + ': ' + c34 + c38 + 'lt;' + c34 + ', ' +
    c34 + '>' + c34 + ': ' + c34 + c38 + 'gt;' + c34 + ', ' +
    c39 + c34 + c39 + ': ' + c34 + c38 + 'quot;' + c34 + ', ' +
    c34 + c39 + c34 + ': ' + c34 + c38 + '#39;' + c34 + '})' + c10
)

pattern = 'HTML_ESCAPE = str.maketrans\\(\\{.*?\\}\\)\\n'
content = re.sub(pattern, new_line, content)

content = content.replace(chr(8211), '-')
content = content.replace(chr(8212), '-')
content = content.replace(chr(8594), '->')
content = content.replace(chr(8592), '<-')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('UI04 repariert')

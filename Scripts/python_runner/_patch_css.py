import sys
path = r'I:\KI_Legal_Project\Scripts\python_runner\ui03_1_anwalts_dreiansicht.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

idx = content.find('CSS = r')
old_end = content.index('\n\n#', idx + 5000)

css_path = r'I:\KI_Legal_Project\Agentensteuerung\UI03_Mandantenakte\20_Anwalts_Dreiansicht\14_Browseransicht\ui03_1.css'
with open(css_path, encoding='utf-8') as f:
    new_css = f.read()

new_block = 'CSS = r"""' + new_css + '"""'
content = content[:idx] + new_block + content[old_end:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('CSS-Block ersetzt. Alte Grenzen:', idx, old_end, 'Neue Länge:', len(content))

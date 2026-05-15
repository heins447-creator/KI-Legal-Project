dq = chr(34)
sq = chr(39)
new_line = (
    'HTML_ESCAPE = str.maketrans({"&": "&", "<": "<", ">": ">", '
    + sq + dq + sq + ': ' + dq + '"' + dq + ', '
    + sq + sq + ': ' + dq + ''' + dq + '})\n'
)
lines = open('Scripts/python_runner/ui04_durchstich_sekretariat_anwalt_ruecklauf.py', 'r', encoding='utf-8').readlines()
lines[189] = new_line
open('Scripts/python_runner/ui04_durchstich_sekretariat_anwalt_ruecklauf.py', 'w', encoding='utf-8').writelines(lines)
print('Zeile 190 korrigiert')

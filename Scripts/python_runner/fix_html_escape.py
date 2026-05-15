lines = open('Scripts/python_runner/ui04_durchstich_sekretariat_anwalt_ruecklauf.py', 'r', encoding='utf-8').readlines()
lines[189] = 'HTML_ESCAPE = str.maketrans({"&": "&", "<": "<", ">": ">", \'"\': """, "\'": "'"})\n'
open('Scripts/python_runner/ui04_durchstich_sekretariat_anwalt_ruecklauf.py', 'w', encoding='utf-8').writelines(lines)
print('Zeile 190 ersetzt')

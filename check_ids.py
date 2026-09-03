import re

with open(r'c:\Users\Administrator\Downloads\mastermind\omnibrain\web\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open(r'c:\Users\Administrator\Downloads\mastermind\omnibrain\web\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

js_ids = re.findall(r'getElementById\([\'"]([^\'"]+)[\'"]\)', js)
html_ids = set(re.findall(r'id=[\'"]([^\'"]+)[\'"]', html))

print("Total getElementById in JS:", len(js_ids))
missing = [i for i in js_ids if i not in html_ids]
print("Missing IDs:", missing)

# Check classes
js_classes = re.findall(r'querySelectorAll\([\'"]\.([a-zA-Z0-9_-]+)[\'"]\)', js)
html_classes = set(re.findall(r'class=[\'"]([^\'"]+)[\'"]', html))
all_html_classes = set()
for c_group in html_classes:
    for c in c_group.split():
        all_html_classes.add(c)

print("Missing Classes:", [c for c in js_classes if c not in all_html_classes])

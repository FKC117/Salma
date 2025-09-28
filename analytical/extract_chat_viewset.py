with open('analytics/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
start = -1
for i, line in enumerate(lines):
    if 'class ChatViewSet' in line:
        start = i
        break

if start >= 0:
    print(f"Found ChatViewSet at line {start + 1}")
    for i in range(start, min(start + 45, len(lines))):
        print(f"{i+1:4}: {lines[i].rstrip()}")
else:
    print("ChatViewSet not found")
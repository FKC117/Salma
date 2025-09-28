with open('analytics/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
start = -1
for i, line in enumerate(lines):
    if 'class ChatViewSet' in line:
        start = i
        break

if start >= 0:
    print(f"Found ChatViewSet at line {start + 1}")
    # Print more lines to see the complete method
    for i in range(start + 35, min(start + 65, len(lines))):
        print(f"{i+1:4}: {lines[i].rstrip()}")
else:
    print("ChatViewSet not found")
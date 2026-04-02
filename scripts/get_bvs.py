import subprocess
import json
import re

url = "https://space.bilibili.com/1140672573/video"

result = subprocess.run(
    ['curl', '-s', url],
    capture_output=True,
    text=True
)

html = result.stdout

bv_pattern = r'BV[\w]+'
titles_pattern = r'"title":"([^"]+)"'

bvs = re.findall(bv_pattern, html)
titles = re.findall(titles_pattern, html)

print(f"找到 {len(bvs)} 个BV号")
for i, (bv, title) in enumerate(zip(bvs[:20], titles[:20])):
    print(f"{i+1}. {title[:40]} - {bv}")

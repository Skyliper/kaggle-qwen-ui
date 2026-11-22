from pathlib import Path
import sys,shutil
r=Path(sys.argv[1]);out=r/'out'
for p in out.rglob('*.html'):
 s=p.read_text(encoding='utf-8')
 guard='<script>if(!sessionStorage.getItem("qwen-chat-config")){location.replace("/kaggle-qwen-ui/")}</script>'
 s=s.replace('<head>','<head>'+guard,1);p.write_text(s,encoding='utf-8')
shutil.copyfile(r/'LICENSE',out/'NEXTCHAT-LICENSE.txt')

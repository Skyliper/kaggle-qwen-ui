from pathlib import Path
import sys,shutil
r=Path(sys.argv[1]);out=r/'out'
for p in out.rglob('*.html'):
 s=p.read_text(encoding='utf-8')
 guard='<script>if(!sessionStorage.getItem("qwen-chat-config")){location.replace("/kaggle-qwen-ui/")}</script>'
 s=s.replace('<head>','<head>'+guard+'<link rel="stylesheet" href="/kaggle-qwen-ui/chat/qwen-theme.css">',1);p.write_text(s,encoding='utf-8')
shutil.copyfile(r/'LICENSE',out/'NEXTCHAT-LICENSE.txt')

shutil.copyfile(Path(__file__).with_name('qwen-theme.css'),out/'qwen-theme.css')

shutil.copyfile(r/"node_modules/pdfjs-dist/build/pdf.worker.min.mjs",out/"pdf.worker.min.mjs")

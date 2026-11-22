"use strict";
const $=id=>document.getElementById(id),repo='Skyliper/kaggle-qwen';let pat='',timer=null;
const decode=f=>JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(f.content.replace(/\s/g,'')),c=>c.charCodeAt(0))));
async function github(path){const r=await fetch('https://api.github.com/repos/'+repo+'/contents/'+path,{cache:'no-store',headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+pat,'X-GitHub-Api-Version':'2022-11-28'}});if(!r.ok)throw Error(r.status===401?'Токен недействителен или истёк.':r.status===404?'Нет доступа к приватному репозиторию или конфигурация чата ещё не подготовлена.':'GitHub временно недоступен ('+r.status+').');return decode(await r.json())}
async function status(){try{const s=await github('status.json'),fresh=Date.now()-Date.parse(s.updated_at)<300000;const online=s.status==='online'&&fresh;$('server-state').textContent=online?'● Сервер online':s.status==='starting'?'◌ Загружается':'○ Сервер offline';$('server-state').dataset.state=online?'online':'offline';sessionStorage.setItem('qwen-server-state',$('server-state').textContent);}catch{$('server-state').textContent='○ Нет статуса'}}
function show(tab){const server=tab==='server';$('client').src=server?'server.html':'chat/#/chat';$('client').title=server?'Управление сервером Kaggle':'Чат Qwen';$('chat-tab').classList.toggle('selected',!server);$('server-tab').classList.toggle('selected',server)}
async function login(token){pat=token.trim();if(!pat)throw Error('Введите GitHub PAT.');const config=await github('web-client.json');if(config.baseUrl!=='https://kaggle-qwen-gateway.kaggle-gateway.workers.dev'||!config.apiKey||config.model!=='qwen3.8-27b-uncensored')throw Error('Неверная приватная конфигурация чата.');sessionStorage.setItem('qwen-gh-pat',pat);sessionStorage.setItem('qwen-chat-config',JSON.stringify(config));localStorage.removeItem('kaggle-qwen-github-pat');$('pat').value='';$('login').hidden=true;$('workspace').hidden=false;show('chat');await status();clearInterval(timer);timer=setInterval(status,30000)}
$('auth').onsubmit=async e=>{e.preventDefault();$('enter').disabled=true;$('login-error').textContent='';try{await login($('pat').value)}catch(e){$('login-error').textContent=e.message}finally{$('enter').disabled=false}};
$('reveal').onclick=()=>{$('pat').type=$('pat').type==='password'?'text':'password'};
$('chat-tab').onclick=()=>show('chat');$('server-tab').onclick=()=>show('server');
$('logout').onclick=()=>{clearInterval(timer);$('client').removeAttribute('src');sessionStorage.removeItem('qwen-gh-pat');sessionStorage.removeItem('qwen-chat-config');localStorage.removeItem('kaggle-qwen-github-pat');pat='';$('workspace').hidden=true;$('login').hidden=false;$('login-error').textContent=''};
const remembered=sessionStorage.getItem('qwen-gh-pat')||localStorage.getItem('kaggle-qwen-github-pat');if(remembered){$('enter').disabled=true;login(remembered).catch(e=>{$('login-error').textContent=e.message}).finally(()=>{$('enter').disabled=false})}

$('web-enabled').checked=localStorage.getItem('qwen-web-enabled')!=='false';
sessionStorage.setItem('qwen-web-enabled',String($('web-enabled').checked));
$('web-enabled').onchange=()=>{const v=String($('web-enabled').checked);sessionStorage.setItem('qwen-web-enabled',v);localStorage.setItem('qwen-web-enabled',v)};

window.addEventListener('message',event=>{if(event.origin!==location.origin||event.source!==$('client').contentWindow)return;if(event.data?.type==='qwen-logout')$('logout').click()});

sessionStorage.setItem("qwen-onion-enabled",String(localStorage.getItem("qwen-onion-enabled")==="true"));

sessionStorage.setItem("qwen-effort",localStorage.getItem("qwen-effort")||"medium");

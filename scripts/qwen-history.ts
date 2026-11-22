import { get } from "idb-keyval";
import { qwenSession } from "./qwen-session";

export const historyKey = "chat-next-web-store";
type Chat = {id:string;messages:any[]};
type Row = {id:string;revision:string;session:Chat};
let baseline = new Map<string,Row>();
let loaded = false;
let queued: string | undefined;
let timer: ReturnType<typeof setTimeout> | undefined;
let saving = false;
let blocked = false;
const checkpointAt = new Map<string,number>();
export function cloudHistoryLoaded(){return loaded;}

function status(message:string) {
  window.dispatchEvent(new CustomEvent("qwen-history-status",{detail:message}));
}

async function api(body?:unknown) {
  const pat = sessionStorage.getItem("qwen-gh-pat");
  if(!pat) throw Error("Войди через GitHub.");
  const payload = body === undefined ? undefined : JSON.stringify(body);
  const response = await fetch(qwenSession().baseUrl+"/__chat_history", {
    method: body === undefined ? "GET" : "POST",
    headers: {Authorization:"Bearer "+pat,"Content-Type":"application/json"},
    body:payload,
    keepalive:payload !== undefined && new TextEncoder().encode(payload).length < 60000,
    cache:"no-store",
  });
  if(response.status===409) throw Error("Диалог изменён на другом устройстве. Скопируй несохранённый ответ перед обновлением страницы.");
  if(response.status===413) throw Error("Диалог слишком большой для облачного сохранения.");
  if(!response.ok) throw Error("Облачная история временно недоступна.");
  return response.json();
}

if(typeof window!=="undefined"){
  window.addEventListener("pagehide",()=>void flush());
}

export async function loadQwenHistory() {
  const {chats} = await api() as {chats:Row[]};
  baseline = new Map(chats.map(row=>[row.id,row]));
  loaded = true;
  blocked = false;
  return JSON.stringify({version:3.3,state:chats.length?{sessions:chats.map(({session})=>({...session,messages:session.messages.map(message=>message.streaming?{...message,streaming:false,content:(message.content||"")+"\n\n_Ответ был прерван. Можно повторить запрос._"}:message)})),currentSessionIndex:0}:{}});
}

export function saveQwenHistory(value:string) {
  if(!loaded||blocked)return;
  queued=value;
  const sessions:Chat[]=JSON.parse(value).state.sessions;
  const hasNewTurn=sessions.some(chat=>chat.messages.length>(baseline.get(chat.id)?.session.messages.length??0)&&chat.messages.some(message=>message.streaming));
  if(hasNewTurn&&!saving){void flush();return;}
  if(!saving&&!timer)timer=setTimeout(()=>void flush(),120);
}

async function flush(){
  clearTimeout(timer);
  timer=undefined;
  if(saving||!queued||blocked)return;
  const value=queued;
  queued=undefined;
  saving=true;
  try{
    const sessions:Chat[]=JSON.parse(value).state.sessions;
    const current=new Set(sessions.map(chat=>chat.id));
    for(const session of sessions){
      const previous=baseline.get(session.id);
      const running=session.messages.some(message=>message.streaming);
      if(running && previous?.session.messages.length===session.messages.length && Date.now()-(checkpointAt.get(session.id)||0)<5000)continue;
      if((!previous&&!session.messages.length)||JSON.stringify(previous?.session)===JSON.stringify(session))continue;
      const {revision}=await api({id:session.id,expected:previous?.revision,session});
      baseline.set(session.id,{id:session.id,revision,session});
      checkpointAt.set(session.id,Date.now());
    }
    for(const [id,previous] of baseline){
      if(current.has(id))continue;
      await api({id,expected:previous.revision,session:null});
      baseline.delete(id);
    }
    status("История сохранена в облаке");
  }catch(error){
    const message=(error as Error).message;
    status(message);
    if(message.startsWith("Диалог"))blocked=true;
    else {queued??=value;timer=setTimeout(()=>void flush(),6000)}
    return;
  }finally{saving=false}
  if(queued&&!timer)timer=setTimeout(()=>void flush(),120);
}

export async function importQwenHistory(){
  if(!loaded) throw Error("Облачная история не загружена. Обнови страницу.");
  const legacy=(await get(historyKey))||localStorage.getItem(historyKey);
  if(!legacy)return 0;
  const {chats}=await api() as {chats:Row[]};
  const known=new Set(chats.map(row=>row.id));
  let count=0;
  for(const session of JSON.parse(legacy).state.sessions as Chat[]){
    if(!session.messages?.length||known.has(session.id))continue;
    await api({id:session.id,session});
    count++;
  }
  return count;
}

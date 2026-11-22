import { get } from "idb-keyval";
import { qwenSession } from "./qwen-session";

export const historyKey = "chat-next-web-store";
type Chat = {id:string;messages:any[]};
type Row = {id:string;revision:string;session:Chat};
let baseline = new Map<string,Row>();
let loaded = false;
let queued: string | undefined;
let timer: ReturnType<typeof setTimeout>;
let saving = false;
let blocked = false;
export function cloudHistoryLoaded(){return loaded;}

function status(message:string) {
  window.dispatchEvent(new CustomEvent("qwen-history-status",{detail:message}));
}

async function api(body?:unknown) {
  const pat = sessionStorage.getItem("qwen-gh-pat");
  if(!pat) throw Error("Войди через GitHub.");
  const response = await fetch(qwenSession().baseUrl+"/__chat_history", {
    method: body === undefined ? "GET" : "POST",
    headers: {Authorization:"Bearer "+pat,"Content-Type":"application/json"},
    body:body === undefined ? undefined : JSON.stringify(body),
    cache:"no-store",
  });
  if(response.status===409) throw Error("Диалог изменён на другом устройстве. Скопируй несохранённый ответ перед обновлением страницы.");
  if(response.status===413) throw Error("Диалог слишком большой для облачного сохранения.");
  if(!response.ok) throw Error("Облачная история временно недоступна.");
  return response.json();
}

export async function loadQwenHistory() {
  const {chats} = await api() as {chats:Row[]};
  baseline = new Map(chats.map(row=>[row.id,row]));
  loaded = true;
  blocked = false;
  return JSON.stringify({version:3.3,state:chats.length?{sessions:chats.map(row=>row.session),currentSessionIndex:0}:{}});
}

export function saveQwenHistory(value:string) {
  if(!loaded||blocked)return;
  queued=value;
  clearTimeout(timer);
  timer=setTimeout(()=>void flush(),300);
}

async function flush(){
  if(saving||!queued||blocked)return;
  const value=queued;
  queued=undefined;
  saving=true;
  try{
    const sessions:Chat[]=JSON.parse(value).state.sessions;
    const current=new Set(sessions.map(chat=>chat.id));
    for(const session of sessions){
      if(session.messages.some(message=>message.streaming))continue;
      const previous=baseline.get(session.id);
      if((!previous&&!session.messages.length)||JSON.stringify(previous?.session)===JSON.stringify(session))continue;
      const {revision}=await api({id:session.id,expected:previous?.revision,session});
      baseline.set(session.id,{id:session.id,revision,session});
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
  if(queued)void flush();
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

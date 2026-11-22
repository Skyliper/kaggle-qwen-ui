import { qwenSession } from "./qwen-session";

export type QwenJob = {
  status:"queued"|"running"|"complete"|"error"|"cancelled";
  answer:string;
  reasoning:string;
  error?:string;
};

async function request(id:string, method:string, data?:unknown, signal?:AbortSignal) {
  const body=data===undefined?undefined:JSON.stringify(data);
  return fetch(qwenSession().baseUrl+"/__chat_job/"+encodeURIComponent(id),{
    method,
    headers:{Authorization:"Bearer "+sessionStorage.getItem("qwen-gh-pat"),"Content-Type":"application/json"},
    body,
    keepalive:body!==undefined&&new TextEncoder().encode(body).length<60000,
    cache:"no-store",
    signal,
  });
}

export function qwenJobText(job:QwenJob) {
  const reasoning=job.reasoning ? job.reasoning.split("\n").map(line=>"> "+line).join("\n")+"\n\n" : "";
  return reasoning+job.answer+(job.error?"\n\nОшибка: "+job.error:"")+(job.status==="cancelled"?"\n\n_Ответ остановлен._":"");
}

export async function watchQwenJob(id:string,onUpdate:(job:QwenJob)=>void,signal:AbortSignal) {
  let failures=0;
  while(!signal.aborted){
    try{
      const response=await request(id,"GET",undefined,signal);
      if(response.status===404){
        if(++failures>4)return {status:"error",answer:"",reasoning:"",error:"Запрос не был принят или срок хранения истёк."} as QwenJob;
      }else if(response.status===401||response.status===403){
        return {status:"error",answer:"",reasoning:"",error:"Войди через GitHub, чтобы открыть ответ."} as QwenJob;
      }else if(response.ok){
        failures=0;
        const job:QwenJob=await response.json();
        onUpdate(job);
        if(job.status!=="running"&&job.status!=="queued")return job;
      }
    }catch{
      if(signal.aborted)return;
    }
    await new Promise(resolve=>setTimeout(resolve,5000));
  }
}

export async function runQwenJob(id:string,payload:unknown,options:{onUpdate?:(text:string,chunk:string)=>void;onFinish:(text:string,response:Response)=>void;onError?:(error:Error)=>void},signal:AbortSignal){
  function stop(){void request(id,"DELETE").catch(()=>{})}
  // Only the explicit Stop action triggers this abort controller.
  signal.addEventListener("abort",stop,{once:true});
  try{
    const response=await request(id,"POST",payload);
    if(!response.ok)throw Error("Облачный запуск не принят (HTTP "+response.status+").");
    if(signal.aborted){stop();return}
    const result=await watchQwenJob(id,job=>options.onUpdate?.(qwenJobText(job),""),signal);
    if(result)options.onFinish(qwenJobText(result),response);
    else if(signal.aborted)options.onFinish("_Ответ остановлен._",response);
  }catch(error){options.onError?.(error instanceof Error?error:Error(String(error)))}
  finally{signal.removeEventListener("abort",stop)}
}

export function stopQwenJob(id:string){return request(id,"DELETE")}

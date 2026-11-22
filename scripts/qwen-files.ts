import {useEffect,useState} from "react";
export type QwenAttachment={id:string,name:string,text:string};
export function useQwenFiles(sessionId:string){
 const [files,setFiles]=useState<QwenAttachment[]>([]),[reading,setReading]=useState(false),[error,setError]=useState("");
 useEffect(()=>{setFiles([]);setError("")},[sessionId]);
 async function add(input:FileList|null){if(!input||reading)return;setReading(true);setError("");const added:QwenAttachment[]=[];
  try{if(files.length+input.length>5)throw Error("Можно прикрепить до 5 файлов за сообщение.");
   for(const file of Array.from(input)){
    if(file.size>10*1024*1024)throw Error(file.name+": размер больше 10 МБ.");
    const ext=file.name.split('.').pop()?.toLowerCase();let text="";
    if(ext==="pdf"){
     const pdf=await import("pdfjs-dist");pdf.GlobalWorkerOptions.workerSrc="/kaggle-qwen-ui/chat/pdf.worker.min.mjs";
     const task=pdf.getDocument({data:new Uint8Array(await file.arrayBuffer()),isEvalSupported:false});const doc=await task.promise;
     try{if(doc.numPages>200)throw Error("PDF содержит больше 200 страниц.");for(let n=1;n<=doc.numPages;n++){const page=await doc.getPage(n),content=await page.getTextContent();text+=content.items.map((i:any)=>i.str||"").join(" ")+"\n";if(text.length>160000)throw Error("Слишком много текста в PDF.")}}finally{await doc.destroy()}
    }else if(ext==="docx"){
     const imported=await import("mammoth/mammoth.browser"),m=imported.default||imported;text=(await m.extractRawText({arrayBuffer:await file.arrayBuffer()})).value;
    }else if(file.type.startsWith('text/')||/^(txt|md|mdx|csv|tsv|json|jsonl|yaml|yml|xml|html|css|scss|js|jsx|ts|tsx|py|lua|rs|go|java|c|h|cpp|cs|sql|sh|ps1|bat|log|ini|toml|env|gitignore)$/i.test(ext||'')){
     const data=await file.arrayBuffer();text=new TextDecoder('utf-8').decode(data);if((text.match(/\ufffd/g)||[]).length>Math.max(2,text.length*.01))text=new TextDecoder('windows-1251').decode(data);
     if(text.includes('\u0000'))throw Error("Этот файл не является текстовым.");
    }else throw Error(file.name+": поддерживаются PDF с текстом, DOCX, текст и исходный код. Изображения эта модель не читает.");
    if(!text.trim())throw Error(file.name+": текст не найден. Для сканов нужен OCR.");
    if([...files,...added].reduce((n,f)=>n+f.text.length,0)+text.length>160000)throw Error("Общий объём файлов больше 160 000 символов. Раздели их на несколько сообщений.");
    added.push({id:crypto.randomUUID(),name:file.name,text});
   }setFiles(previous=>[...previous,...added]);
  }catch(e){setError(e instanceof Error?e.message:"Не удалось прочитать файл.")}finally{setReading(false)}
 }
 return {files,reading,error,add,remove:(id:string)=>setFiles(previous=>previous.filter(f=>f.id!==id)),clear:()=>{setFiles([]);setError("")},compose:(input:string)=>files.length?input+"\n\nПрикреплённые файлы (содержимое):\n"+files.map(f=>"\n--- Файл: "+f.name+" ---\n"+f.text+"\n--- Конец файла ---").join("\n"):input};
}

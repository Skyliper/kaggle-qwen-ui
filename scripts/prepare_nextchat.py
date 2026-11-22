from pathlib import Path
import re,shutil,sys,json
r=Path(sys.argv[1]).resolve()
def edit(name,fn):
 p=r/name;p.write_text(fn(p.read_text(encoding='utf-8')),encoding='utf-8')
edit('next.config.mjs',lambda s:s.replace('const disableChunk = !!process.env.DISABLE_CHUNK || mode === "export";', 'const disableChunk = false;').replace('  output: mode,','  basePath: "/kaggle-qwen-ui/chat",\n  trailingSlash: true,\n  output: mode,').replace('    forceSwcTransforms: true,','    forceSwcTransforms: true,\n    cpus: 2,'))
api=(r/'app/api').resolve()
assert api.is_relative_to(r) and api.name=='api'
if api.exists():shutil.rmtree(api)
actions=r/'app/mcp/actions.ts';names=re.findall(r'export async function (\w+)\(',actions.read_text(encoding='utf-8'))
values={'isMcpEnabled':'false','getClientsStatus':'{}','getAllTools':'[]','getAvailableClientsCount':'0','getClientTools':'[]','getMcpConfigFromFile':'{mcpServers:{}}','initializeMcpSystem':'{mcpServers:{}}'}
original=actions.read_text(encoding='utf-8');functions=[]
for match in re.finditer(r'export async function (\w+)\(',original):
 name=match.group(1);body=original.index('{',match.end());signature=original[match.start():body].strip()
 if signature.endswith(')'):
  annotation='any[]' if name in ('getClientTools','getAllTools') else 'number' if name=='getAvailableClientsCount' else 'boolean' if name=='isMcpEnabled' else 'any'
  signature+=': Promise<'+annotation+'>'
 functions.append(signature+' { return '+values.get(name,'undefined')+' as any; }')
actions.write_text('import type {McpClientData,McpConfigData,McpRequestMessage,ServerConfig,ServerStatusResponse} from "./types";\n'+'\n'.join(functions)+'\n',encoding='utf-8')
(r/'app/components/realtime-chat/realtime-chat.tsx').write_text('export function RealtimeChat(_props: {onClose?:()=>void;onStartVoice?:()=>void;onPausedVoice?:()=>void}) { return null; }\n',encoding='utf-8')
eslint=r/'.eslintrc.json'
if eslint.exists():
 data=json.loads(eslint.read_text());data.setdefault('rules',{})['unused-imports/no-unused-imports']='off';eslint.write_text(json.dumps(data,indent=2))
(r/'app/qwen-session.ts').write_text('export function qwenSession(): any { if(typeof window === "undefined")return {}; try{return JSON.parse(sessionStorage.getItem("qwen-chat-config")||"{}")}catch{return {}} }\n')
edit('app/store/access.ts',lambda s:'import { qwenSession } from "../qwen-session";\n'+s.replace('useCustomConfig: false','useCustomConfig: true').replace('openaiUrl: DEFAULT_OPENAI_URL','openaiUrl: qwenSession().baseUrl || DEFAULT_OPENAI_URL').replace('openaiApiKey: ""','openaiApiKey: qwenSession().apiKey || ""'))
edit('app/store/config.ts',lambda s:s.replace('model: "gpt-4o-mini"','model: "qwen3.8-27b-uncensored"').replace('temperature: 0.5','temperature: 1.0').replace('top_p: 1,','top_p: 0.95,').replace('max_tokens: 4000','max_tokens: 32768').replace('historyMessageCount: 4','historyMessageCount: 10000').replace('compressMessageLengthThreshold: 1000','compressMessageLengthThreshold: 130000').replace('enableInjectSystemPrompts: true','enableInjectSystemPrompts: false').replace('customModels: ""','customModels: "-all,+qwen3.8-27b-uncensored@OpenAI"').replace('dontShowMaskSplashScreen: false','dontShowMaskSplashScreen: true').replace('enableAutoGenerateTitle: true','enableAutoGenerateTitle: false'))
edit('app/constant.ts',lambda s:s.replace('REQUEST_TIMEOUT_MS = 60000','REQUEST_TIMEOUT_MS = 900000'))
# Inject key from the current authenticated tab on hydration, never persist it in chat storage.
p=r/'app/utils/indexedDB-storage.ts';s=p.read_text(encoding='utf-8');s='import { qwenSession } from "../qwen-session";\n'+s
s=s.replace('      return value;','''      if(name === "access-control") {
        const data=JSON.parse(value||'{"state":{},"version":2}');const config=qwenSession();
        data.state={...data.state,useCustomConfig:true,provider:"OpenAI",openaiUrl:config.baseUrl||"",openaiApiKey:config.apiKey||""};
        return JSON.stringify(data);
      }
      return value;''')
s=s.replace('      await set(name, value);','''      if(name === "access-control") { _value.state.openaiApiKey=""; value=JSON.stringify(_value); }
      await set(name, value);''');p.write_text(s,encoding='utf-8')
edit('app/client/platforms/openai.ts',lambda s:s.replace('    console.log("[Request] openai payload: ", requestPayload);','''    if(modelConfig.model === "qwen3.8-27b-uncensored") {
      (requestPayload as any).max_tokens = Math.min(modelConfig.max_tokens || 32768,32768);
      (requestPayload as any).reasoning_effort = ["low","medium","high"].includes(sessionStorage.getItem("qwen-effort") || "") ? sessionStorage.getItem("qwen-effort") : "medium";
      (requestPayload as any).top_k = 20;
      (requestPayload as any).min_p = 0;
    }'''))
edit('app/layout.tsx',lambda s:s.replace('title: "NextChat"','title: "Qwen В· NextChat"').replace('<script src="/serviceWorkerRegister.js" defer></script>','').replace('href="/site.webmanifest"','href="/kaggle-qwen-ui/chat/site.webmanifest"'))
(r/'app/qwen-static.d.ts').write_text('declare global { type DangerConfig = Pick<ReturnType<typeof import("./config/server").getServerSideConfig>, "needCode" | "hideUserApiKey" | "disableGPT4" | "hideBalanceQuery" | "disableFastLink" | "customModels" | "defaultModel" | "visionModels">; } export {};\n',encoding='utf-8')
edit('app/store/chat.ts',lambda s:s.replace('const maxTokenThreshold = modelConfig.max_tokens;', 'const maxTokenThreshold = modelConfig.model === "qwen3.8-27b-uncensored" ? 120832 : modelConfig.max_tokens;').replace('if (historyMsgLength > (modelConfig?.max_tokens || 4000))', 'if (historyMsgLength > (modelConfig.model === "qwen3.8-27b-uncensored" ? 120832 : (modelConfig?.max_tokens || 4000)))'))
print('Prepared pinned NextChat static build for Qwen; no API credentials embedded.')

shutil.copyfile(Path(__file__).with_name('qwen-web.ts'),r/'app/qwen-web.ts')
edit('app/client/platforms/openai.ts',lambda s:s.replace('"use client";', '"use client";\nimport { qwenWebTools } from "../../qwen-web";').replace('const [tools, funcs] = usePluginStore','let [tools, funcs] = usePluginStore').replace('// console.log("getAsTools", tools, funcs);', 'if(modelConfig.model === "qwen3.8-27b-uncensored") {\n          const [webTools,webFuncs]=qwenWebTools();\n          tools=[...(tools as any[]),...webTools];funcs={...funcs,...webFuncs};\n        }'))

shutil.copyfile(Path(__file__).with_name('qwen-controls.tsx'),r/'app/components/qwen-controls.tsx')
edit('app/components/chat.tsx',lambda s:'import { QwenControls } from "./qwen-controls";\n'+re.sub(r'<ChatActions\s+uploadImage=\{uploadImage\}.*?setShowChatSidePanel=\{setShowChatSidePanel\}\s*/>', '<QwenControls onFiles={qwenFiles.add} files={qwenFiles.files} removeFile={qwenFiles.remove} fileError={qwenFiles.error} reading={qwenFiles.reading} />',s,flags=re.S).replace('placeholder={Locale.Chat.Input(submitKey)}','placeholder="Напиши сообщение…"'))
edit('app/components/sidebar.tsx',lambda s:s.replace('title="NextChat"','title="Qwen"').replace('subTitle="Build your own AI assistant."','subTitle="Твоё пространство для идей"'))
edit('app/store/config.ts',lambda s:s.replace('theme: Theme.Auto as Theme','theme: Theme.Dark as Theme').replace('tightBorder: !!config?.isApp','tightBorder: true').replace('sendPreviewBubble: true','sendPreviewBubble: false'))

shutil.copyfile(Path(__file__).with_name('qwen-files.ts'),r/'app/qwen-files.ts')
(r/'app/qwen-vendor.d.ts').write_text('declare module "mammoth/mammoth.browser";\n')
edit('app/components/chat.tsx',lambda s:'import { useQwenFiles, qwenDisplayText } from "../qwen-files";\n'+s.replace('  const [attachImages, setAttachImages]', '  const qwenFiles=useQwenFiles(session.id);\n  const [attachImages, setAttachImages]').replace('  const doSubmit = (userInput: string) => {','  const doSubmit = (userInput: string) => {\n    if(qwenFiles.reading)return;\n    userInput=qwenFiles.compose(userInput);').replace('    setAttachImages([]);\n    chatStore.setLastInput(userInput);','    qwenFiles.clear();\n    setAttachImages([]);\n    chatStore.setLastInput(userInput);').replace('<div className={styles["chat-input-panel"]}>','<div className={styles["chat-input-panel"]} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();qwenFiles.add(e.dataTransfer.files)}}>').replace('text={Locale.Chat.Send}\n                  className={styles["chat-input-send"]}', 'text="↑"\n                  aria="Отправить сообщение"\n                  title="Отправить сообщение"\n                  className={styles["chat-input-send"]}'))

edit("app/components/chat.tsx",lambda s:s.replace("    context.push(copiedHello);","    // No synthetic greeting in the Codex-style workspace."))

edit("app/components/chat.tsx",lambda s:s.replace("content={getMessageTextContent(message)}", "content={qwenDisplayText(getMessageTextContent(message),message.role)}"))

edit("app/components/chat.tsx",lambda s:s.replace('icon={<SendWhiteIcon />}\n                  text="↑"', 'icon={<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 19V5m-5 5 5-5 5 5"/></svg>}'))

shutil.copyfile(Path(__file__).with_name('qwen-history.ts'),r/'app/qwen-history.ts')
edit('app/utils/indexedDB-storage.ts',lambda s:'import { historyKey, loadQwenHistory, saveQwenHistory, cloudHistoryLoaded } from "../qwen-history";\n'+s.replace('      if(name === "access-control") {', '      if(name === historyKey)return await loadQwenHistory();\n      if(name === "access-control") {',1).replace('      await set(name, value);','      if(name === historyKey && cloudHistoryLoaded()){saveQwenHistory(value);return;}\n      await set(name, value);'))

shutil.copyfile(Path(__file__).with_name('qwen-jobs.ts'),r/'app/qwen-jobs.ts')
def background_openai(s):
 s=s.replace('"use client";','"use client";\nimport {runQwenJob} from "../../qwen-jobs";',1)
 marker='        streamWithThink('
 assert s.count(marker)==1
 return s.replace(marker, """        if(options.qwenJobId && modelConfig.model === "qwen3.8-27b-uncensored"){
          void runQwenJob(options.qwenJobId,{...requestPayload,tools:(tools as any[]).filter(tool=>["web_search","read_web_page","onion_extended_search"].includes(tool.function?.name))},options,controller.signal);
          return;
        }
"""+marker,1)
edit('app/client/platforms/openai.ts',background_openai)
edit('app/client/api.ts', lambda s:s.replace('export interface ChatOptions {','export interface ChatOptions {\n  qwenJobId?: string;'))
def background_store(s):
 marker='        const messageIndex = session.messages.length + 1;'
 assert s.count(marker)==1
 s=s.replace(marker,marker+'\n        const qwenJobId = modelConfig.model === "qwen3.8-27b-uncensored" ? botMessage.id : undefined;\n        if(qwenJobId)Object.assign(botMessage,{qwenJob:qwenJobId});')
 return s.replace('          messages: sendMessages,','          qwenJobId,\n          messages: sendMessages,',1)
edit('app/store/chat.ts',background_store)
def background_chat(s):
 s='import {watchQwenJob,qwenJobText,stopQwenJob} from "../qwen-jobs";\n'+s
 marker='  const doSubmit = (userInput: string) => {'
 assert s.count(marker)==1
 s=s.replace(marker,"""  useEffect(()=>{
    const controller=new AbortController();
    const target=useChatStore.getState().sessions.find(chat=>chat.id===session.id);
    for(const message of target?.messages||[]){
      const pending=message as typeof message & {qwenJob?:string;qwenResume?:boolean};
      if(!pending.qwenResume||!pending.qwenJob)continue;
      const update=(job:Parameters<typeof qwenJobText>[0])=>{
        if(controller.signal.aborted||!target)return;
        useChatStore.getState().updateTargetSession(target,chat=>{
          const current=chat.messages.find(item=>item.id===message.id);
          if(!current)return;
          current.content=qwenJobText(job);
          current.streaming=job.status==="queued"||job.status==="running";
          if(!current.streaming)Object.assign(current,{qwenResume:false});
          chat.messages=chat.messages.concat();
        });
      };
      void watchQwenJob(pending.qwenJob,update,controller.signal).then(job=>{if(job)update(job)});
    }
    return ()=>controller.abort();
  },[session.id,useChatStore.getState()._hasHydrated]);
"""+marker)
 return s.replace('  const onUserStop = (messageId: string) => {','  const onUserStop = (messageId: string) => {\n    const message=session.messages.find(item=>item.id===messageId) as {qwenResume?:boolean;qwenJob?:string}|undefined;\n    if(message?.qwenResume&&message.qwenJob){void stopQwenJob(message.qwenJob);return;}')
edit('app/components/chat.tsx',background_chat)

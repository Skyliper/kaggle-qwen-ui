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
      (requestPayload as any).reasoning_effort = "medium";
      (requestPayload as any).top_k = 20;
      (requestPayload as any).min_p = 0;
    }'''))
edit('app/layout.tsx',lambda s:s.replace('title: "NextChat"','title: "Qwen В· NextChat"').replace('<script src="/serviceWorkerRegister.js" defer></script>','').replace('href="/site.webmanifest"','href="/kaggle-qwen-ui/chat/site.webmanifest"'))
(r/'app/qwen-static.d.ts').write_text('declare global { type DangerConfig = Pick<ReturnType<typeof import("./config/server").getServerSideConfig>, "needCode" | "hideUserApiKey" | "disableGPT4" | "hideBalanceQuery" | "disableFastLink" | "customModels" | "defaultModel" | "visionModels">; } export {};\n',encoding='utf-8')
edit('app/store/chat.ts',lambda s:s.replace('const maxTokenThreshold = modelConfig.max_tokens;', 'const maxTokenThreshold = modelConfig.model === "qwen3.8-27b-uncensored" ? 120832 : modelConfig.max_tokens;').replace('if (historyMsgLength > (modelConfig?.max_tokens || 4000))', 'if (historyMsgLength > (modelConfig.model === "qwen3.8-27b-uncensored" ? 120832 : (modelConfig?.max_tokens || 4000)))'))
print('Prepared pinned NextChat static build for Qwen; no API credentials embedded.')

shutil.copyfile(Path(__file__).with_name('qwen-web.ts'),r/'app/qwen-web.ts')
edit('app/client/platforms/openai.ts',lambda s:s.replace('"use client";', '"use client";\nimport { qwenWebTools } from "../../qwen-web";').replace('const [tools, funcs] = usePluginStore','let [tools, funcs] = usePluginStore').replace('// console.log("getAsTools", tools, funcs);', 'if(modelConfig.model === "qwen3.8-27b-uncensored") {\n          const [webTools,webFuncs]=qwenWebTools();\n          tools=[...tools,...webTools];funcs={...funcs,...webFuncs};\n        }'))

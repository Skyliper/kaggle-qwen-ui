from pathlib import Path
import re,shutil,sys
r=Path(sys.argv[1]).resolve()
def edit(name,fn):
 p=r/name;p.write_text(fn(p.read_text(encoding='utf-8')),encoding='utf-8')
edit('next.config.mjs',lambda s:s.replace('  output: mode,','  basePath: "/kaggle-qwen-ui/chat",\n  trailingSlash: true,\n  output: mode,').replace('    forceSwcTransforms: true,','    forceSwcTransforms: true,\n    cpus: 2,'))
api=(r/'app/api').resolve()
assert api.is_relative_to(r) and api.name=='api'
if api.exists():shutil.rmtree(api)
actions=r/'app/mcp/actions.ts';names=re.findall(r'export async function (\w+)\(',actions.read_text(encoding='utf-8'))
values={'isMcpEnabled':'false','getClientsStatus':'{}','getAllTools':'[]','getAvailableClientsCount':'0','getClientTools':'[]','getMcpConfigFromFile':'{mcpServers:{}}','initializeMcpSystem':'{mcpServers:{}}'}
actions.write_text('\n'.join('export async function '+name+'(..._args: any[]): Promise<any> { return '+values.get(name,'undefined')+'; }' for name in names)+'\n',encoding='utf-8')
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
      requestPayload["max_tokens"] = Math.min(modelConfig.max_tokens || 32768,32768);
      (requestPayload as any).reasoning_effort = "medium";
      (requestPayload as any).top_k = 20;
      (requestPayload as any).min_p = 0;
    }'''))
edit('app/layout.tsx',lambda s:s.replace('title: "NextChat"','title: "Qwen · NextChat"').replace('<script src="/serviceWorkerRegister.js" defer></script>','').replace('href="/site.webmanifest"','href="/kaggle-qwen-ui/chat/site.webmanifest"'))
print('Prepared pinned NextChat static build for Qwen; no API credentials embedded.')

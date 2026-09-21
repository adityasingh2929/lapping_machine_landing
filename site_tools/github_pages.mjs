// Use the existing Git credential helper; never persist or print credentials.
import {execFileSync} from 'node:child_process';
const credential=execFileSync('git',['credential','fill'],{input:'protocol=https\nhost=github.com\n\n',encoding:'utf8'});
const fields=Object.fromEntries(credential.trim().split('\n').map(line=>{const i=line.indexOf('=');return [line.slice(0,i),line.slice(i+1)];}));
const base='https://api.github.com/repos/adityasingh2929/lapping_machine_landing';
const headers={Authorization:`Bearer ${fields.password}`,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'};
async function call(path,method='GET',body){const r=await fetch(base+path,{method,headers,body:body?JSON.stringify(body):undefined});const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(`${r.status}: ${data.message}`);return data;}
if(process.argv.includes('--enable')){
  let exists=false;
  try{await call('/pages');exists=true;}catch(e){if(!e.message.startsWith('404:'))throw e;}
  const result=await call('/pages',exists?'PUT':'POST',{build_type:'legacy',source:{branch:'master',path:'/docs'}});
  console.log(JSON.stringify({configured:true,url:result.html_url}));
}else{
  const p=await call('/pages');console.log(JSON.stringify({status:p.status,url:p.html_url,source:p.source}));
  const b=await call('/pages/builds/latest');console.log(JSON.stringify({build:b.status,error:b.error?.message}));
}

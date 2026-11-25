let ownerPromise;
export function ensureOwner() {
  if(!ownerPromise)ownerPromise=fetch('/api/v1/session',{method:'POST'}).then(response=>{if(!response.ok)throw new Error('Không kết nối được phiên');}).catch(error=>{ownerPromise=null;throw error;});
  return ownerPromise;
}
export async function postJson(url,payload,options={}) {
  if(/^\/api\/v1\/(chat|quality|visuals)/.test(url))await ensureOwner();
  const response=await fetch(url,{...options,method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(response.status===401)ownerPromise=null;
  return response;
}

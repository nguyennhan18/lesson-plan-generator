import {postJson} from '../../shared/api/client.js';
/** No local fallback geometry: coordinates come from the confirmed canonical scene. */
export async function fetchScene(spec, options={}) {
  const response=await postJson('/api/v1/visuals/scene',spec,options);
  const data=await response.json();
  if(!response.ok)throw new Error(data.detail?.message||'Không dựng được hình');
  return data;
}

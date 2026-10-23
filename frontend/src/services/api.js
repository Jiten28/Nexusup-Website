import {resolveImageURL} from './image-url';
const base=(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/,'');
if(base && !/^https?:\/\//.test(base))throw Error('VITE_API_BASE_URL must be an absolute HTTP(S) backend origin');
if(import.meta.env.PROD && /https?:\/\/(localhost|127\.0\.0\.1)([:/]|$)/.test(base))throw Error('Production API must not point to localhost');
export async function api(path,options={}) {
 const response=await fetch(`${base}${path}`,{credentials:'omit',...options});
 let data;try{data=await response.json()}catch{throw Error('The backend did not return JSON. Check API routing and deployment configuration.')}
 if(!response.ok)throw Error(data.error || data.detail || Object.values(data.errors||{}).flat().join(' ') || 'Service unavailable. Please try again.');
 return data;
}
export async function submit(path,data){const {csrfToken}=await api('/api/csrf/',{credentials:'include'});return api(path,{credentials:'include',method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken},body:JSON.stringify(data)});}
export const backendLink=path=>`${base}${path}`;

export const articleImageURL=value=>resolveImageURL(value,base,window.location.origin);

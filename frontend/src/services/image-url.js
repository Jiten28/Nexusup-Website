// Resolve media against the API origin, never the frontend's directory or SPA route.
export function resolveImageURL(value, backendOrigin='', pageOrigin='http://localhost') {
 if(typeof value!=='string'||!value.trim())return '';
 try {
  const origin=new URL(backendOrigin||pageOrigin);
  const url=new URL(value,origin.origin+'/');
  if(!['https:','http:'].includes(url.protocol)||url.username||url.password)return '';
  // HTTPS pages must not embed mixed-content HTTP images.
  if(new URL(pageOrigin).protocol==='https:'&&url.protocol!=='https:')return '';
  return url.href;
 }catch{return '';}
}

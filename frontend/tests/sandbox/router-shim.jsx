// SANDBOX-ONLY stand-in for react-router-dom, used when the real package cannot be installed
// (no registry access). It is NOT shipped in the app; `npm run build` uses the real router.
import React, {createContext, useContext, useEffect, useState} from 'react';
const Loc = createContext({pathname: '/', search: ''}), Params = createContext({}), listeners = new Set();
const here = () => ({pathname: location.pathname, search: location.search});
const go = to => { history.pushState({}, '', to); listeners.forEach(f => f()); };
export function BrowserRouter({children}) {
  const [loc, setLoc] = useState(here);
  useEffect(() => { const f = () => setLoc(here()); listeners.add(f); addEventListener('popstate', f); return () => { listeners.delete(f); removeEventListener('popstate', f); }; }, []);
  return <Loc.Provider value={loc}>{children}</Loc.Provider>;
}
export const useLocation = () => useContext(Loc);
export const useNavigate = () => go;
export const useParams = () => useContext(Params);
export function Link({to, children, onClick, target, ...rest}) {
  return <a href={to} target={target} {...rest} onClick={e => { onClick && onClick(e); if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || target === '_blank') return; e.preventDefault(); go(to); }}>{children}</a>;
}
export function Route() { return null; }
const match = (pattern, path) => {
  if (pattern === '*') return {};
  const names = [], re = new RegExp('^' + pattern.replace(/\/$/, '').replace(/:([A-Za-z_]+)/g, (_, n) => { names.push(n); return '([^/]+)'; }) + '/?$'), m = path.match(re);
  return m ? Object.fromEntries(names.map((n, i) => [n, decodeURIComponent(m[i + 1])])) : null;
};
export function Routes({children}) {
  const {pathname} = useContext(Loc);
  for (const el of React.Children.toArray(children)) { const p = match(el.props.path, pathname); if (p) return <Params.Provider value={p}>{el.props.element}</Params.Provider>; }
  return null;
}

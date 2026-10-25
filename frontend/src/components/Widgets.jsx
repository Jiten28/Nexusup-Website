import React,{useContext,useEffect} from 'react';
import {Translation} from '../context/Translation';
import {mountWidgets} from './legacyWidgets';
import {api} from '../services/api';
import {previewEnabled} from '../preview/data';
export default function Widgets(){const t=useContext(Translation);useEffect(()=>mountWidgets(api,{weatherDisabled:previewEnabled}),[]);return <>
 <details className="header-popover"><summary>{t('ui:widgets','Widgets +')}</summary><div className="popover">{[['calculator','Calculator'],['currency','Currency'],['weather','Weather'],['clock','World clock'],['calendar','Calendar'],['units','Unit converter']].map(([key,label])=><button key={key} data-widget={key}>{label}</button>)}</div></details>
 <dialog id="utility-dialog" aria-labelledby="utility-title"><div className="dialog-head"><h2 id="utility-title">Widgets</h2><button id="close-utility" aria-label="Close widget">×</button></div><div id="utility-content"/><p id="widget-status" role="status"/></dialog>
 </>}

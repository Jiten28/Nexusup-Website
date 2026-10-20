import {createContext} from 'react';
// Marked public text only. Original strings remain the fallback for partial coverage.
export const Translation=createContext((key,fallback)=>fallback||key);

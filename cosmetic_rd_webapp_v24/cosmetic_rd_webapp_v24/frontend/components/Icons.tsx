import type { CSSProperties } from 'react';
const paths: Record<string, React.ReactNode> = {
  grid:<><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
  flask:<><path d="M9 3h6M10 3v7l-5.4 8.3A2 2 0 0 0 6.3 21h11.4a2 2 0 0 0 1.7-2.7L14 10V3"/><path d="M8 15h8"/></>,
  layers:<><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 9v11"/></>,
  book:<><path d="M4 19.5a2.5 2.5 0 0 1 2.5-2.5H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5a2.5 2.5 0 0 0 2.5 2.5H20"/><path d="M9 8h6M9 12h5"/></>,
  globe:<><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c-5 5-5 13 0 18M12 3c5 5 5 13 0 18"/></>,
  beaker:<><path d="M4 3h16M7 3v6l-3 9a2 2 0 0 0 2 3h12a2 2 0 0 0 2-3l-3-9V3M5.5 15h13"/></>,
  chevron:<path d="m9 18 6-6-6-6"/>,
  down:<path d="m6 9 6 6 6-6"/>,
  add:<path d="M12 5v14M5 12h14"/>,
  check:<path d="m5 12 4 4L19 6"/>,
  alert:<><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 17h.01"/></>,
  search:<><circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/></>,
  refresh:<><path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M5.6 9a8 8 0 0 1 13.8-2L20 12M4 12l.6 5a8 8 0 0 0 13.8-2"/></>,
  arrow:<path d="M4 12h16m-7-7 7 7-7 7"/>,
  download:<><path d="M12 3v12m-4-4 4 4 4-4M4 17v4h16v-4"/></>,
  save:<><path d="M4 3h14l3 3v15H3V3zM7 3v6h10V3M7 21v-9h10v9"/></>,
  shield:<><path d="M12 2 4 6v6c0 5 3.5 8 8 10 4.5-2 8-5 8-10V6z"/><path d="m9 12 2 2 4-4"/></>,
  clock:<><circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/></>,
  trash:<><path d="M3 6h18M8 6V4h8v2M6 6l1 15h10l1-15M10 10v7M14 10v7"/></>,
  filter:<><path d="M3 4h18l-7 8v7l-4 2v-9z"/></>,
  menu:<path d="M4 7h16M4 12h16M4 17h16"/>,
  close:<path d="M5 5 19 19M19 5 5 19"/>,
  logout:<><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/></>,
  external:<><path d="M14 4h6v6M20 4l-9 9"/><path d="M20 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h5"/></>,
  spark:<><path d="m12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5z"/></>,
  copy:<><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h3"/></>,
};
export function Icon({name,size=18,style,className}:{name:string;size?:number;style?:CSSProperties;className?:string}){
 return <svg className={className} style={style} aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]||paths.flask}</svg>;
}

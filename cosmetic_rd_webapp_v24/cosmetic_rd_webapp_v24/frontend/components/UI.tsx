import {Icon} from './Icons';
export function Pill({children,tone='neutral'}:{children:React.ReactNode;tone?:'neutral'|'success'|'warning'|'danger'|'blue'}){return <span className={`pill ${tone}`}>{children}</span>}
export function Empty({title,description,action}:{title:string;description:string;action?:React.ReactNode}){return <div className="empty-state"><div className="empty-symbol"><Icon name="flask" size={26}/></div><strong>{title}</strong><p>{description}</p>{action}</div>}
export function Panel({children,className=''}:{children:React.ReactNode;className?:string}){return <section className={`panel ${className}`}>{children}</section>}
export function PanelHeader({label,title,aside}:{label?:string;title:string;aside?:React.ReactNode}){return <div className="panel-header"><div>{label&&<div className="overline">{label}</div>}<h2>{title}</h2></div>{aside}</div>}
export function Field({label,sub,children}:{label:string;sub?:string;children:React.ReactNode}){return <label className="field"><span className="field-label">{label}</span>{children}{sub&&<span className="field-hint">{sub}</span>}</label>}
export function Notice({children,tone='info'}:{children:React.ReactNode;tone?:'info'|'warn'|'danger'|'success'}){return <div className={`notice ${tone}`}><Icon name={tone==='success'?'check':'alert'} size={18}/><div>{children}</div></div>}

// Execute TypeScript pure helpers through globally available TypeScript compiler,
// without depending on React / Next.js and without a browser. Not a Next build.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const cp = require('node:child_process');
function loadTypeScript(){
  try { return require('typescript'); }
  catch { return require(path.join(cp.execFileSync('npm', ['root','-g'], {encoding:'utf8'}).trim(),'typescript')); }
}
const ts = loadTypeScript();
const code = fs.readFileSync(require('node:path').join(__dirname,'../lib/form-model.ts'),'utf8');
const out = ts.transpileModule(code,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const mod={exports:{}}; vm.runInNewContext(out,{exports:mod.exports,module:mod,require,structuredClone,console});
const {formulaErrors,formulaTotal,balanceFormula,protocolErrors} = mod.exports;
const make=(a,b,c)=>({items:[
  {item_id:'oil',inci:'Simmondsia Chinensis Seed Oil',group_code:'lip',percent_bounds:{min:1,max:90},prior_percent:a},
  {item_id:'wax',inci:'Cera Alba',group_code:'cons',percent_bounds:{min:5,max:22},prior_percent:b},
  {item_id:'base',inci:'Unknown Premix',group_code:'b_lip',percent_bounds:{min:0,max:70},prior_percent:c,composition:{complete:false}}
]});
assert.deepEqual(Array.from(formulaErrors(make(35,18,43))),[]);
assert.equal(formulaTotal(make(35,18,43)),96);
let balanced=balanceFormula(make(35,18,43),'base');
assert.equal(formulaTotal(balanced),100);
assert.equal(balanced.items[2].prior_percent,47);
assert.equal(make(35,18,43).items[2].prior_percent,43,'must not mutate original');
assert.throws(()=>balanceFormula(make(90,20,40),'base'),/Không thể cân bằng/);
assert.ok(formulaErrors(make(105,18,0)).length);
assert.ok(formulaErrors({...make(35,18,43),items:[...make(35,18,43).items,{...make(35,18,43).items[0]}]}).some(x=>x.includes('trùng')));
const good={metrics:[{code:'PH',name:'pH',kind:'numeric',unit:'pH',timepoints_days:[0,7],target_min:4,target_max:6}]};
assert.equal(protocolErrors(good).length,0);
assert.ok(protocolErrors({metrics:[{...good.metrics[0],target_min:7,target_max:5}]}).length);
assert.ok(protocolErrors({metrics:[{...good.metrics[0],timepoints_days:[0,0]}]}).length);
assert.ok(protocolErrors({metrics:[{...good.metrics[0],kind:'categorical',acceptable_values:[]}]}).length);
console.log('PASS: 11 frontend model assertions');

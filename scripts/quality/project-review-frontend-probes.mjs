#!/usr/bin/env node
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {normalizeDeck,mutateDeck} from '../../app/frontend/src/shared/storage/projectStore.js';
const args=Object.fromEntries(process.argv.slice(2).reduce((out,item,index,list)=>index%2===0?[...out,[item.replace(/^--/,''),list[index+1]]]:out,[]));
if(!args.input||!args.output||!['baseline','acceptance'].includes(args.mode))throw new Error('Expected --mode --input --output');
if(fs.existsSync(args.output))throw new Error('Evidence already exists; choose a new output path');
const report=JSON.parse(fs.readFileSync(args.input,'utf8'));
const deck=normalizeDeck({presentation_title:'Probe',slides:[{title:'A'},{title:'B'}]});
const changed=mutateDeck(deck,{...deck,slides:[deck.slides[1],deck.slides[0]]});
const html=fs.readFileSync(fileURLToPath(new URL('../../app/frontend/index.html',import.meta.url)),'utf8');
const plotter=fs.readFileSync(fileURLToPath(new URL('../../app/frontend/src/shared/math/FunctionPlotter.jsx',import.meta.url)),'utf8');
const checks={reorder_keeps_ids:changed.slides[0].slide_id===deck.slides[1].slide_id&&changed.revision===1,local_math_assets:!html.includes('cdn.jsdelivr.net'),plotter_has_no_evaluator:!plotter.includes('new Function')&&!plotter.includes('eval(')};
const result={...report,frontend_checks:checks,pass:report.pass&&Object.values(checks).every(Boolean),browser_evidence:'Run npm run test:e2e separately; these probes do not claim browser acceptance.'};
fs.writeFileSync(args.output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({output:args.output,pass:result.pass}));
if(args.mode==='acceptance'&&!result.pass)process.exitCode=1;

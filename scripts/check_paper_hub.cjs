const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..');
const page=fs.readFileSync(path.join(root,'reports/paper_v4.html'),'utf8');
const script=[...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
function element(){return {value:'',children:[],handlers:{},textContent:'',appendChild(x){this.children.push(x)},replaceChildren(){this.children=[]},addEventListener(k,f){this.handlers[k]=f}}}
const elements=Object.fromEntries(['error-model','error-kind','error-rows','error-count'].map(k=>[k,element()]));elements['error-model'].value='cnn64';elements['error-kind'].value='all';
const document={getElementById:k=>elements[k],createElement:()=>element()};vm.runInNewContext(script,{document});
const data=JSON.parse(fs.readFileSync(path.join(root,'experiments/paper_v4/review_candidates.json'),'utf8'));
for(const model of ['cnn64','ssl_transformer48'])for(const kind of ['all','0','1']){elements['error-model'].value=model;elements['error-kind'].value=kind;elements['error-kind'].handlers.change();const expected=data.filter(r=>r.predictions[model].wrong_seeds>=2&&(kind==='all'||String(r.label)===kind));assert.equal(elements['error-rows'].children.length,expected.length);assert.equal(elements['error-count'].textContent,expected.length+' inceleme adayı');for(let i=0;i<expected.length;i++)assert.equal(elements['error-rows'].children[i].children[0].textContent,expected[i].id);}
console.log('PASS: six model/error filter combinations checked with DOM test doubles; no browser rendered');

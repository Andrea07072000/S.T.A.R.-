import{t as e}from"./main-Dx8lu5GH.js";var t=null,n=new Set;function r(){return document.documentElement.dataset.base||`/`}async function i(n){if(!t){n(`loading Python (about 12 MB, once)…`);let i=r()+`pyodide/pyodide.mjs`;t=e(()=>import(i).then(e=>e.loadPyodide({indexURL:r()+`pyodide/`})),[])}return t}async function a(e,t,i){for(let a of t){if(n.has(a))continue;i(`installing ${a}…`);let t=await fetch(r()+`downloads/wheels/`+a);if(!t.ok)throw Error(`cannot download ${a} (HTTP ${t.status})`);e.globals.set(`_wheel_bytes`,new Uint8Array(await t.arrayBuffer())),await e.runPythonAsync(`import io, site, zipfile
zipfile.ZipFile(io.BytesIO(bytes(_wheel_bytes.to_py()))).extractall(site.getsitepackages()[0])
del _wheel_bytes
`),n.add(a)}}function o(e){let t=e.querySelector(`textarea`),n=e.querySelector(`button.run`),r=e.querySelector(`button.reset`),o=e.querySelector(`output`),s=t.value,c=JSON.parse(e.dataset.wheels||`[]`),l=e=>{o.textContent=e};r?.addEventListener(`click`,()=>{t.value=s,o.textContent=``,t.focus()}),t.addEventListener(`keydown`,e=>{(e.ctrlKey||e.metaKey)&&e.key===`Enter`&&(e.preventDefault(),n.click())}),n.addEventListener(`click`,async()=>{n.disabled=!0;let r=[];try{let n=await i(l);await a(n,c,l),l(`running…`),n.setStdout({batched:e=>r.push(e)}),n.setStderr({batched:e=>r.push(e)}),await n.runPythonAsync(t.value),o.textContent=r.join(`
`)||e.dataset.empty||`(no output: add print(...) to see a result)`,o.className=`ok`}catch(e){let t=String(e.message||e).trim().split(`
`).slice(-6).join(`
`);o.textContent=(r.length?r.join(`
`)+`

`:``)+t,o.className=`err`}finally{n.disabled=!1}})}export{o as initRunner};
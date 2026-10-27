import{At as e,W as t,gt as n,nt as r}from"./three.module-C_IHS0MM.js";import{n as i,o as a,p as o,r as s,u as c}from"./kit-C3ryh3st.js";var l=e=>[(e+Math.sqrt(e*e+4))/2,(e-Math.sqrt(e*e+4))/2];function u(e){let t=(e*e+2)/(e*Math.sqrt(e*e+4));return{plus:t/2+.5,minus:t/2-.5,total:t}}var d=`varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,f=`precision highp float;
varying vec2 vUv; uniform vec2 uRes; uniform vec2 uLens; uniform vec2 uSrc; uniform float uE; uniform float uOn; uniform float uT;
float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float noise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float s = 0.0, a = 0.5; for (int i = 0; i < 5; i++){ s += a * noise(p); p *= 2.03; a *= 0.5; } return s; }
vec3 stars(vec2 p){
  vec3 c = vec3(0.0);
  for (int k = 0; k < 3; k++){
    float sc = 60.0 + 70.0 * float(k); vec2 q = p * sc, i = floor(q), f = fract(q) - 0.5;
    float r = h21(i + float(k) * 17.0);
    if (r > 0.86){ vec2 o = vec2(h21(i + 3.1), h21(i + 7.7)) - 0.5; float d = length(f - o * 0.6); float b = (r - 0.86) * 7.0;
      vec3 col = mix(vec3(0.75, 0.85, 1.0), vec3(1.0, 0.85, 0.65), h21(i + 9.0)); c += col * b * exp(-d * d * 260.0); }
  }
  return c;
}
vec3 galaxy(vec2 p){
  // a face-on spiral: bright bulge, two logarithmic arms, dust
  float r = length(p), a = atan(p.y, p.x);
  float arms = 0.5 + 0.5 * cos(2.0 * (a - 3.2 * log(r + 0.02)) );
  float disk = exp(-r / 0.06) * (0.35 + 0.9 * pow(arms, 3.0)) * (0.7 + 0.6 * fbm(p * 40.0));
  float bulge = exp(-r * r / 0.0009);
  return vec3(0.95, 0.82, 0.62) * bulge * 1.6 + mix(vec3(0.55, 0.65, 1.0), vec3(1.0, 0.75, 0.6), exp(-r / 0.04)) * disk;
}
vec3 sky(vec2 p){
  vec3 neb = vec3(0.10, 0.05, 0.16) * fbm(p * 3.0 + 4.0) + vec3(0.02, 0.06, 0.12) * fbm(p * 5.0 - 2.0);
  return neb * 0.9 + stars(p) + galaxy(p - uSrc);
}
void main(){
  vec2 asp = vec2(uRes.x / uRes.y, 1.0);
  vec2 p = (vUv - 0.5) * asp, d = p - uLens;
  vec2 q = p;
  float r2 = dot(d, d);
  if (uOn > 0.5) q = p - uE * uE * d / max(r2, 1e-7);          // the lens equation
  vec3 col = sky(q);
  float r = sqrt(r2);
  // the dark core marks the lens (a black hole's own shadow would be far smaller at this scale)
  col *= smoothstep(0.10 * uE, 0.16 * uE, r) * uOn + (1.0 - uOn);
  // a faint guide circle at the Einstein radius
  col += vec3(0.25, 0.5, 1.0) * 0.18 * exp(-pow((r - uE) / 0.0025, 2.0)) * uOn;
  gl_FragColor = vec4(col, 1.0);
}`;function p(p){let m=JSON.parse(p.dataset.t||`{}`).ui;p.innerHTML=`<div class="mx-stage"><div class="mx-view ln-view"></div><div class="mx-hud"><span></span><dl class="mx-read"></dl></div></div>
    <div class="mx-ctl"><div class="mx-row"><label for="ln-m">${i(m.mass)}</label><input type="range" id="ln-m" min="0.03" max="0.22" step="0.005" value="0.11"></div>
      <div class="btn-row"><button type="button" class="btn small ln-on" aria-pressed="true">${i(m.on)}</button><button type="button" class="btn small primary ln-ring">${i(m.ring)}</button><button type="button" class="btn small ln-fly">${i(m.fly)}</button></div></div>
    <p class="mx-hint small">${i(m.hint)}</p>`;let h=p.querySelector(`.mx-view`),g=c(p);if(!o()){h.innerHTML=`<p class="note">${i(m.nogl)}</p>`,p.dataset.ready=`1`;return}let _=a(h,{bloom:.55,background:0,shadows:!1});_.controls.enabled=!1;let v={uRes:{value:new e(1,1)},uLens:{value:new e(-.35,.12)},uSrc:{value:new e(.18,-.04)},uE:{value:.11},uOn:{value:1},uT:{value:0}},y=new t(new r(2,2),new n({vertexShader:d,fragmentShader:f,uniforms:v,depthTest:!1,depthWrite:!1}));y.frustumCulled=!1,_.scene.add(y);let b=_.renderer.domElement,x=t=>{let n=b.getBoundingClientRect();return new e(((t.clientX-n.left)/n.width-.5)*(n.width/n.height),.5-(t.clientY-n.top)/n.height)},S=null,C=0,w=!1;b.style.cursor=`grab`,b.style.touchAction=`none`,b.addEventListener(`pointerdown`,e=>{let t=x(e);S=t.distanceTo(v.uLens.value)<Math.max(.06,v.uE.value*.6)||!e.shiftKey?`lens`:`src`,e.shiftKey&&(S=`src`),C=0,b.setPointerCapture(e.pointerId),b.style.cursor=`grabbing`,(S===`lens`?v.uLens:v.uSrc).value.copy(t),_.kick()}),b.addEventListener(`pointermove`,e=>{S&&((S===`lens`?v.uLens:v.uSrc).value.copy(x(e)),_.kick())});let T=()=>{S=null,b.style.cursor=`grab`};b.addEventListener(`pointerup`,T),b.addEventListener(`pointercancel`,T);let E=p.querySelector(`#ln-m`);E.addEventListener(`input`,()=>{v.uE.value=Number(E.value),_.kick()});let D=p.querySelector(`.ln-on`);D.addEventListener(`click`,()=>{let e=v.uOn.value>.5?0:1;v.uOn.value=e,D.setAttribute(`aria-pressed`,String(!!e)),g(e?m.on_said:m.off_said),_.kick()}),p.querySelector(`.ln-ring`).addEventListener(`click`,()=>{C=0,v.uLens.value.copy(v.uSrc.value).add(new e(.002,.001)),_.kick()}),p.querySelector(`.ln-fly`).addEventListener(`click`,()=>{C=+!C,g(C?m.flying:m.lead),_.kick()});let O=0;_.onFrame((e,t)=>{v.uRes.value.set(h.clientWidth,h.clientHeight),v.uT.value=t/1e3,C&&(O+=e*.12,v.uLens.value.set(v.uSrc.value.x-.5+O%1*1,v.uSrc.value.y+.03*Math.sin(O*2)));let n=v.uLens.value.distanceTo(v.uSrc.value)/v.uE.value,r=u(Math.max(n,1e-4)),[a,o]=l(n);p.querySelector(`.mx-read`).innerHTML=[[m.r_u,s(n,2)],[m.r_mu,n<.01?`> 100`:`×${s(r.total,2)}`],[m.r_img,`${s(a,2)} · ${s(Math.abs(o),2)} θE`]].map(([e,t])=>`<div><dt>${i(e)}</dt><dd>${i(t)}</dd></div>`).join(``),p.dataset.u=n.toFixed(3),n<.06&&v.uOn.value>.5&&!w&&(w=!0,g(m.ring_said,`ok`),p.dataset.ring=`1`),n>.3&&(w=!1)}),g(m.lead),p.dataset.ready=`1`}export{p as init};
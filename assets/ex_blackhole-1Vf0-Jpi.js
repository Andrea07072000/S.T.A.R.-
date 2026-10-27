import{G as e,Mt as t,U as n,_t as r,jt as i,rt as a}from"./three.module-NYXnoNEW.js";import{l as o,n as s,o as c,p as l,r as u,u as d}from"./kit-ChNSd1D6.js";var f=3*Math.sqrt(3)/2,p=`varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,m=`precision highp float;
varying vec2 vUv; uniform vec2 uRes; uniform vec3 uPos; uniform mat3 uRot; uniform float uDisk; uniform float uDop; uniform float uT; uniform float uFov;
float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
vec3 sky(vec3 d){
  vec2 uv = vec2(atan(d.z, d.x), asin(clamp(d.y, -1.0, 1.0)));
  vec3 c = vec3(0.0);
  for (int k = 0; k < 2; k++){ float sc = 90.0 + 140.0 * float(k); vec2 q = uv * sc, i = floor(q), f = fract(q) - 0.5; float r = h21(i + float(k) * 7.0);
    if (r > 0.93){ float dd = length(f); c += mix(vec3(0.7,0.8,1.0), vec3(1.0,0.8,0.6), h21(i + 3.0)) * (r - 0.93) * 18.0 * exp(-dd * dd * 70.0); } }
  float band = exp(-pow(d.y * 3.0 + 0.3 * sin(uv.x * 2.0), 2.0)); c += vec3(0.18, 0.15, 0.22) * band * (0.6 + 0.4 * h21(floor(uv * 40.0)));
  return c;
}
vec3 bb(float T){ T = clamp(T, 1000.0, 40000.0) / 100.0; float r = T <= 66.0 ? 1.0 : clamp(1.29 * pow(T - 60.0, -0.133), 0.0, 1.0);
  float g = T <= 66.0 ? clamp(0.39 * log(T) - 0.63, 0.0, 1.0) : clamp(1.13 * pow(T - 60.0, -0.0755), 0.0, 1.0); float b = T >= 66.0 ? 1.0 : (T <= 19.0 ? 0.0 : clamp(0.543 * log(T - 10.0) - 1.196, 0.0, 1.0)); return vec3(r, g, b); }
void main(){
  vec2 p = (vUv - 0.5) * vec2(uRes.x / uRes.y, 1.0) * uFov;
  vec3 dir = normalize(uRot * vec3(p, -1.0));
  vec3 x = uPos, v = dir;
  float h2 = dot(cross(x, v), cross(x, v));
  vec3 col = vec3(0.0); float alpha = 0.0; bool captured = false;
  for (int i = 0; i < 420; i++){
    float r = length(x);
    if (r < 1.0){ captured = true; break; }
    if (r > 60.0 && dot(x, v) > 0.0) break;
    float hstep = 0.02 * max(1.0, r * 0.35);
    vec3 a0 = -1.5 * h2 * x / pow(r, 5.0);
    vec3 xn = x + v * hstep + 0.5 * a0 * hstep * hstep;
    vec3 a1 = -1.5 * h2 * xn / pow(length(xn), 5.0);
    vec3 vn = v + 0.5 * (a0 + a1) * hstep;
    // crossing the disc plane (y = 0) between 3 r_s (the innermost stable orbit) and 14 r_s
    if (uDisk > 0.5 && x.y * xn.y < 0.0){
      float t = x.y / (x.y - xn.y); vec3 c = mix(x, xn, t); float rc = length(c);
      if (rc > 3.0 && rc < 14.0){
        float Tk = 9000.0 * pow(3.0 / rc, 0.75) * pow(1.0 - sqrt(3.0 / rc), 0.25) * 1.9;
        vec3 vel = normalize(vec3(-c.z, 0.0, c.x)) * sqrt(0.5 / (rc - 1.0));
        float beta = length(vel), gam = 1.0 / sqrt(1.0 - beta * beta);
        float dop = uDop > 0.5 ? 1.0 / (gam * (1.0 - dot(vel, -normalize(v)))) : 1.0;
        float grav = sqrt(1.0 - 1.5 / rc);
        float g = dop * grav;
        float ring = 0.75 + 0.25 * sin(rc * 6.0 - uT * 2.0 / sqrt(rc * rc * rc) * 8.0 + atan(c.z, c.x) * 3.0);
        vec3 e = bb(Tk * g) * pow(g, 3.0) * ring * smoothstep(3.0, 3.6, rc) * (1.0 - smoothstep(11.0, 14.0, rc)) * 1.4;
        col += (1.0 - alpha) * e; alpha += (1.0 - alpha) * 0.88;
        if (alpha > 0.98) break;
      }
    }
    x = xn; v = vn;
  }
  if (!captured) col += (1.0 - alpha) * sky(normalize(v));
  gl_FragColor = vec4(col, 1.0);
}`;function h(h){let g=JSON.parse(h.dataset.t||`{}`).ui;h.innerHTML=`<div class="mx-stage bh-stage"><div class="mx-view"></div><div class="mx-hud"><span class="bh-state mono"></span><dl class="mx-read"></dl></div></div>
    <div class="mx-ctl"><div class="mx-row"><label for="bh-d">${s(g.dist)}</label><input type="range" id="bh-d" min="4" max="60" step="0.5" value="26"><output class="mono"></output></div>
      <div class="mx-row"><label for="bh-i">${s(g.tilt)}</label><input type="range" id="bh-i" min="-80" max="80" step="1" value="10"><output class="mono"></output></div>
      <div class="btn-row"><button type="button" class="btn small bh-disk" aria-pressed="true">${s(g.disk)}</button><button type="button" class="btn small bh-dop" aria-pressed="true">${s(g.dop)}</button><button type="button" class="btn small primary bh-dive">${s(g.dive)}</button></div></div>
    <p class="mx-hint small">${s(g.hint)}</p>`;let _=h.querySelector(`.mx-view`),v=d(h),y=h.querySelector(`#bh-d`),b=h.querySelector(`#bh-i`),x=.4,S=!1;if(!l()){_.innerHTML=`<p class="note">${s(g.nogl)}</p>`,h.dataset.ready=`1`;return}let C=c(_,{bloom:.75,background:0,shadows:!1});C.controls.enabled=!1,C.controls.update=()=>!1,C.renderer.setPixelRatio(Math.min(1,window.devicePixelRatio||1)*.8),window.dispatchEvent(new Event(`resize`));let w={uRes:{value:new i(1,1)},uPos:{value:new t},uRot:{value:new n},uDisk:{value:1},uDop:{value:1},uT:{value:0},uFov:{value:.9}},T=new e(new a(2,2),new r({vertexShader:p,fragmentShader:m,uniforms:w,depthTest:!1,depthWrite:!1}));T.frustumCulled=!1,C.scene.add(T);let E=C.renderer.domElement,D=null;E.style.cursor=`grab`,E.style.touchAction=`none`,E.addEventListener(`pointerdown`,e=>{D={x:e.clientX,y:e.clientY},E.setPointerCapture(e.pointerId),E.style.cursor=`grabbing`}),E.addEventListener(`pointermove`,e=>{D&&(x-=(e.clientX-D.x)*.005,b.value=String(Math.max(-80,Math.min(80,Number(b.value)+(e.clientY-D.y)*.25))),D={x:e.clientX,y:e.clientY},C.kick())}),E.addEventListener(`pointerup`,()=>{D=null,E.style.cursor=`grab`}),E.addEventListener(`wheel`,e=>{e.preventDefault(),y.value=String(Math.max(4,Math.min(60,Number(y.value)*(1+e.deltaY*.001))))},{passive:!1});let O=(e,t)=>{let n=h.querySelector(e);n.addEventListener(`click`,()=>{let e=w[t].value>.5?0:1;w[t].value=e,n.setAttribute(`aria-pressed`,String(!!e)),v(g[`${t}_${e}`])})};O(`.bh-disk`,`uDisk`),O(`.bh-dop`,`uDop`),h.querySelector(`.bh-dive`).addEventListener(`click`,()=>{S=!S,v(S?g.diving:g.lead)}),C.onFrame((e,n)=>{if(w.uT.value=n/1e3,w.uRes.value.set(_.clientWidth,_.clientHeight),S){let t=Math.max(4,Number(y.value)-e*(o()?.6:2));y.value=String(t),t<=4&&(S=!1)}x+=e*.02;let r=Number(y.value),i=Number(b.value)*Math.PI/180,a=new t(r*Math.cos(i)*Math.sin(x),r*Math.sin(i),r*Math.cos(i)*Math.cos(x)),c=a.clone().multiplyScalar(-1).normalize(),l=new t().crossVectors(c,new t(0,1,0)).normalize(),d=new t().crossVectors(l,c);w.uPos.value.copy(a),w.uRot.value.set(l.x,d.x,-c.x,l.y,d.y,-c.y,l.z,d.z,-c.z),h.querySelector(`#bh-d + output`).textContent=`${u(r,1)} rₛ`,h.querySelector(`#bh-i + output`).textContent=`${b.value}°`;let p=1.3348e-9*1989e27/2998e5**2*r,m=Math.sqrt(1-1/r),v=5309834399999999e6/p**3/9.81;h.querySelector(`.mx-read`).innerHTML=[[g.r_dist,`${u(p/1e3,0)} km`],[g.r_clock,`${u(m*100,1)} %`],[g.r_tidal,v>1e3?`${v.toExponential(1)} g`:`${u(v,1)} g`],[g.r_shadow,`${u(f,2)} rₛ`]].map(([e,t])=>`<div><dt>${s(e)}</dt><dd>${s(t)}</dd></div>`).join(``),h.querySelector(`.bh-state`).textContent=r<3?g.inside_isco:r<6?g.close:``,h.dataset.d=r.toFixed(1)}),v(g.lead),h.dataset.ready=`1`}export{h as init};
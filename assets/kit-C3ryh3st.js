import{At as e,D as t,Et as n,G as r,J as i,K as a,M as o,Nt as s,O as c,Q as l,U as u,W as d,X as f,Y as p,b as m,ct as h,dt as g,et as ee,gt as _,h as v,ht as y,i as b,jt as x,kt as S,l as C,lt as w,m as T,pt as E,q as D,rt as O,s as k,t as te,w as A}from"./three.module-C_IHS0MM.js";import{n as j,r as M,t as N}from"./CSS2DRenderer-DJUXQWb_.js";var P={name:`CopyShader`,uniforms:{tDiffuse:{value:null},opacity:{value:1}},vertexShader:`

		varying vec2 vUv;

		void main() {

			vUv = uv;
			gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

		}`,fragmentShader:`

		uniform float opacity;

		uniform sampler2D tDiffuse;

		varying vec2 vUv;

		void main() {

			vec4 texel = texture2D( tDiffuse, vUv );
			gl_FragColor = opacity * texel;


		}`},F=class{constructor(){this.isPass=!0,this.enabled=!0,this.needsSwap=!0,this.clear=!1,this.renderToScreen=!1}setSize(){}render(){console.error(`THREE.Pass: .render() must be implemented in derived pass.`)}dispose(){}},I=new l(-1,1,1,-1,0,1),L=new class extends C{constructor(){super(),this.setAttribute(`position`,new A([-1,3,0,-1,-1,0,3,-1,0],3)),this.setAttribute(`uv`,new A([0,2,0,0,2,0],2))}},R=class{constructor(e){this._mesh=new d(L,e)}dispose(){this._mesh.geometry.dispose()}render(e){e.render(this._mesh,I)}get material(){return this._mesh.material}set material(e){this._mesh.material=e}},ne=class extends F{constructor(e,t=`tDiffuse`){super(),this.textureID=t,this.uniforms=null,this.material=null,e instanceof _?(this.uniforms=e.uniforms,this.material=e):e&&(this.uniforms=S.clone(e.uniforms),this.material=new _({name:e.name===void 0?`unspecified`:e.name,defines:Object.assign({},e.defines),uniforms:this.uniforms,vertexShader:e.vertexShader,fragmentShader:e.fragmentShader})),this._fsQuad=new R(this.material)}render(e,t,n){this.uniforms[this.textureID]&&(this.uniforms[this.textureID].value=n.texture),this._fsQuad.material=this.material,this.renderToScreen?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(t),this.clear&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),this._fsQuad.render(e))}dispose(){this.material.dispose(),this._fsQuad.dispose()}},z=class extends F{constructor(e,t){super(),this.scene=e,this.camera=t,this.clear=!0,this.needsSwap=!1,this.inverse=!1}render(e,t,n){let r=e.getContext(),i=e.state;i.buffers.color.setMask(!1),i.buffers.depth.setMask(!1),i.buffers.color.setLocked(!0),i.buffers.depth.setLocked(!0);let a,o;this.inverse?(a=0,o=1):(a=1,o=0),i.buffers.stencil.setTest(!0),i.buffers.stencil.setOp(r.REPLACE,r.REPLACE,r.REPLACE),i.buffers.stencil.setFunc(r.ALWAYS,a,4294967295),i.buffers.stencil.setClear(o),i.buffers.stencil.setLocked(!0),e.setRenderTarget(n),this.clear&&e.clear(),e.render(this.scene,this.camera),e.setRenderTarget(t),this.clear&&e.clear(),e.render(this.scene,this.camera),i.buffers.color.setLocked(!1),i.buffers.depth.setLocked(!1),i.buffers.color.setMask(!0),i.buffers.depth.setMask(!0),i.buffers.stencil.setLocked(!1),i.buffers.stencil.setFunc(r.EQUAL,1,4294967295),i.buffers.stencil.setOp(r.KEEP,r.KEEP,r.KEEP),i.buffers.stencil.setLocked(!0)}},B=class extends F{constructor(){super(),this.needsSwap=!1}render(e){e.state.buffers.stencil.setLocked(!1),e.state.buffers.stencil.setTest(!1)}},V=class{constructor(r,i){if(this.renderer=r,this._pixelRatio=r.getPixelRatio(),i===void 0){let n=r.getSize(new e);this._width=n.width,this._height=n.height,i=new s(this._width*this._pixelRatio,this._height*this._pixelRatio,{type:t}),i.texture.name=`EffectComposer.rt1`}else this._width=i.width,this._height=i.height;this.renderTarget1=i,this.renderTarget2=i.clone(),this.renderTarget2.texture.name=`EffectComposer.rt2`,this.writeBuffer=this.renderTarget1,this.readBuffer=this.renderTarget2,this.renderToScreen=!0,this.passes=[],this.copyPass=new ne(P),this.copyPass.material.blending=0,this.timer=new n}swapBuffers(){let e=this.readBuffer;this.readBuffer=this.writeBuffer,this.writeBuffer=e}addPass(e){this.passes.push(e),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}insertPass(e,t){this.passes.splice(t,0,e),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}removePass(e){let t=this.passes.indexOf(e);t!==-1&&this.passes.splice(t,1)}isLastEnabledPass(e){for(let t=e+1;t<this.passes.length;t++)if(this.passes[t].enabled)return!1;return!0}render(e){this.timer.update(),e===void 0&&(e=this.timer.getDelta());let t=this.renderer.getRenderTarget(),n=!1;for(let t=0,r=this.passes.length;t<r;t++){let r=this.passes[t];if(r.enabled!==!1){if(r.renderToScreen=this.renderToScreen&&this.isLastEnabledPass(t),r.render(this.renderer,this.writeBuffer,this.readBuffer,e,n),r.needsSwap){if(n){let t=this.renderer.getContext(),n=this.renderer.state.buffers.stencil;n.setFunc(t.NOTEQUAL,1,4294967295),this.copyPass.render(this.renderer,this.writeBuffer,this.readBuffer,e),n.setFunc(t.EQUAL,1,4294967295)}this.swapBuffers()}z!==void 0&&(r instanceof z?n=!0:r instanceof B&&(n=!1))}}this.renderer.setRenderTarget(t)}reset(t){if(t===void 0){let n=this.renderer.getSize(new e);this._pixelRatio=this.renderer.getPixelRatio(),this._width=n.width,this._height=n.height,t=this.renderTarget1.clone(),t.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}this.renderTarget1.dispose(),this.renderTarget2.dispose(),this.renderTarget1=t,this.renderTarget2=t.clone(),this.writeBuffer=this.renderTarget1,this.readBuffer=this.renderTarget2}setSize(e,t){this._width=e,this._height=t;let n=this._width*this._pixelRatio,r=this._height*this._pixelRatio;this.renderTarget1.setSize(n,r),this.renderTarget2.setSize(n,r);for(let e=0;e<this.passes.length;e++)this.passes[e].setSize(n,r)}setPixelRatio(e){this._pixelRatio=e,this.setSize(this._width,this._height)}dispose(){this.renderTarget1.dispose(),this.renderTarget2.dispose(),this.copyPass.dispose()}},H=class extends F{constructor(e,t,n=null,r=null,i=null){super(),this.scene=e,this.camera=t,this.overrideMaterial=n,this.clearColor=r,this.clearAlpha=i,this.clear=!0,this.clearDepth=!1,this.needsSwap=!1,this.isRenderPass=!0,this._oldClearColor=new T}render(e,t,n){let r=e.autoClear;e.autoClear=!1;let i,a;this.overrideMaterial!==null&&(a=this.scene.overrideMaterial,this.scene.overrideMaterial=this.overrideMaterial),this.clearColor!==null&&(e.getClearColor(this._oldClearColor),e.setClearColor(this.clearColor,e.getClearAlpha())),this.clearAlpha!==null&&(i=e.getClearAlpha(),e.setClearAlpha(this.clearAlpha)),this.clearDepth==1&&e.clearDepth(),e.setRenderTarget(this.renderToScreen?null:n),this.clear===!0&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),e.render(this.scene,this.camera),this.clearColor!==null&&e.setClearColor(this._oldClearColor),this.clearAlpha!==null&&e.setClearAlpha(i),this.overrideMaterial!==null&&(this.scene.overrideMaterial=a),e.autoClear=r}},U=class n extends F{constructor(n,r,i,o){super(),this.renderScene=r,this.renderCamera=i,this.selectedObjects=o===void 0?[]:o,this.visibleEdgeColor=new T(1,1,1),this.hiddenEdgeColor=new T(.1,.04,.02),this.edgeGlow=0,this.usePatternTexture=!1,this.patternTexture=null,this.edgeThickness=1,this.edgeStrength=3,this.downSampleRatio=2,this.pulsePeriod=0,this._visibilityCache=new Map,this._selectionCache=new Set,this.resolution=n===void 0?new e(256,256):new e(n.x,n.y);let c=Math.round(this.resolution.x/this.downSampleRatio),l=Math.round(this.resolution.y/this.downSampleRatio);this.renderTargetMaskBuffer=new s(this.resolution.x,this.resolution.y),this.renderTargetMaskBuffer.texture.name=`OutlinePass.mask`,this.renderTargetMaskBuffer.texture.generateMipmaps=!1,this.depthMaterial=new a,this.depthMaterial.side=2,this.depthMaterial.depthPacking=h,this.depthMaterial.blending=0,this.prepareMaskMaterial=this._getPrepareMaskMaterial(),this.prepareMaskMaterial.side=2,this.prepareMaskMaterial.fragmentShader=f(this.prepareMaskMaterial.fragmentShader,this.renderCamera),this.renderTargetDepthBuffer=new s(this.resolution.x,this.resolution.y,{type:t}),this.renderTargetDepthBuffer.texture.name=`OutlinePass.depth`,this.renderTargetDepthBuffer.texture.generateMipmaps=!1,this.renderTargetMaskDownSampleBuffer=new s(c,l,{type:t,depthBuffer:!1}),this.renderTargetMaskDownSampleBuffer.texture.name=`OutlinePass.depthDownSample`,this.renderTargetMaskDownSampleBuffer.texture.generateMipmaps=!1,this.renderTargetBlurBuffer1=new s(c,l,{type:t,depthBuffer:!1}),this.renderTargetBlurBuffer1.texture.name=`OutlinePass.blur1`,this.renderTargetBlurBuffer1.texture.generateMipmaps=!1,this.renderTargetBlurBuffer2=new s(Math.round(c/2),Math.round(l/2),{type:t,depthBuffer:!1}),this.renderTargetBlurBuffer2.texture.name=`OutlinePass.blur2`,this.renderTargetBlurBuffer2.texture.generateMipmaps=!1,this.edgeDetectionMaterial=this._getEdgeDetectionMaterial(),this.renderTargetEdgeBuffer1=new s(c,l,{type:t,depthBuffer:!1}),this.renderTargetEdgeBuffer1.texture.name=`OutlinePass.edge1`,this.renderTargetEdgeBuffer1.texture.generateMipmaps=!1,this.renderTargetEdgeBuffer2=new s(Math.round(c/2),Math.round(l/2),{type:t,depthBuffer:!1}),this.renderTargetEdgeBuffer2.texture.name=`OutlinePass.edge2`,this.renderTargetEdgeBuffer2.texture.generateMipmaps=!1,this.separableBlurMaterial1=this._getSeparableBlurMaterial(4),this.separableBlurMaterial1.uniforms.texSize.value.set(c,l),this.separableBlurMaterial1.uniforms.kernelRadius.value=1,this.separableBlurMaterial2=this._getSeparableBlurMaterial(4),this.separableBlurMaterial2.uniforms.texSize.value.set(Math.round(c/2),Math.round(l/2)),this.separableBlurMaterial2.uniforms.kernelRadius.value=4,this.overlayMaterial=this._getOverlayMaterial();let d=P;this.copyUniforms=S.clone(d.uniforms),this.materialCopy=new _({uniforms:this.copyUniforms,vertexShader:d.vertexShader,fragmentShader:d.fragmentShader,blending:0,depthTest:!1,depthWrite:!1}),this.enabled=!0,this.needsSwap=!1,this._oldClearColor=new T,this.oldClearAlpha=1,this._fsQuad=new R(null),this.tempPulseColor1=new T,this.tempPulseColor2=new T,this.textureMatrix=new u;function f(e,t){let n=t.isPerspectiveCamera?`perspective`:`orthographic`;return e.replace(/DEPTH_TO_VIEW_Z/g,n+`DepthToViewZ`)}}dispose(){this.renderTargetMaskBuffer.dispose(),this.renderTargetDepthBuffer.dispose(),this.renderTargetMaskDownSampleBuffer.dispose(),this.renderTargetBlurBuffer1.dispose(),this.renderTargetBlurBuffer2.dispose(),this.renderTargetEdgeBuffer1.dispose(),this.renderTargetEdgeBuffer2.dispose(),this.depthMaterial.dispose(),this.prepareMaskMaterial.dispose(),this.edgeDetectionMaterial.dispose(),this.separableBlurMaterial1.dispose(),this.separableBlurMaterial2.dispose(),this.overlayMaterial.dispose(),this.materialCopy.dispose(),this._fsQuad.dispose()}setSize(e,t){this.renderTargetMaskBuffer.setSize(e,t),this.renderTargetDepthBuffer.setSize(e,t);let n=Math.round(e/this.downSampleRatio),r=Math.round(t/this.downSampleRatio);this.renderTargetMaskDownSampleBuffer.setSize(n,r),this.renderTargetBlurBuffer1.setSize(n,r),this.renderTargetEdgeBuffer1.setSize(n,r),this.separableBlurMaterial1.uniforms.texSize.value.set(n,r),n=Math.round(n/2),r=Math.round(r/2),this.renderTargetBlurBuffer2.setSize(n,r),this.renderTargetEdgeBuffer2.setSize(n,r),this.separableBlurMaterial2.uniforms.texSize.value.set(n,r)}render(e,t,r,i,a){if(this.selectedObjects.length>0){e.getClearColor(this._oldClearColor),this.oldClearAlpha=e.getClearAlpha();let t=e.autoClear;e.autoClear=!1,a&&e.state.buffers.stencil.setTest(!1),e.setClearColor(16777215,1),this._updateSelectionCache(),this._changeVisibilityOfSelectedObjects(!1);let i=this.renderScene.background,o=this.renderScene.overrideMaterial;if(this.renderScene.background=null,this.renderScene.overrideMaterial=this.depthMaterial,e.setRenderTarget(this.renderTargetDepthBuffer),e.clear(),e.render(this.renderScene,this.renderCamera),this._changeVisibilityOfSelectedObjects(!0),this._visibilityCache.clear(),this._updateTextureMatrix(),this._changeVisibilityOfNonSelectedObjects(!1),this.renderScene.overrideMaterial=this.prepareMaskMaterial,this.prepareMaskMaterial.uniforms.cameraNearFar.value.set(this.renderCamera.near,this.renderCamera.far),this.prepareMaskMaterial.uniforms.depthTexture.value=this.renderTargetDepthBuffer.texture,this.prepareMaskMaterial.uniforms.textureMatrix.value=this.textureMatrix,e.setRenderTarget(this.renderTargetMaskBuffer),e.clear(),e.render(this.renderScene,this.renderCamera),this._changeVisibilityOfNonSelectedObjects(!0),this._visibilityCache.clear(),this._selectionCache.clear(),this.renderScene.background=i,this.renderScene.overrideMaterial=o,this._fsQuad.material=this.materialCopy,this.copyUniforms.tDiffuse.value=this.renderTargetMaskBuffer.texture,e.setRenderTarget(this.renderTargetMaskDownSampleBuffer),e.clear(),this._fsQuad.render(e),this.tempPulseColor1.copy(this.visibleEdgeColor),this.tempPulseColor2.copy(this.hiddenEdgeColor),this.pulsePeriod>0){let e=1.25/2+Math.cos(performance.now()*.01/this.pulsePeriod)*.75/2;this.tempPulseColor1.multiplyScalar(e),this.tempPulseColor2.multiplyScalar(e)}this._fsQuad.material=this.edgeDetectionMaterial,this.edgeDetectionMaterial.uniforms.maskTexture.value=this.renderTargetMaskDownSampleBuffer.texture,this.edgeDetectionMaterial.uniforms.texSize.value.set(this.renderTargetMaskDownSampleBuffer.width,this.renderTargetMaskDownSampleBuffer.height),this.edgeDetectionMaterial.uniforms.visibleEdgeColor.value=this.tempPulseColor1,this.edgeDetectionMaterial.uniforms.hiddenEdgeColor.value=this.tempPulseColor2,e.setRenderTarget(this.renderTargetEdgeBuffer1),e.clear(),this._fsQuad.render(e),this._fsQuad.material=this.separableBlurMaterial1,this.separableBlurMaterial1.uniforms.colorTexture.value=this.renderTargetEdgeBuffer1.texture,this.separableBlurMaterial1.uniforms.direction.value=n.BlurDirectionX,this.separableBlurMaterial1.uniforms.kernelRadius.value=this.edgeThickness,e.setRenderTarget(this.renderTargetBlurBuffer1),e.clear(),this._fsQuad.render(e),this.separableBlurMaterial1.uniforms.colorTexture.value=this.renderTargetBlurBuffer1.texture,this.separableBlurMaterial1.uniforms.direction.value=n.BlurDirectionY,e.setRenderTarget(this.renderTargetEdgeBuffer1),e.clear(),this._fsQuad.render(e),this._fsQuad.material=this.separableBlurMaterial2,this.separableBlurMaterial2.uniforms.colorTexture.value=this.renderTargetEdgeBuffer1.texture,this.separableBlurMaterial2.uniforms.direction.value=n.BlurDirectionX,e.setRenderTarget(this.renderTargetBlurBuffer2),e.clear(),this._fsQuad.render(e),this.separableBlurMaterial2.uniforms.colorTexture.value=this.renderTargetBlurBuffer2.texture,this.separableBlurMaterial2.uniforms.direction.value=n.BlurDirectionY,e.setRenderTarget(this.renderTargetEdgeBuffer2),e.clear(),this._fsQuad.render(e),this._fsQuad.material=this.overlayMaterial,this.overlayMaterial.uniforms.maskTexture.value=this.renderTargetMaskBuffer.texture,this.overlayMaterial.uniforms.edgeTexture1.value=this.renderTargetEdgeBuffer1.texture,this.overlayMaterial.uniforms.edgeTexture2.value=this.renderTargetEdgeBuffer2.texture,this.overlayMaterial.uniforms.patternTexture.value=this.patternTexture,this.overlayMaterial.uniforms.edgeStrength.value=this.edgeStrength,this.overlayMaterial.uniforms.edgeGlow.value=this.edgeGlow,this.overlayMaterial.uniforms.usePatternTexture.value=this.usePatternTexture,a&&e.state.buffers.stencil.setTest(!0),e.setRenderTarget(r),this._fsQuad.render(e),e.setClearColor(this._oldClearColor,this.oldClearAlpha),e.autoClear=t}this.renderToScreen&&(this._fsQuad.material=this.materialCopy,this.copyUniforms.tDiffuse.value=r.texture,e.setRenderTarget(null),this._fsQuad.render(e))}_updateSelectionCache(){let e=this._selectionCache;function t(t){t.isMesh&&e.add(t)}e.clear();for(let e=0;e<this.selectedObjects.length;e++)this.selectedObjects[e].traverse(t)}_changeVisibilityOfSelectedObjects(e){let t=this._visibilityCache;for(let n of this._selectionCache)e===!0?n.visible=t.get(n):(t.set(n,n.visible),n.visible=e)}_changeVisibilityOfNonSelectedObjects(e){let t=this._visibilityCache,n=this._selectionCache;function r(r){if(r.isPoints||r.isLine||r.isLine2)e===!0?r.visible=t.get(r):(t.set(r,r.visible),r.visible=e);else if((r.isMesh||r.isSprite)&&!n.has(r)){let n=r.visible;(e===!1||t.get(r)===!0)&&(r.visible=e),t.set(r,n)}}this.renderScene.traverse(r)}_updateTextureMatrix(){this.textureMatrix.set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1),this.textureMatrix.multiply(this.renderCamera.projectionMatrix),this.textureMatrix.multiply(this.renderCamera.matrixWorldInverse)}_getPrepareMaskMaterial(){return new _({uniforms:{depthTexture:{value:null},cameraNearFar:{value:new e(.5,.5)},textureMatrix:{value:null}},vertexShader:`#include <batching_pars_vertex>
				#include <morphtarget_pars_vertex>
				#include <skinning_pars_vertex>

				varying vec4 projTexCoord;
				varying vec4 vPosition;
				uniform mat4 textureMatrix;

				void main() {

					#include <batching_vertex>
					#include <skinbase_vertex>
					#include <begin_vertex>
					#include <morphtarget_vertex>
					#include <skinning_vertex>
					#include <project_vertex>

					vPosition = mvPosition;

					vec4 worldPosition = vec4( transformed, 1.0 );

					#ifdef USE_INSTANCING

						worldPosition = instanceMatrix * worldPosition;

					#endif

					worldPosition = modelMatrix * worldPosition;

					projTexCoord = textureMatrix * worldPosition;

				}`,fragmentShader:`#include <packing>
				varying vec4 vPosition;
				varying vec4 projTexCoord;
				uniform sampler2D depthTexture;
				uniform vec2 cameraNearFar;

				void main() {

					float depth = unpackRGBAToDepth(texture2DProj( depthTexture, projTexCoord ));
					float viewZ = - DEPTH_TO_VIEW_Z( depth, cameraNearFar.x, cameraNearFar.y );
					float depthTest = (-vPosition.z > viewZ) ? 1.0 : 0.0;
					gl_FragColor = vec4(0.0, depthTest, 1.0, 1.0);

				}`})}_getEdgeDetectionMaterial(){return new _({uniforms:{maskTexture:{value:null},texSize:{value:new e(.5,.5)},visibleEdgeColor:{value:new x(1,1,1)},hiddenEdgeColor:{value:new x(1,1,1)}},vertexShader:`varying vec2 vUv;

				void main() {
					vUv = uv;
					gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
				}`,fragmentShader:`varying vec2 vUv;

				uniform sampler2D maskTexture;
				uniform vec2 texSize;
				uniform vec3 visibleEdgeColor;
				uniform vec3 hiddenEdgeColor;

				void main() {
					vec2 invSize = 1.0 / texSize;
					vec4 uvOffset = vec4(1.0, 0.0, 0.0, 1.0) * vec4(invSize, invSize);
					vec4 c1 = texture2D( maskTexture, vUv + uvOffset.xy);
					vec4 c2 = texture2D( maskTexture, vUv - uvOffset.xy);
					vec4 c3 = texture2D( maskTexture, vUv + uvOffset.yw);
					vec4 c4 = texture2D( maskTexture, vUv - uvOffset.yw);
					float diff1 = (c1.r - c2.r)*0.5;
					float diff2 = (c3.r - c4.r)*0.5;
					float d = length( vec2(diff1, diff2) );
					float a1 = min(c1.g, c2.g);
					float a2 = min(c3.g, c4.g);
					float visibilityFactor = min(a1, a2);
					vec3 edgeColor = 1.0 - visibilityFactor > 0.001 ? visibleEdgeColor : hiddenEdgeColor;
					gl_FragColor = vec4(edgeColor, 1.0) * vec4(d);
				}`})}_getSeparableBlurMaterial(t){return new _({defines:{MAX_RADIUS:t},uniforms:{colorTexture:{value:null},texSize:{value:new e(.5,.5)},direction:{value:new e(.5,.5)},kernelRadius:{value:1}},vertexShader:`varying vec2 vUv;

				void main() {
					vUv = uv;
					gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
				}`,fragmentShader:`#include <common>
				varying vec2 vUv;
				uniform sampler2D colorTexture;
				uniform vec2 texSize;
				uniform vec2 direction;
				uniform float kernelRadius;

				float gaussianPdf(in float x, in float sigma) {
					return 0.39894 * exp( -0.5 * x * x/( sigma * sigma))/sigma;
				}

				void main() {
					vec2 invSize = 1.0 / texSize;
					float sigma = kernelRadius/2.0;
					float weightSum = gaussianPdf(0.0, sigma);
					vec4 diffuseSum = texture2D( colorTexture, vUv) * weightSum;
					vec2 delta = direction * invSize * kernelRadius/float(MAX_RADIUS);
					vec2 uvOffset = delta;
					for( int i = 1; i <= MAX_RADIUS; i ++ ) {
						float x = kernelRadius * float(i) / float(MAX_RADIUS);
						float w = gaussianPdf(x, sigma);
						vec4 sample1 = texture2D( colorTexture, vUv + uvOffset);
						vec4 sample2 = texture2D( colorTexture, vUv - uvOffset);
						diffuseSum += ((sample1 + sample2) * w);
						weightSum += (2.0 * w);
						uvOffset += delta;
					}
					gl_FragColor = diffuseSum/weightSum;
				}`})}_getOverlayMaterial(){return new _({uniforms:{maskTexture:{value:null},edgeTexture1:{value:null},edgeTexture2:{value:null},patternTexture:{value:null},edgeStrength:{value:1},edgeGlow:{value:1},usePatternTexture:{value:0}},vertexShader:`varying vec2 vUv;

				void main() {
					vUv = uv;
					gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
				}`,fragmentShader:`varying vec2 vUv;

				uniform sampler2D maskTexture;
				uniform sampler2D edgeTexture1;
				uniform sampler2D edgeTexture2;
				uniform sampler2D patternTexture;
				uniform float edgeStrength;
				uniform float edgeGlow;
				uniform bool usePatternTexture;

				void main() {
					vec4 edgeValue1 = texture2D(edgeTexture1, vUv);
					vec4 edgeValue2 = texture2D(edgeTexture2, vUv);
					vec4 maskColor = texture2D(maskTexture, vUv);
					vec4 patternColor = texture2D(patternTexture, 6.0 * vUv);
					float visibilityFactor = 1.0 - maskColor.g > 0.0 ? 1.0 : 0.5;
					vec4 edgeValue = edgeValue1 + edgeValue2 * edgeGlow;
					vec4 finalColor = edgeStrength * maskColor.r * edgeValue;
					if(usePatternTexture)
						finalColor += + visibilityFactor * (1.0 - maskColor.r) * (1.0 - patternColor.r);
					gl_FragColor = finalColor;
				}`,blending:2,depthTest:!1,depthWrite:!1,transparent:!0})}};U.BlurDirectionX=new e(1,0),U.BlurDirectionY=new e(0,1);var W={name:`LuminosityHighPassShader`,uniforms:{tDiffuse:{value:null},luminosityThreshold:{value:1},smoothWidth:{value:1},defaultColor:{value:new T(0)},defaultOpacity:{value:0}},vertexShader:`

		varying vec2 vUv;

		void main() {

			vUv = uv;

			gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

		}`,fragmentShader:`

		uniform sampler2D tDiffuse;
		uniform vec3 defaultColor;
		uniform float defaultOpacity;
		uniform float luminosityThreshold;
		uniform float smoothWidth;

		varying vec2 vUv;

		void main() {

			vec4 texel = texture2D( tDiffuse, vUv );

			float v = luminance( texel.xyz );

			vec4 outputColor = vec4( defaultColor.rgb, defaultOpacity );

			float alpha = smoothstep( luminosityThreshold, luminosityThreshold + smoothWidth, v );

			gl_FragColor = mix( outputColor, texel, alpha );

		}`},G=class n extends F{constructor(n,i=1,a,o){super(),this.strength=i,this.radius=a,this.threshold=o,this.resolution=n===void 0?new e(256,256):new e(n.x,n.y),this.clearColor=new T(0,0,0),this.needsSwap=!1,this.renderTargetsHorizontal=[],this.renderTargetsVertical=[],this.nMips=5;let c=Math.round(this.resolution.x/2),l=Math.round(this.resolution.y/2);this.renderTargetBright=new s(c,l,{type:t,depthBuffer:!1}),this.renderTargetBright.texture.name=`UnrealBloomPass.bright`,this.renderTargetBright.texture.generateMipmaps=!1;for(let e=0;e<this.nMips;e++){let n=new s(c,l,{type:t,depthBuffer:!1});n.texture.name=`UnrealBloomPass.h`+e,n.texture.generateMipmaps=!1,this.renderTargetsHorizontal.push(n);let r=new s(c,l,{type:t,depthBuffer:!1});r.texture.name=`UnrealBloomPass.v`+e,r.texture.generateMipmaps=!1,this.renderTargetsVertical.push(r),c=Math.round(c/2),l=Math.round(l/2)}let u=W;this.highPassUniforms=S.clone(u.uniforms),this.highPassUniforms.luminosityThreshold.value=o,this.highPassUniforms.smoothWidth.value=.01,this.materialHighPassFilter=new _({uniforms:this.highPassUniforms,vertexShader:u.vertexShader,fragmentShader:u.fragmentShader}),this.separableBlurMaterials=[];let d=[6,10,14,18,22];c=Math.round(this.resolution.x/2),l=Math.round(this.resolution.y/2);for(let t=0;t<this.nMips;t++)this.separableBlurMaterials.push(this._getSeparableBlurMaterial(d[t])),this.separableBlurMaterials[t].uniforms.invSize.value=new e(1/c,1/l),c=Math.round(c/2),l=Math.round(l/2);this.compositeMaterial=this._getCompositeMaterial(this.nMips),this.compositeMaterial.uniforms.blurTexture1.value=this.renderTargetsVertical[0].texture,this.compositeMaterial.uniforms.blurTexture2.value=this.renderTargetsVertical[1].texture,this.compositeMaterial.uniforms.blurTexture3.value=this.renderTargetsVertical[2].texture,this.compositeMaterial.uniforms.blurTexture4.value=this.renderTargetsVertical[3].texture,this.compositeMaterial.uniforms.blurTexture5.value=this.renderTargetsVertical[4].texture,this.compositeMaterial.uniforms.bloomStrength.value=i,this.compositeMaterial.uniforms.bloomRadius.value=.1;let f=[1,.8,.6,.4,.2];this.compositeMaterial.uniforms.bloomFactors.value=f,this.bloomTintColors=[new x(1,1,1),new x(1,1,1),new x(1,1,1),new x(1,1,1),new x(1,1,1)],this.compositeMaterial.uniforms.bloomTintColors.value=this.bloomTintColors,this.copyUniforms=S.clone(P.uniforms),this.blendMaterial=new _({uniforms:this.copyUniforms,vertexShader:P.vertexShader,fragmentShader:P.fragmentShader,premultipliedAlpha:!0,blending:2,depthTest:!1,depthWrite:!1,transparent:!0}),this._oldClearColor=new T,this._oldClearAlpha=1,this._basic=new r,this._fsQuad=new R(null)}dispose(){for(let e=0;e<this.renderTargetsHorizontal.length;e++)this.renderTargetsHorizontal[e].dispose();for(let e=0;e<this.renderTargetsVertical.length;e++)this.renderTargetsVertical[e].dispose();this.renderTargetBright.dispose();for(let e=0;e<this.separableBlurMaterials.length;e++)this.separableBlurMaterials[e].dispose();this.compositeMaterial.dispose(),this.blendMaterial.dispose(),this._basic.dispose(),this._fsQuad.dispose()}setSize(t,n){let r=Math.round(t/2),i=Math.round(n/2);this.renderTargetBright.setSize(r,i);for(let t=0;t<this.nMips;t++)this.renderTargetsHorizontal[t].setSize(r,i),this.renderTargetsVertical[t].setSize(r,i),this.separableBlurMaterials[t].uniforms.invSize.value=new e(1/r,1/i),r=Math.round(r/2),i=Math.round(i/2)}render(e,t,r,i,a){e.getClearColor(this._oldClearColor),this._oldClearAlpha=e.getClearAlpha();let o=e.autoClear;e.autoClear=!1,e.setClearColor(this.clearColor,0),a&&e.state.buffers.stencil.setTest(!1),this.renderToScreen&&(this._fsQuad.material=this._basic,this._basic.map=r.texture,e.setRenderTarget(null),e.clear(),this._fsQuad.render(e)),this.highPassUniforms.tDiffuse.value=r.texture,this.highPassUniforms.luminosityThreshold.value=this.threshold,this._fsQuad.material=this.materialHighPassFilter,e.setRenderTarget(this.renderTargetBright),e.clear(),this._fsQuad.render(e);let s=this.renderTargetBright;for(let t=0;t<this.nMips;t++)this._fsQuad.material=this.separableBlurMaterials[t],this.separableBlurMaterials[t].uniforms.colorTexture.value=s.texture,this.separableBlurMaterials[t].uniforms.direction.value=n.BlurDirectionX,e.setRenderTarget(this.renderTargetsHorizontal[t]),e.clear(),this._fsQuad.render(e),this.separableBlurMaterials[t].uniforms.colorTexture.value=this.renderTargetsHorizontal[t].texture,this.separableBlurMaterials[t].uniforms.direction.value=n.BlurDirectionY,e.setRenderTarget(this.renderTargetsVertical[t]),e.clear(),this._fsQuad.render(e),s=this.renderTargetsVertical[t];this._fsQuad.material=this.compositeMaterial,this.compositeMaterial.uniforms.bloomStrength.value=this.strength,this.compositeMaterial.uniforms.bloomRadius.value=this.radius,this.compositeMaterial.uniforms.bloomTintColors.value=this.bloomTintColors,e.setRenderTarget(this.renderTargetsHorizontal[0]),e.clear(),this._fsQuad.render(e),this._fsQuad.material=this.blendMaterial,this.copyUniforms.tDiffuse.value=this.renderTargetsHorizontal[0].texture,a&&e.state.buffers.stencil.setTest(!0),this.renderToScreen?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(r),this._fsQuad.render(e)),e.setClearColor(this._oldClearColor,this._oldClearAlpha),e.autoClear=o}_getSeparableBlurMaterial(t){let n=[],r=t/3;for(let e=0;e<t;e++)n.push(.39894*Math.exp(-.5*e*e/(r*r))/r);let i=[],a=[];for(let e=1;e<t;e+=2){let r=n[e],o=e+1<t?n[e+1]:0,s=r+o;i.push((e*r+(e+1)*o)/s),a.push(s)}return new _({defines:{KERNEL_PAIRS:i.length},uniforms:{colorTexture:{value:null},invSize:{value:new e(.5,.5)},direction:{value:new e(.5,.5)},centerWeight:{value:n[0]},gaussianOffsets:{value:i},gaussianWeights:{value:a}},vertexShader:`

				varying vec2 vUv;

				void main() {

					vUv = uv;
					gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

				}`,fragmentShader:`

				#include <common>

				varying vec2 vUv;

				uniform sampler2D colorTexture;
				uniform vec2 invSize;
				uniform vec2 direction;
				uniform float centerWeight;
				uniform float gaussianOffsets[KERNEL_PAIRS];
				uniform float gaussianWeights[KERNEL_PAIRS];

				void main() {

					vec3 diffuseSum = texture2D( colorTexture, vUv ).rgb * centerWeight;

					for ( int i = 0; i < KERNEL_PAIRS; i ++ ) {

						vec2 uvOffset = direction * invSize * gaussianOffsets[ i ];
						vec3 sample1 = texture2D( colorTexture, vUv + uvOffset ).rgb;
						vec3 sample2 = texture2D( colorTexture, vUv - uvOffset ).rgb;
						diffuseSum += ( sample1 + sample2 ) * gaussianWeights[ i ];

					}

					gl_FragColor = vec4( diffuseSum, 1.0 );

				}`})}_getCompositeMaterial(e){return new _({defines:{NUM_MIPS:e},uniforms:{blurTexture1:{value:null},blurTexture2:{value:null},blurTexture3:{value:null},blurTexture4:{value:null},blurTexture5:{value:null},bloomStrength:{value:1},bloomFactors:{value:null},bloomTintColors:{value:null},bloomRadius:{value:0}},vertexShader:`

				varying vec2 vUv;

				void main() {

					vUv = uv;
					gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

				}`,fragmentShader:`

				varying vec2 vUv;

				uniform sampler2D blurTexture1;
				uniform sampler2D blurTexture2;
				uniform sampler2D blurTexture3;
				uniform sampler2D blurTexture4;
				uniform sampler2D blurTexture5;
				uniform float bloomStrength;
				uniform float bloomRadius;
				uniform float bloomFactors[NUM_MIPS];
				uniform vec3 bloomTintColors[NUM_MIPS];

				float lerpBloomFactor( const in float factor ) {

					float mirrorFactor = 1.2 - factor;
					return mix( factor, mirrorFactor, bloomRadius );

				}

				void main() {

					// 3.0 for backwards compatibility with previous alpha-based intensity
					vec3 bloom = 3.0 * bloomStrength * (
						lerpBloomFactor( bloomFactors[ 0 ] ) * bloomTintColors[ 0 ] * texture2D( blurTexture1, vUv ).rgb +
						lerpBloomFactor( bloomFactors[ 1 ] ) * bloomTintColors[ 1 ] * texture2D( blurTexture2, vUv ).rgb +
						lerpBloomFactor( bloomFactors[ 2 ] ) * bloomTintColors[ 2 ] * texture2D( blurTexture3, vUv ).rgb +
						lerpBloomFactor( bloomFactors[ 3 ] ) * bloomTintColors[ 3 ] * texture2D( blurTexture4, vUv ).rgb +
						lerpBloomFactor( bloomFactors[ 4 ] ) * bloomTintColors[ 4 ] * texture2D( blurTexture5, vUv ).rgb
					);

					float bloomAlpha = max( bloom.r, max( bloom.g, bloom.b ) );
					gl_FragColor = vec4( bloom, bloomAlpha );

				}`})}};G.BlurDirectionX=new e(1,0),G.BlurDirectionY=new e(0,1);var K={name:`OutputShader`,uniforms:{tDiffuse:{value:null},toneMappingExposure:{value:1}},vertexShader:`
		precision highp float;

		uniform mat4 modelViewMatrix;
		uniform mat4 projectionMatrix;

		attribute vec3 position;
		attribute vec2 uv;

		varying vec2 vUv;

		void main() {

			vUv = uv;
			gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

		}`,fragmentShader:`

		precision highp float;

		uniform sampler2D tDiffuse;

		#include <tonemapping_pars_fragment>
		#include <colorspace_pars_fragment>

		varying vec2 vUv;

		void main() {

			gl_FragColor = texture2D( tDiffuse, vUv );

			// tone mapping

			#ifdef LINEAR_TONE_MAPPING

				gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );

			#elif defined( REINHARD_TONE_MAPPING )

				gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );

			#elif defined( CINEON_TONE_MAPPING )

				gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );

			#elif defined( ACES_FILMIC_TONE_MAPPING )

				gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );

			#elif defined( AGX_TONE_MAPPING )

				gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );

			#elif defined( NEUTRAL_TONE_MAPPING )

				gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );

			#elif defined( CUSTOM_TONE_MAPPING )

				gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );

			#endif

			// color space

			#ifdef SRGB_TRANSFER

				gl_FragColor = sRGBTransferOETF( gl_FragColor );

			#endif

		}`},q=class extends F{constructor(){super(),this.isOutputPass=!0,this.uniforms=S.clone(K.uniforms),this.material=new w({name:K.name,uniforms:this.uniforms,vertexShader:K.vertexShader,fragmentShader:K.fragmentShader}),this._fsQuad=new R(this.material),this._outputColorSpace=null,this._toneMapping=null}render(e,t,n){this.uniforms.tDiffuse.value=n.texture,this.uniforms.toneMappingExposure.value=e.toneMappingExposure,(this._outputColorSpace!==e.outputColorSpace||this._toneMapping!==e.toneMapping)&&(this._outputColorSpace=e.outputColorSpace,this._toneMapping=e.toneMapping,this.material.defines={},v.getTransfer(this._outputColorSpace)===`srgb`&&(this.material.defines.SRGB_TRANSFER=``),this._toneMapping===1?this.material.defines.LINEAR_TONE_MAPPING=``:this._toneMapping===2?this.material.defines.REINHARD_TONE_MAPPING=``:this._toneMapping===3?this.material.defines.CINEON_TONE_MAPPING=``:this._toneMapping===4?this.material.defines.ACES_FILMIC_TONE_MAPPING=``:this._toneMapping===6?this.material.defines.AGX_TONE_MAPPING=``:this._toneMapping===7?this.material.defines.NEUTRAL_TONE_MAPPING=``:this._toneMapping===5&&(this.material.defines.CUSTOM_TONE_MAPPING=``),this.material.needsUpdate=!0),this.renderToScreen===!0?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(t),this.clear&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),this._fsQuad.render(e))}dispose(){this.material.dispose(),this._fsQuad.dispose()}},J=class extends y{constructor(){super(),this.name=`RoomEnvironment`,this.position.y=-3.5;let e=new k;e.deleteAttribute(`uv`);let t=new p({side:1}),n=new p,r=new O(16777215,900,28,2);r.position.set(.418,16.199,.3),this.add(r);let i=new d(e,t);i.position.set(-.757,13.219,.717),i.scale.set(31.713,28.305,28.591),this.add(i);let a=new o(e,n,6),s=new f;s.position.set(-10.906,2.009,1.846),s.rotation.set(0,-.195,0),s.scale.set(2.328,7.905,4.651),s.updateMatrix(),a.setMatrixAt(0,s.matrix),s.position.set(-5.607,-.754,-.758),s.rotation.set(0,.994,0),s.scale.set(1.97,1.534,3.955),s.updateMatrix(),a.setMatrixAt(1,s.matrix),s.position.set(6.167,.857,7.803),s.rotation.set(0,.561,0),s.scale.set(3.927,6.285,3.687),s.updateMatrix(),a.setMatrixAt(2,s.matrix),s.position.set(-2.017,.018,6.124),s.rotation.set(0,.333,0),s.scale.set(2.002,4.566,2.064),s.updateMatrix(),a.setMatrixAt(3,s.matrix),s.position.set(2.291,-.756,-2.621),s.rotation.set(0,-.286,0),s.scale.set(1.546,1.552,1.496),s.updateMatrix(),a.setMatrixAt(4,s.matrix),s.position.set(-2.193,-.369,-5.547),s.rotation.set(0,.516,0),s.scale.set(3.875,3.487,2.986),s.updateMatrix(),a.setMatrixAt(5,s.matrix),this.add(a);let c=new d(e,Y(50));c.position.set(-16.116,14.37,8.208),c.scale.set(.1,2.428,2.739),this.add(c);let l=new d(e,Y(50));l.position.set(-16.109,18.021,-8.207),l.scale.set(.1,2.425,2.751),this.add(l);let u=new d(e,Y(17));u.position.set(14.904,12.198,-1.832),u.scale.set(.15,4.265,6.331),this.add(u);let m=new d(e,Y(43));m.position.set(-.462,8.89,14.52),m.scale.set(4.38,5.441,.088),this.add(m);let h=new d(e,Y(20));h.position.set(3.235,11.486,-12.541),h.scale.set(2.5,2,.1),this.add(h);let g=new d(e,Y(100));g.position.set(0,20,0),g.scale.set(1,.1,1),this.add(g)}dispose(){let e=new Set;this.traverse(t=>{t.isMesh&&(e.add(t.geometry),e.add(t.material))});for(let t of e)t.dispose()}};function Y(e){return new D({color:0,emissive:16777215,emissiveIntensity:e})}var X=()=>window.matchMedia(`(prefers-reduced-motion: reduce)`).matches,Z=()=>document.documentElement.lang===`it`?`it`:`en`,re=(e,t=0)=>e.toLocaleString(Z()===`it`?`it-IT`:`en-GB`,{minimumFractionDigits:t,maximumFractionDigits:t}),Q=e=>String(e??``).replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#39;`})[e]);function ie(){try{let e=document.createElement(`canvas`);return!!(e.getContext(`webgl2`)||e.getContext(`webgl`))}catch{return!1}}function ae(t,n={}){let r=new b({antialias:!0,alpha:n.background===null,powerPreference:`high-performance`});r.setPixelRatio(Math.min(window.devicePixelRatio||1,1.75)),r.outputColorSpace=E,r.toneMapping=4,r.toneMappingExposure=1,n.shadows!==!1&&(r.shadowMap.enabled=!0,r.shadowMap.type=1),r.debug.checkShaderErrors=!1,r.domElement.className=`mx-canvas`,r.domElement.setAttribute(`aria-hidden`,`true`),t.appendChild(r.domElement);let i=new j;i.domElement.className=`mx-labels`,t.appendChild(i.domElement);let a=new y;n.background!==null&&(a.background=new T(n.background??395534));let o=new te(r),s=o.fromScene(new J,.04).texture;a.environment=s,a.environmentIntensity=n.env??.55;let c=new ee(n.fov??40,1,n.near??.05,n.far??2e3);n.zUp&&c.up.set(0,0,1),c.position.set(4,3,5);let l=new M(c,r.domElement);l.enableDamping=!0,l.dampingFactor=.08,l.enablePan=!!n.pan,l.zoomToCursor=!0;let u=new V(r);u.addPass(new H(a,c));let d=null;n.outline!==!1&&(d=new U(new e(256,256),a,c),d.edgeStrength=3.2,d.edgeGlow=.35,d.edgeThickness=1.4,d.pulsePeriod=0,d.visibleEdgeColor.set(8369407),d.hiddenEdgeColor.set(2771584),u.addPass(d));let f=null;n.bloom&&n.bloom>0&&(f=new G(new e(256,256),n.bloom,.4,.92),u.addPass(f)),u.addPass(new q);let p=()=>{let e=t.clientWidth||640,n=t.clientHeight||420;r.setSize(e,n),u.setSize(e,n),i.setSize(e,n),c.aspect=e/n,c.updateProjectionMatrix(),k()},m=new ResizeObserver(p),h=[],_=0,v=performance.now(),S=!1,C=!0,w=0,D=!1,O=e=>{if(_=0,!C)return;D=!0;let t=Math.min(.05,(e-v)/1e3);v=e;for(let n of h)n(t,e/1e3);l.update(),u.render(),i.render(a,c),w=h.length?0:w+1,D=!1,!_&&S&&!document.hidden&&w<90&&(_=requestAnimationFrame(O))};function k(){w=0,!_&&!D&&S&&C&&!document.hidden&&(v=performance.now(),_=requestAnimationFrame(O))}let A=new IntersectionObserver(e=>{S=e.some(e=>e.isIntersecting),S&&k()},{rootMargin:`80px`});A.observe(t);let N=()=>k();document.addEventListener(`visibilitychange`,N),l.addEventListener(`change`,k),m.observe(t),p();let P=new e,F=new g,I=e=>{let t=r.domElement.getBoundingClientRect();P.set((e.clientX-t.left)/t.width*2-1,-((e.clientY-t.top)/t.height)*2+1)};return r.domElement.addEventListener(`pointermove`,I),r.domElement.addEventListener(`pointerdown`,I),{host:t,scene:a,camera:c,renderer:r,controls:l,outline:d,bloom:f,labels:i,onFrame:e=>{h.push(e),k()},kick:k,frame:(e,t=new x(.6,.45,.9),n=new x)=>{let r=Math.tan(c.fov*Math.PI/360),i=e*1.15/(r*Math.min(1,c.aspect));c.position.copy(n).add(t.clone().normalize().multiplyScalar(i)),l.target.copy(n),c.near=Math.max(.01,i/2e3),c.far=Math.max(50,i*20),c.updateProjectionMatrix(),l.minDistance=e*.15,l.maxDistance=i*4,l.update(),k()},pointer:()=>P,raycast:(e,t=!0)=>(F.setFromCamera(P,c),F.intersectObjects(e,t)),dispose:()=>{C=!1,A.disconnect(),m.disconnect(),document.removeEventListener(`visibilitychange`,N),u.dispose(),r.dispose(),s.dispose(),o.dispose()},visible:()=>S}}function oe(e,t,n,r=``){let i=document.createElement(`div`);i.className=`mx-tag ${r}`,i.textContent=t;let a=new N(i);return a.position.copy(n),e.add(a),a}function $(e){for(;e&&!e.userData.part;)e=e.parent;return e}function se(e,t){let n=e.renderer.domElement,r=null,i=null,a=null,o=!1,s=0,c=new x,l=new x,u=new x,d=0,f=new g,p=t=>(f.setFromCamera(e.pointer(),e.camera),f.ray.intersectPlane(t,c)?c.clone():null),m=r=>{r!==a&&(a=r,e.outline&&(e.outline.selectedObjects=r?[r]:[]),n.style.cursor=r?t.grab?`grab`:`pointer`:``,t.hover?.(r),e.kick())};n.addEventListener(`pointermove`,n=>{if(r&&i){let n=p(i);if(n){let i=performance.now(),a=Math.max(.001,(i-d)/1e3);u.copy(n).sub(l).divideScalar(a).multiplyScalar(.5).add(u.clone().multiplyScalar(.5)),l.copy(n),d=i,s++,t.drag?.(r,n,u),e.kick()}}else if(o&&t.space){let n=p(t.space.plane());n&&t.space.move?.(n),s++,e.kick()}else if(n.pointerType===`mouse`){let n=e.raycast(t.targets())[0];m(n?$(n.object):null)}}),n.addEventListener(`pointerdown`,a=>{if(a.button!==0)return;s=0;let c=e.raycast(t.targets())[0],f=c?$(c.object):null;if(f){m(f);let o=t.grab?t.grab(f,c):null;if(o){r=f,i=o,e.controls.enabled=!1;let t=p(o);t&&l.copy(t),u.set(0,0,0),d=performance.now(),n.setPointerCapture(a.pointerId),n.style.cursor=`grabbing`;return}}else if(t.space){let r=p(t.space.plane());r&&(o=!0,e.controls.enabled=!1,t.space.down?.(r),n.setPointerCapture(a.pointerId))}});let h=a=>{if(r){let a=r;if(r=null,i=null,e.controls.enabled=!0,s<2){let n=e.raycast(t.targets())[0];n&&t.click?.(a,n)}t.release?.(a,u.clone()),n.style.cursor=`grab`}else if(o&&t.space){o=!1,e.controls.enabled=!0;let n=p(t.space.plane());n&&t.space.up?.(n)}else if(s<2&&a.button===0){let n=e.raycast(t.targets())[0],r=n?$(n.object):null;r&&n&&t.click?.(r,n)}try{n.releasePointerCapture(a.pointerId)}catch{}e.kick()};return n.addEventListener(`pointerup`,h),n.addEventListener(`pointercancel`,h),n.addEventListener(`pointerleave`,()=>{r||m(null)}),{hovered:()=>a,setHover:m}}function ce(e,t){let n=document.createElement(`div`);return n.className=`mx-panel`,n.hidden=!0,n.setAttribute(`role`,`region`),n.setAttribute(`aria-live`,`polite`),e.appendChild(n),{el:n,show:(e,r,i=[],a=``)=>{n.innerHTML=`<button type="button" class="mx-x" aria-label="${Q(t)}">×</button><h4>${Q(e)}</h4><p>${Q(r)}</p>`+(i.length?`<dl>${i.map(([e,t])=>`<div><dt>${Q(e)}</dt><dd>${Q(t)}</dd></div>`).join(``)}</dl>`:``)+a,n.hidden=!1,n.querySelector(`.mx-x`).addEventListener(`click`,()=>{n.hidden=!0})},hide:()=>{n.hidden=!0}}}function le(e){let t=document.createElement(`p`);return t.className=`mx-status`,t.setAttribute(`role`,`status`),t.setAttribute(`aria-live`,`polite`),e.appendChild(t),(e,n=``)=>{t.textContent=e,t.className=`mx-status ${n}`}}var ue={metal:(e,t=.3)=>new p({color:e,metalness:1,roughness:t}),plastic:(e,t=.55)=>new p({color:e,metalness:0,roughness:t}),silicon:()=>new i({color:3818064,metalness:.6,roughness:.18,iridescence:.55,iridescenceIOR:1.6,iridescenceThicknessRange:[180,620]}),glass:(e=16777215,t=.25)=>new i({color:e,metalness:0,roughness:.05,transmission:.9,thickness:.2,transparent:!0,opacity:t}),glow:(e,t=2)=>new p({color:e,emissive:e,emissiveIntensity:t,roughness:.4})};function de(e,t=4,n=!1){let r=new m(16774890,1.7);r.position.set(t*1.2,n?-t:t*2,n?t*2:t),r.castShadow=!0,r.shadow.mapSize.set(1024,1024);let i=r.shadow.camera;i.left=i.bottom=-t*1.5,i.right=i.top=t*1.5,i.near=.1,i.far=t*8,r.shadow.bias=-4e-4,r.shadow.normalBias=.02,r.shadow.radius=4;let a=new m(10274047,.65);return a.position.set(-t*1.5,t,n?t*.5:-t),e.add(r,a,new c(14412031,1711912,.25)),r}var fe=(e,t,n,r)=>t+(e-t)*Math.exp(-n*r);export{Z as a,ce as c,de as d,oe as f,se as i,X as l,Q as n,ae as o,ie as p,re as r,ue as s,fe as t,le as u};
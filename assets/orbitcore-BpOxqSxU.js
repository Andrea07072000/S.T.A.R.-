import{$ as e,A as t,U as n,W as r,a as i,et as a,g as o,j as s,k as c,n as l,nt as u,rt as d,t as f,tt as p,v as m,w as h,x as g,y as _}from"./three.module-BDaqb8_2.js";var v=new i,y=new p,b=class extends m{constructor(){super(),this.isLineSegmentsGeometry=!0,this.type=`LineSegmentsGeometry`,this.setIndex([0,2,1,2,3,1,2,4,3,4,5,3,4,6,5,6,7,5]),this.setAttribute(`position`,new o([-1,2,0,1,2,0,-1,1,0,1,1,0,-1,0,0,1,0,0,-1,-1,0,1,-1,0],3)),this.setAttribute(`uv`,new o([-1,2,1,2,-1,1,1,1,-1,-1,1,-1,-1,-2,1,-2],2))}applyMatrix4(e){let t=this.attributes.instanceStart,n=this.attributes.instanceEnd;return t!==void 0&&(t.applyMatrix4(e),n.applyMatrix4(e),t.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}setPositions(e){let t;e instanceof Float32Array?t=e:Array.isArray(e)&&(t=new Float32Array(e));let n=new _(t,6,1);return this.setAttribute(`instanceStart`,new g(n,3,0)),this.setAttribute(`instanceEnd`,new g(n,3,3)),this.instanceCount=this.attributes.instanceStart.count,this.computeBoundingBox(),this.computeBoundingSphere(),this}setColors(e){let t;e instanceof Float32Array?t=e:Array.isArray(e)&&(t=new Float32Array(e));let n=new _(t,6,1);return this.setAttribute(`instanceColorStart`,new g(n,3,0)),this.setAttribute(`instanceColorEnd`,new g(n,3,3)),this}fromWireframeGeometry(e){return this.setPositions(e.attributes.position.array),this}fromEdgesGeometry(e){return this.setPositions(e.attributes.position.array),this}fromMesh(e){return this.fromWireframeGeometry(new d(e.geometry)),this}fromLineSegments(e){let t=e.geometry;return this.setPositions(t.attributes.position.array),this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new i);let e=this.attributes.instanceStart,t=this.attributes.instanceEnd;e!==void 0&&t!==void 0&&(this.boundingBox.setFromBufferAttribute(e),v.setFromBufferAttribute(t),this.boundingBox.union(v))}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new r),this.boundingBox===null&&this.computeBoundingBox();let e=this.attributes.instanceStart,t=this.attributes.instanceEnd;if(e!==void 0&&t!==void 0){let n=this.boundingSphere.center;this.boundingBox.getCenter(n);let r=0;for(let i=0,a=e.count;i<a;i++)y.fromBufferAttribute(e,i),r=Math.max(r,n.distanceToSquared(y)),y.fromBufferAttribute(t,i),r=Math.max(r,n.distanceToSquared(y));this.boundingSphere.radius=Math.sqrt(r),isNaN(this.boundingSphere.radius)&&console.error(`THREE.LineSegmentsGeometry.computeBoundingSphere(): Computed radius is NaN. The instanced position data is likely to have NaN values.`,this)}}toJSON(){}};l.line={worldUnits:{value:1},linewidth:{value:1},resolution:{value:new a},dashOffset:{value:0},dashScale:{value:1},dashSize:{value:1},gapSize:{value:1}},f.line={uniforms:e.merge([l.common,l.fog,l.line]),vertexShader:`
		#include <common>
		#include <color_pars_vertex>
		#include <fog_pars_vertex>
		#include <logdepthbuf_pars_vertex>
		#include <clipping_planes_pars_vertex>

		uniform float linewidth;
		uniform vec2 resolution;

		attribute vec3 instanceStart;
		attribute vec3 instanceEnd;

		attribute vec3 instanceColorStart;
		attribute vec3 instanceColorEnd;

		#ifdef WORLD_UNITS

			varying vec4 worldPos;
			varying vec3 worldStart;
			varying vec3 worldEnd;

			#ifdef USE_DASH

				varying vec2 vUv;

			#endif

		#else

			varying vec2 vUv;

		#endif

		#ifdef USE_DASH

			uniform float dashScale;
			attribute float instanceDistanceStart;
			attribute float instanceDistanceEnd;
			varying float vLineDistance;

		#endif

		float trimSegmentAlpha( const in vec4 start, const in vec4 end ) {

			// compute the interpolation factor needed to trim the segment so it terminates
			// between the camera plane and the near plane

			// conservative estimate of the near plane
			float a = projectionMatrix[ 2 ][ 2 ]; // 3nd entry in 3th column
			float b = projectionMatrix[ 3 ][ 2 ]; // 3nd entry in 4th column

			// we need different nearEstimate formula for reversed and default depth buffer
			// a is positive with a reversed depth buffer so it can be used for controlling the code flow
			float nearEstimate = ( a > 0.0 ) ? ( - b / ( a + 1.0 ) ) : ( - 0.5 * b / a );

			return ( nearEstimate - start.z ) / ( end.z - start.z );

		}

		void main() {

			#ifdef USE_COLOR

				vColor.xyz = ( position.y < 0.5 ) ? instanceColorStart : instanceColorEnd;

			#endif

			float aspect = resolution.x / resolution.y;

			// camera space
			vec4 start = modelViewMatrix * vec4( instanceStart, 1.0 );
			vec4 end = modelViewMatrix * vec4( instanceEnd, 1.0 );

			#ifdef USE_DASH

				float lineDistanceStart = dashScale * instanceDistanceStart;
				float lineDistanceEnd = dashScale * instanceDistanceEnd;

			#endif

			#ifdef WORLD_UNITS

				worldStart = start.xyz;
				worldEnd = end.xyz;

			#else

				vUv = uv;

			#endif

			// special case for perspective projection, and segments that terminate either in, or behind, the camera plane
			// clearly the gpu firmware has a way of addressing this issue when projecting into ndc space
			// but we need to perform ndc-space calculations in the shader, so we must address this issue directly
			// perhaps there is a more elegant solution -- WestLangley

			bool perspective = ( projectionMatrix[ 2 ][ 3 ] == - 1.0 ); // 4th entry in the 3rd column

			if ( perspective ) {

				if ( start.z < 0.0 && end.z >= 0.0 ) {

					float alpha = trimSegmentAlpha( start, end );
					end.xyz = mix( start.xyz, end.xyz, alpha );

					#ifdef USE_DASH

						lineDistanceEnd = mix( lineDistanceStart, lineDistanceEnd, alpha );

					#endif

				} else if ( end.z < 0.0 && start.z >= 0.0 ) {

					float alpha = trimSegmentAlpha( end, start );
					start.xyz = mix( end.xyz, start.xyz, alpha );

					#ifdef USE_DASH

						lineDistanceStart = mix( lineDistanceEnd, lineDistanceStart, alpha );

					#endif

				}

			}

			#ifdef USE_DASH

				vLineDistance = ( position.y < 0.5 ) ? lineDistanceStart : lineDistanceEnd;
				vUv = uv;

			#endif

			// clip space
			vec4 clipStart = projectionMatrix * start;
			vec4 clipEnd = projectionMatrix * end;

			// ndc space
			vec3 ndcStart = clipStart.xyz / clipStart.w;
			vec3 ndcEnd = clipEnd.xyz / clipEnd.w;

			// direction
			vec2 dir = ndcEnd.xy - ndcStart.xy;

			// account for clip-space aspect ratio
			dir.x *= aspect;
			dir = normalize( dir );

			#ifdef WORLD_UNITS

				vec3 worldDir = normalize( end.xyz - start.xyz );
				vec3 tmpFwd = normalize( mix( start.xyz, end.xyz, 0.5 ) );
				vec3 worldUp = normalize( cross( worldDir, tmpFwd ) );
				vec3 worldFwd = cross( worldDir, worldUp );
				worldPos = position.y < 0.5 ? start: end;

				// height offset
				float hw = linewidth * 0.5;
				worldPos.xyz += position.x < 0.0 ? hw * worldUp : - hw * worldUp;

				// don't extend the line if we're rendering dashes because we
				// won't be rendering the endcaps
				#ifndef USE_DASH

					// cap extension
					worldPos.xyz += position.y < 0.5 ? - hw * worldDir : hw * worldDir;

					// add width to the box
					worldPos.xyz += worldFwd * hw;

					// endcaps
					if ( position.y > 1.0 || position.y < 0.0 ) {

						worldPos.xyz -= worldFwd * 2.0 * hw;

					}

				#endif

				// project the worldpos
				vec4 clip = projectionMatrix * worldPos;

				// shift the depth of the projected points so the line
				// segments overlap neatly
				vec3 clipPose = ( position.y < 0.5 ) ? ndcStart : ndcEnd;
				clip.z = clipPose.z * clip.w;

			#else

				vec2 offset = vec2( dir.y, - dir.x );
				// undo aspect ratio adjustment
				dir.x /= aspect;
				offset.x /= aspect;

				// sign flip
				if ( position.x < 0.0 ) offset *= - 1.0;

				// endcaps
				if ( position.y < 0.0 ) {

					offset += - dir;

				} else if ( position.y > 1.0 ) {

					offset += dir;

				}

				// adjust for linewidth
				offset *= linewidth;

				// adjust for clip-space to screen-space conversion // maybe resolution should be based on viewport ...
				offset /= resolution.y;

				// select end
				vec4 clip = ( position.y < 0.5 ) ? clipStart : clipEnd;

				// back to clip space
				offset *= clip.w;

				clip.xy += offset;

			#endif

			gl_Position = clip;

			vec4 mvPosition = ( position.y < 0.5 ) ? start : end; // this is an approximation

			#include <logdepthbuf_vertex>
			#include <clipping_planes_vertex>
			#include <fog_vertex>

		}
		`,fragmentShader:`
		uniform vec3 diffuse;
		uniform float opacity;
		uniform float linewidth;

		#ifdef USE_DASH

			uniform float dashOffset;
			uniform float dashSize;
			uniform float gapSize;

		#endif

		varying float vLineDistance;

		#ifdef WORLD_UNITS

			varying vec4 worldPos;
			varying vec3 worldStart;
			varying vec3 worldEnd;

			#ifdef USE_DASH

				varying vec2 vUv;

			#endif

		#else

			varying vec2 vUv;

		#endif

		#include <common>
		#include <color_pars_fragment>
		#include <fog_pars_fragment>
		#include <logdepthbuf_pars_fragment>
		#include <clipping_planes_pars_fragment>

		vec2 closestLineToLine(vec3 p1, vec3 p2, vec3 p3, vec3 p4) {

			float mua;
			float mub;

			vec3 p13 = p1 - p3;
			vec3 p43 = p4 - p3;

			vec3 p21 = p2 - p1;

			float d1343 = dot( p13, p43 );
			float d4321 = dot( p43, p21 );
			float d1321 = dot( p13, p21 );
			float d4343 = dot( p43, p43 );
			float d2121 = dot( p21, p21 );

			float denom = d2121 * d4343 - d4321 * d4321;

			float numer = d1343 * d4321 - d1321 * d4343;

			mua = numer / denom;
			mua = clamp( mua, 0.0, 1.0 );
			mub = ( d1343 + d4321 * ( mua ) ) / d4343;
			mub = clamp( mub, 0.0, 1.0 );

			return vec2( mua, mub );

		}

		void main() {

			float alpha = opacity;
			vec4 diffuseColor = vec4( diffuse, alpha );

			#include <clipping_planes_fragment>

			#ifdef USE_DASH

				if ( vUv.y < - 1.0 || vUv.y > 1.0 ) discard; // discard endcaps

				if ( mod( vLineDistance + dashOffset, dashSize + gapSize ) > dashSize ) discard; // todo - FIX

			#endif

			#ifdef WORLD_UNITS

				// Find the closest points on the view ray and the line segment
				vec3 rayEnd = normalize( worldPos.xyz ) * 1e5;
				vec3 lineDir = worldEnd - worldStart;
				vec2 params = closestLineToLine( worldStart, worldEnd, vec3( 0.0, 0.0, 0.0 ), rayEnd );

				vec3 p1 = worldStart + lineDir * params.x;
				vec3 p2 = rayEnd * params.y;
				vec3 delta = p1 - p2;
				float len = length( delta );
				float norm = len / linewidth;

				#ifndef USE_DASH

					#ifdef USE_ALPHA_TO_COVERAGE

						float dnorm = fwidth( norm );
						alpha = 1.0 - smoothstep( 0.5 - dnorm, 0.5 + dnorm, norm );

					#else

						if ( norm > 0.5 ) {

							discard;

						}

					#endif

				#endif

			#else

				#ifdef USE_ALPHA_TO_COVERAGE

					// artifacts appear on some hardware if a derivative is taken within a conditional
					float a = vUv.x;
					float b = ( vUv.y > 0.0 ) ? vUv.y - 1.0 : vUv.y + 1.0;
					float len2 = a * a + b * b;
					float dlen = fwidth( len2 );

					if ( abs( vUv.y ) > 1.0 ) {

						alpha = 1.0 - smoothstep( 1.0 - dlen, 1.0 + dlen, len2 );

					}

				#else

					if ( abs( vUv.y ) > 1.0 ) {

						float a = vUv.x;
						float b = ( vUv.y > 0.0 ) ? vUv.y - 1.0 : vUv.y + 1.0;
						float len2 = a * a + b * b;

						if ( len2 > 1.0 ) discard;

					}

				#endif

			#endif

			#include <logdepthbuf_fragment>
			#include <color_fragment>

			gl_FragColor = vec4( diffuseColor.rgb, alpha );

			#include <tonemapping_fragment>
			#include <colorspace_fragment>
			#include <fog_fragment>
			#include <premultiplied_alpha_fragment>

		}
		`};var x=class extends n{constructor(t){super({type:`LineMaterial`,uniforms:e.clone(f.line.uniforms),vertexShader:f.line.vertexShader,fragmentShader:f.line.fragmentShader,clipping:!0}),this.isLineMaterial=!0,this.setValues(t)}get color(){return this.uniforms.diffuse.value}set color(e){this.uniforms.diffuse.value=e}get worldUnits(){return`WORLD_UNITS`in this.defines}set worldUnits(e){e===!0!==this.worldUnits&&(this.needsUpdate=!0),e===!0?this.defines.WORLD_UNITS=``:delete this.defines.WORLD_UNITS}get linewidth(){return this.uniforms.linewidth.value}set linewidth(e){this.uniforms.linewidth&&(this.uniforms.linewidth.value=e)}get dashed(){return`USE_DASH`in this.defines}set dashed(e){e===!0!==this.dashed&&(this.needsUpdate=!0),e===!0?this.defines.USE_DASH=``:delete this.defines.USE_DASH}get dashScale(){return this.uniforms.dashScale.value}set dashScale(e){this.uniforms.dashScale.value=e}get dashSize(){return this.uniforms.dashSize.value}set dashSize(e){this.uniforms.dashSize.value=e}get dashOffset(){return this.uniforms.dashOffset.value}set dashOffset(e){this.uniforms.dashOffset.value=e}get gapSize(){return this.uniforms.gapSize.value}set gapSize(e){this.uniforms.gapSize.value=e}get opacity(){return this.uniforms.opacity.value}set opacity(e){this.uniforms&&(this.uniforms.opacity.value=e)}get resolution(){return this.uniforms.resolution.value}set resolution(e){this.uniforms.resolution.value.copy(e)}get alphaToCoverage(){return`USE_ALPHA_TO_COVERAGE`in this.defines}set alphaToCoverage(e){this.defines&&(e===!0!==this.alphaToCoverage&&(this.needsUpdate=!0),e===!0?this.defines.USE_ALPHA_TO_COVERAGE=``:delete this.defines.USE_ALPHA_TO_COVERAGE)}},S=new u,C=new p,w=new p,T=new u,E=new u,D=new u,O=new p,k=new t,A=new h,j=new p,M=new i,N=new r,P=new u,F,I;function ee(e,t,n){return P.set(0,0,-t,1).applyMatrix4(e.projectionMatrix),P.multiplyScalar(1/P.w),P.x=I/n.width,P.y=I/n.height,P.applyMatrix4(e.projectionMatrixInverse),P.multiplyScalar(1/P.w),Math.abs(Math.max(P.x,P.y))}function te(e,t){let n=e.matrixWorld,r=e.geometry,i=r.attributes.instanceStart,a=r.attributes.instanceEnd,o=Math.min(r.instanceCount,i.count);for(let r=0,s=o;r<s;r++){A.start.fromBufferAttribute(i,r),A.end.fromBufferAttribute(a,r),A.applyMatrix4(n);let o=new p,s=new p;F.distanceSqToSegment(A.start,A.end,s,o),s.distanceTo(o)<I*.5&&t.push({point:s,pointOnLine:o,distance:F.origin.distanceTo(s),object:e,face:null,faceIndex:r,uv:null,uv1:null})}}function ne(e,t,n){let r=t.projectionMatrix,i=e.material.resolution,a=e.matrixWorld,o=e.geometry,s=o.attributes.instanceStart,l=o.attributes.instanceEnd,u=Math.min(o.instanceCount,s.count),d=-t.near;F.at(1,D),D.w=1,D.applyMatrix4(t.matrixWorldInverse),D.applyMatrix4(r),D.multiplyScalar(1/D.w),D.x*=i.x/2,D.y*=i.y/2,D.z=0,O.copy(D),k.multiplyMatrices(t.matrixWorldInverse,a);for(let t=0,o=u;t<o;t++){if(T.fromBufferAttribute(s,t),E.fromBufferAttribute(l,t),T.w=1,E.w=1,T.applyMatrix4(k),E.applyMatrix4(k),T.z>d&&E.z>d)continue;if(T.z>d){let e=T.z-E.z,t=(T.z-d)/e;T.lerp(E,t)}else if(E.z>d){let e=E.z-T.z,t=(E.z-d)/e;E.lerp(T,t)}T.applyMatrix4(r),E.applyMatrix4(r),T.multiplyScalar(1/T.w),E.multiplyScalar(1/E.w),T.x*=i.x/2,T.y*=i.y/2,E.x*=i.x/2,E.y*=i.y/2,A.start.copy(T),A.start.z=0,A.end.copy(E),A.end.z=0;let o=A.closestPointToPointParameter(O,!0);A.at(o,j);let u=c.lerp(T.z,E.z,o),f=u>=-1&&u<=1,m=O.distanceTo(j)<I*.5;if(f&&m){A.start.fromBufferAttribute(s,t),A.end.fromBufferAttribute(l,t),A.start.applyMatrix4(a),A.end.applyMatrix4(a);let r=new p,i=new p;F.distanceSqToSegment(A.start,A.end,i,r),n.push({point:i,pointOnLine:r,distance:F.origin.distanceTo(i),object:e,face:null,faceIndex:t,uv:null,uv1:null})}}}var re=class extends s{constructor(e=new b,t=new x({color:Math.random()*16777215})){super(e,t),this.isLineSegments2=!0,this.type=`LineSegments2`}computeLineDistances(){let e=this.geometry,t=e.attributes.instanceStart,n=e.attributes.instanceEnd,r=new Float32Array(2*t.count);for(let e=0,i=0,a=t.count;e<a;e++,i+=2)C.fromBufferAttribute(t,e),w.fromBufferAttribute(n,e),r[i]=i===0?0:r[i-1],r[i+1]=r[i]+C.distanceTo(w);let i=new _(r,2,1);return e.setAttribute(`instanceDistanceStart`,new g(i,1,0)),e.setAttribute(`instanceDistanceEnd`,new g(i,1,1)),this}raycast(e,t){let n=this.material.worldUnits,r=e.camera;if(r===null&&!n&&console.error(`LineSegments2: "Raycaster.camera" needs to be set in order to raycast against LineSegments2 while worldUnits is set to false.`),n===!1&&(this.material.resolution.x===0||this.material.resolution.y===0))return;let i=e.params.Line2===void 0?0:e.params.Line2.threshold||0;F=e.ray;let a=this.matrixWorld,o=this.geometry,s=this.material;I=s.linewidth+i,o.boundingSphere===null&&o.computeBoundingSphere(),N.copy(o.boundingSphere).applyMatrix4(a);let c;if(c=n?I*.5:ee(r,Math.max(r.near,N.distanceToPoint(F.origin)),s.resolution),N.radius+=c,F.intersectsSphere(N)===!1)return;o.boundingBox===null&&o.computeBoundingBox(),M.copy(o.boundingBox).applyMatrix4(a);let l;l=n?I*.5:ee(r,Math.max(r.near,M.distanceToPoint(F.origin)),s.resolution),M.expandByScalar(l),F.intersectsBox(M)!==!1&&(n?te(this,t):ne(this,r,t))}onBeforeRender(e){let t=this.material.uniforms;t&&t.resolution&&(e.getViewport(S),this.material.uniforms.resolution.value.set(S.z,S.w))}},L=class extends b{constructor(){super(),this.isLineGeometry=!0,this.type=`LineGeometry`}setPositions(e){let t=e.length-3,n=new Float32Array(2*t);for(let r=0;r<t;r+=3)n[2*r]=e[r],n[2*r+1]=e[r+1],n[2*r+2]=e[r+2],n[2*r+3]=e[r+3],n[2*r+4]=e[r+4],n[2*r+5]=e[r+5];return super.setPositions(n),this}setColors(e){let t=e.length-3,n=new Float32Array(2*t);for(let r=0;r<t;r+=3)n[2*r]=e[r],n[2*r+1]=e[r+1],n[2*r+2]=e[r+2],n[2*r+3]=e[r+3],n[2*r+4]=e[r+4],n[2*r+5]=e[r+5];return super.setColors(n),this}setFromPoints(e){let t=e.length-1,n=new Float32Array(6*t);for(let r=0;r<t;r++)n[6*r]=e[r].x,n[6*r+1]=e[r].y,n[6*r+2]=e[r].z||0,n[6*r+3]=e[r+1].x,n[6*r+4]=e[r+1].y,n[6*r+5]=e[r+1].z||0;return super.setPositions(n),this}fromLine(e){let t=e.geometry;return this.setPositions(t.attributes.position.array),this}},ie=class extends re{constructor(e=new L,t=new x({color:Math.random()*16777215})){super(e,t),this.isLine2=!0,this.type=`Line2`}},R=398600.4418,z=6378.137,B=.001082626683,V=72921159e-12,ae=360/365.2421897,H=2*Math.PI,U=Math.PI/180,W=86400,G=(e,t)=>e[0]*t[0]+e[1]*t[1]+e[2]*t[2],K=(e,t)=>[e[1]*t[2]-e[2]*t[1],e[2]*t[0]-e[0]*t[2],e[0]*t[1]-e[1]*t[0]],q=e=>Math.hypot(e[0],e[1],e[2]),J=e=>(e%H+H)%H;function Y(e,t){e=J(e);let n=t<.8?e:Math.PI;for(let r=0;r<50;r++){let r=(n-t*Math.sin(n)-e)/(1-t*Math.cos(n));if(n-=r,Math.abs(r)<1e-13)break}return n}function X(e,t){return 2*Math.atan2(Math.sqrt(1+t)*Math.sin(e/2),Math.sqrt(1-t)*Math.cos(e/2))}function Z(e,t){let n=2*Math.atan2(Math.sqrt(1-t)*Math.sin(e/2),Math.sqrt(1+t)*Math.cos(e/2));return J(n-t*Math.sin(n))}function Q(e,t,n,r=!0){let i=Math.sqrt(R/(e*e*e)),a=e*(1-t*t),o=r?B*(z/a)**2:0,s=Math.cos(n);return{n0:i,raan:-1.5*i*o*s,argp:.75*i*o*(5*s*s-1),n:i*(1+.75*o*Math.sqrt(1-t*t)*(3*s*s-1))}}function oe(e,t,n,r,i,a){let o=e*(1-t*t),s=o/(1+t*Math.cos(a)),c=[s*Math.cos(a),s*Math.sin(a),0],l=Math.sqrt(R/o),u=[-l*Math.sin(a),l*(t+Math.cos(a)),0],d=Math.cos(r),f=Math.sin(r),p=Math.cos(n),m=Math.sin(n),h=Math.cos(i),g=Math.sin(i),_=[[d*h-f*g*p,-d*g-f*h*p,f*m],[f*h+d*g*p,-f*g+d*h*p,-d*m],[g*m,h*m,p]],v=e=>[_[0][0]*e[0]+_[0][1]*e[1],_[1][0]*e[0]+_[1][1]*e[1],_[2][0]*e[0]+_[2][1]*e[1]];return{r:v(c),v:v(u)}}function se(e,t){let n=q(e),r=G(t,t),i=r/2-R/n;if(!(i<0))return null;let a=-398600.4418/(2*i),o=K(e,t),s=q(o);if(s<1e-9)return null;let c=Math.acos(Math.max(-1,Math.min(1,o[2]/s))),l=[-o[1],o[0],0],u=q(l),d=G(e,t),f=[0,1,2].map(i=>((r-R/n)*e[i]-d*t[i])/R),p=q(f),m=1e-9,h=[o[0]/s,o[1]/s,o[2]/s],g=(e,t)=>J(Math.atan2(G(K(e,t),h),G(e,t))),_=u>m?J(Math.atan2(l[1],l[0])):0,v=u>m?[l[0]/u,l[1]/u,0]:[1,0,0],y=p>m?g(v,f):0,b=g(p>m?f:v,e);return{a,e:p,i:c,raan:_,argp:y,m:Z(b,p),nu:b}}function $(e,t,n=!0){let r=Q(e.a,e.e,e.i,n),i=e.raan+r.raan*t,a=e.argp+r.argp*t,o=X(Y(e.m+r.n*t,e.e),e.e);return{...oe(e.a,e.e,e.i,i,a,o),raan:i,argp:a,nu:o}}function ce(e,t,n=0){let r=(Math.atan2(e[1],e[0])-n-V*t)/U;return r=((r+180)%360+360)%360-180,{lon:r,lat:Math.asin(e[2]/q(e))/U}}function le(e,t,n,r=0,i=0){let a=Math.min(e,t),o=Math.max(e,t),s=z+a,c=z+o;return{a:(s+c)/2,e:(c-s)/(c+s),i:n*U,raan:r*U,argp:i*U,m:0}}function ue(e,t=!0){let n=Q(e.a,e.e,e.i,t),r=e.a*(1-e.e),i=e.a*(1+e.e),a=H/n.n0,o=n.raan/U*W,s=H/(n.n+n.argp),c=(V-n.raan)*s/U;return{period:a,perigeeAlt:r-z,apogeeAlt:i-z,vPerigee:Math.sqrt(R*(2/r-1/e.a)),vApogee:Math.sqrt(R*(2/i-1/e.a)),raanDay:o,argpDay:n.argp/U*W,lapsPerDay:W/s,nodalPeriod:s,shiftPerLap:c,sso:t&&Math.abs(o-.9856473598947981)<.05,geosync:e.e<.01&&Math.abs(a-H/72921159e-12)<120,geostationary:e.e<.01&&Math.abs(a-H/72921159e-12)<120&&e.i<1*U}}function de(e){let t=e%360,n=t<0?t+360:t;return n>180?{deg:360-n,east:!0}:{deg:n,east:!1}}function fe(e,t,n,r=!0){let i=$(e,t,r),a=q(i.v),o=[i.v[0]*(1+n/a),i.v[1]*(1+n/a),i.v[2]*(1+n/a)];return se(i.r,o)}export{ie as _,V as a,le as c,$ as d,Q as f,X as g,ue as h,ae as i,Y as l,ce as m,R as n,fe as o,de as p,z as r,oe as s,B as t,Z as u,L as v,x as y};
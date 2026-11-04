var e=[`critical`,`high`,`medium`,`low`,`info`],t=`0.2.0`,n=(e,t=``,n=!1)=>new RegExp(e,(t.includes(`i`)?`i`:``)+(n?`gd`:``)),r=e=>Array.from(e).length;function i(e){let t=Array.from(e);if(!t.length)return 0;let n=new Map;for(let e of t)n.set(e,(n.get(e)??0)+1);let r=0;for(let e of n.values()){let n=e/t.length;r-=n*Math.log2(n)}return r}async function a(e){let t=await crypto.subtle.digest(`SHA-256`,new TextEncoder().encode(e));return Array.from(new Uint8Array(t)).map(e=>e.toString(16).padStart(2,`0`)).join(``).slice(0,12)}function o(e,t){let n=Array.from(e),r=Array.from(t);for(let e=0;e<Math.min(n.length,r.length);e++){let t=n[e].codePointAt(0)-r[e].codePointAt(0);if(t)return t}return n.length-r.length}var s=`ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/`;function c(e){let t=e.replace(/=+$/,``);if(e.length-t.length>2||/[-_]/.test(t)&&/[+/]/.test(t)||t.length%4==1)return null;t=t.replace(/-/g,`+`).replace(/_/g,`/`);let n=0,r=0,i=``;for(let e of t){let t=s.indexOf(e);if(t<0)return null;if(n=(n<<6|t)&16777215,r+=6,r>=8){r-=8;let e=n>>r&255;if(!(e>=32&&e<127||e===9||e===10||e===13))return null;i+=String.fromCharCode(e)}}return i}var l=class{rules;secret;fileCtx;join;files;config;placeholders;allow;ignored;constructor(e){this.rules=e,this.secret=e.secret_rules.map(e=>({r:e,g:n(e.regex,e.flags,!0),req:(e.require??[]).map(e=>n(e)),exc:e.exclude_regex?n(e.exclude_regex):null,next:e.next_line_regex?n(e.next_line_regex):null,same:e.same_line_regex?n(e.same_line_regex):null,ctx:e.context_regex?n(e.context_regex,`i`):null,kube:e.file_context_line_regex?n(e.file_context_line_regex):null})),this.fileCtx=e.secret_rules.filter(e=>e.decode&&e.file_context_regex).map(e=>n(e.file_context_regex)),this.join=n(e.join_regex,``,!0),this.files=e.file_rules.map(e=>({r:e,p:n(e.path_regex),e:e.except_regex?n(e.except_regex):null})),this.config=e.config_rules.map(e=>({r:e,p:n(e.path_regex),g:e.regex?n(e.regex,``,!0):null,all:(e.all??[]).map(e=>n(e)),none:(e.none??[]).map(e=>n(e)),ex:e.except_line_regex?n(e.except_line_regex):null})),this.placeholders=e.placeholders.map(e=>e.toLowerCase()),this.allow=e.allow_comment.toLowerCase(),this.ignored=new Set(e.limits.ignored_dirs)}isIgnored(e){return e.split(`/`).slice(0,-1).some(e=>this.ignored.has(e))}secretHits(e,t,n=!0,a=!1){let o=[];for(let s=1;s<=e.length;s++){let c=e[s-1];if(!c)continue;let l=c.toLowerCase().includes(this.allow),u=new Set;for(let d of this.secret)if(!d.r.decode||n)for(let n of c.matchAll(d.g)){let f=n[d.r.group];if(f===void 0)continue;let p=r(c.slice(0,n.indices[d.r.group][0]))+1;if(!u.has(p)){if(d.r.decode){let e=this.decodedSecret(d,f,c,a);if(e===null)continue;if(u.add(p),l){t.allow_comment++;continue}if(e===``){t.placeholder++;continue}o.push({r:d.r,line:s,col:p,value:e})}else u.add(p),l?t.allow_comment++:d.r.placeholder_check&&this.isPlaceholder(f)?t.placeholder++:i(f)<(d.r.entropy_min??0)?t.low_entropy++:!d.req.every(e=>e.test(f))||d.exc&&d.exc.test(f)||d.r.not_equal_group&&n[d.r.not_equal_group]===f||d.next&&!(d.same&&d.same.test(c)||s<e.length&&d.next.test(e[s]))?t.shape++:o.push({r:d.r,line:s,col:p,value:f})}}let d=n?[...c.matchAll(this.join)]:[];if(d.length&&!l){let e=``,t=0,n=[];for(let i of d)e+=c.slice(t,i.index),t=i.index+i[0].length,n.push([r(e),r(c.slice(0,t))-r(e)]);e+=c.slice(t);for(let t of this.secretHits([e],{placeholder:0,allow_comment:0,low_entropy:0,shape:0},!1)){let e=t.col-1+r(t.value);if(!n.some(([n])=>t.col-1<n&&n<e))continue;let i=Math.max(0,...n.filter(([e])=>t.col-1>=e).map(([,e])=>e)),a=t.col+i;o=o.filter(e=>e.line!==s||e.col!==a),o.push({r:t.r,line:s,col:a,value:t.value})}}}return o}isPlaceholder(e){let t=e.toLowerCase();return this.placeholders.some(e=>t.includes(e))}decodedSecret(e,t,n,a){let o=e.r;if(r(t)>(o.max_length??0)||i(t)<(o.entropy_min??0))return null;let s=c(t);if(s===null)return null;let l=this.secretHits(s.replace(/\r/g,``).split(`
`),{placeholder:0,allow_comment:0,low_entropy:0,shape:0},!1);if(l.length)return l[0].value;let u=s.trim();if(e.ctx&&e.ctx.test(n)||a&&e.kube&&e.kube.test(n)){if(this.isPlaceholder(u))return``;if(!u.includes(`
`)&&u.length>=(o.decoded_min_length??0)&&i(u)>=(o.decoded_entropy_min??0)&&e.req.every(e=>e.test(u)))return u}return null}async scanText(e,t,n){let i=[],o=t.split(`
`).map(e=>e.endsWith(`\r`)?e.slice(0,-1):e),s=this.fileCtx.some(e=>o.some(t=>e.test(t)));for(let t of this.secretHits(o,n,!0,s))i.push({rule:t.r.id,category:`secret`,severity:t.r.severity,path:e,line:t.line,column:t.col,fingerprint:await a(t.value),length:r(t.value)});for(let t of this.config)t.p.test(e)&&(t.r.kind===`line`?o.forEach((n,a)=>{if(!(t.ex&&t.ex.test(n)))for(let o of n.matchAll(t.g))i.push({rule:t.r.id,category:`config`,severity:t.r.severity,path:e,line:a+1,column:r(n.slice(0,o.index))+1})}):t.r.kind===`file-all`?t.all.every(e=>o.some(t=>e.test(t)))&&i.push({rule:t.r.id,category:`config`,severity:t.r.severity,path:e,line:o.findIndex(e=>t.all[0].test(e))+1,column:1}):o.some(e=>t.none.some(t=>t.test(e)))||i.push({rule:t.r.id,category:`config`,severity:t.r.severity,path:e,line:0,column:0}));return i}scanName(e){return this.files.filter(t=>t.p.test(e)&&!(t.e&&t.e.test(e))).map(t=>({rule:t.r.id,category:`file`,severity:t.r.severity,path:e,line:0,column:0}))}async scanFiles(n,r){let i={placeholder:0,allow_comment:0,low_entropy:0,shape:0},a={binary:0,too_large:0},s=this.rules.limits,c=new TextDecoder(`utf-8`),l=[],u=0,d=0;for await(let e of n)l=l.concat(this.scanName(e.path)),d++,(e.size??e.data.length)>s.max_file_bytes?(a.too_large++,r?.(d)):e.data.subarray(0,s.binary_probe_bytes).includes(0)?(a.binary++,r?.(d)):(u++,l=l.concat(await this.scanText(e.path,c.decode(e.data),i)),r?.(d));l.sort((e,t)=>o(e.path,t.path)||e.line-t.line||e.column-t.column||o(e.rule,t.rule));let f=Object.fromEntries(e.map(e=>[e,l.filter(t=>t.severity===e).length]));return{tool:`star-preflight`,version:t,rules_version:this.rules.version,scanned_files:u,skipped:a,suppressed:i,by_severity:f,findings:l,not_checked:this.rules.not_checked}}},u=e=>String(e??``).replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#39;`})[e]),d=3e4;function f(){let e=20261027,t=()=>(e=e*16807%2147483647)/2147483647,n=(e,n=`ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789`)=>Array.from({length:e},()=>n[Math.floor(t()*n.length)]).join(``),r=e=>new TextEncoder().encode(e);return[{path:`app/settings.py`,data:r(`DEBUG = False\nGITHUB_TOKEN = "ghp_${n(36)}"\nDATABASE_URL = "postgres://app:${n(18)}@db.internal:5432/app"\n`)},{path:`web/config.js`,data:r(`export const stripeKey = "sk_live_${n(24)}";\nexport const mapsKey = "AIza${n(35)}";\n`)},{path:`.env`,data:r(`SECRET_KEY=${n(32)}\n`)},{path:`.env.example`,data:r(`SECRET_KEY=
`)},{path:`docs/setup.md`,data:r("Set `API_KEY` to your-api-key-here before the first run.\n")},{path:`.github/workflows/ci.yml`,data:r(`on: [push]
jobs:
  b:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "\${{ github.event.head_commit.message }}"
`)},{path:`Dockerfile`,data:r(`FROM ubuntu:24.04
RUN curl -fsSL https://example.org/install.sh | sh
`)},{path:`requirements.txt`,data:r(`numpy
requests==2.32.3
`)}]}function p(t){let n=JSON.parse(t.dataset.t||`{}`),r=JSON.parse(`{\r
  "version": "0.2.0",\r
  "note": "One rule set, two engines: star_preflight (Python) and the browser engine of the S.T.A.R. Security Center (TypeScript) read this file and must report the same findings. Regular expressions use only syntax that Python re (ASCII mode) and JavaScript RegExp read the same way: no inline flags, no named groups, [ \\\\t] instead of \\\\s. Each rule is applied line by line; 'group' is the capture group holding the secret. When two secret rules match the same value at the same place, only the first rule in this list reports it (the specific rules come before the generic ones). A rule may also list 'require' (patterns the value must contain) and 'exclude_regex' (a value matching it is not a secret: paths and file names); values rejected this way are counted as 'shape'. Further options: 'next_line_regex'/'same_line_regex' (a match counts only if key material follows), 'not_equal_group' (a value equal to that group is not reported, e.g. password = user name), 'except_line_regex' for line rules (lines matching it are not reported). Since 0.2.0: a rule with 'decode': 'base64' reads its value as base64 and reports it only if the other rules find a secret in the decoded text, or, in a secret context ('context_regex' on the line, or a file matching 'file_context_regex' and a line matching 'file_context_line_regex'), if the decoded text is one line of at least 'decoded_min_length' characters with entropy at least 'decoded_entropy_min'; it claims a place only when it reports. 'join_regex': string literals joined on one line are also scanned joined, and a secret crossing a join is reported at its column on the line.",\r
  "limits": {\r
    "max_file_bytes": 2000000,\r
    "binary_probe_bytes": 8000,\r
    "ignored_dirs": [\r
      ".git",\r
      "node_modules",\r
      "vendor",\r
      "dist",\r
      "build",\r
      "__pycache__",\r
      ".venv",\r
      "venv",\r
      ".mypy_cache",\r
      ".pytest_cache",\r
      ".tox",\r
      ".next",\r
      "target"\r
    ]\r
  },\r
  "placeholders": [\r
    "example",\r
    "sample",\r
    "dummy",\r
    "placeholder",\r
    "changeme",\r
    "change_me",\r
    "your",\r
    "xxxx",\r
    "<",\r
    ">",\r
    "\${",\r
    "{{",\r
    "****",\r
    "redacted",\r
    "insert",\r
    "replace",\r
    "fake",\r
    "notreal",\r
    "not_real",\r
    "test_key",\r
    "testkey",\r
    "abcdefghij",\r
    "0123456789",\r
    "1234567890",\r
    "password",\r
    "{",\r
    "$",\r
    "%(",\r
    "123456789",\r
    "abc123",\r
    "sk-abc"\r
  ],\r
  "allow_comment": "star-preflight: allow",\r
  "secret_rules": [\r
    {\r
      "id": "private-key",\r
      "title": "Private key",\r
      "severity": "critical",\r
      "regex": "-----BEGIN ((RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY( BLOCK)?)-----",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 0,\r
      "placeholder_check": false,\r
      "next_line_regex": "^[ \\\\t\\"'\`]*[A-Za-z0-9+/=]{40,}",\r
      "same_line_regex": "\\\\\\\\n[A-Za-z0-9+/=]{40,}"\r
    },\r
    {\r
      "id": "aws-access-key-id",\r
      "title": "AWS access key ID",\r
      "severity": "high",\r
      "regex": "\\\\b((AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA)[0-9A-Z]{16})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "aws-secret-access-key",\r
      "title": "AWS secret access key",\r
      "severity": "critical",\r
      "regex": "aws_?(secret)?_?(access)?_?key[\\"']?[ \\\\t]*[:=][ \\\\t]*[\\"']?([A-Za-z0-9/+=]{40})(?![A-Za-z0-9/+=])",\r
      "group": 3,\r
      "flags": "i",\r
      "entropy_min": 4.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "github-token",\r
      "title": "GitHub token",\r
      "severity": "high",\r
      "regex": "\\\\b(gh[pousr]_[A-Za-z0-9]{36})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "github-fine-grained-token",\r
      "title": "GitHub fine-grained token",\r
      "severity": "high",\r
      "regex": "\\\\b(github_pat_[A-Za-z0-9_]{82})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "gitlab-token",\r
      "title": "GitLab personal access token",\r
      "severity": "high",\r
      "regex": "\\\\b(glpat-[A-Za-z0-9_-]{20})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "slack-token",\r
      "title": "Slack token",\r
      "severity": "high",\r
      "regex": "\\\\b(xox[baprs]-[A-Za-z0-9-]{10,72})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "slack-webhook",\r
      "title": "Slack incoming webhook",\r
      "severity": "medium",\r
      "regex": "(https://hooks\\\\.slack\\\\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]{20,})",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "stripe-live-key",\r
      "title": "Stripe live secret key",\r
      "severity": "critical",\r
      "regex": "\\\\b((sk|rk)_live_[A-Za-z0-9]{20,99})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "stripe-test-key",\r
      "title": "Stripe test secret key",\r
      "severity": "low",\r
      "regex": "\\\\b((sk|rk)_test_[A-Za-z0-9]{20,99})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "google-api-key",\r
      "title": "Google API key",\r
      "severity": "high",\r
      "regex": "\\\\b(AIza[0-9A-Za-z_-]{35})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "openai-key",\r
      "title": "OpenAI API key",\r
      "severity": "high",\r
      "regex": "\\\\b(sk-(proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}T3BlbkFJ[A-Za-z0-9_-]{20,})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "openai-project-key",\r
      "title": "OpenAI project or service key",\r
      "severity": "high",\r
      "regex": "\\\\b(sk-(proj|svcacct|admin)-[A-Za-z0-9_-]{40,})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.5,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "anthropic-key",\r
      "title": "Anthropic API key",\r
      "severity": "high",\r
      "regex": "\\\\b(sk-ant-(api|admin)[0-9]{2}-[A-Za-z0-9_-]{80,})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "openrouter-key",\r
      "title": "OpenRouter API key",\r
      "severity": "high",\r
      "regex": "\\\\b(sk-or-v1-[a-f0-9]{64})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "groq-key",\r
      "title": "Groq API key",\r
      "severity": "high",\r
      "regex": "\\\\b(gsk_[A-Za-z0-9]{52})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "xai-key",\r
      "title": "xAI API key",\r
      "severity": "high",\r
      "regex": "\\\\b(xai-[A-Za-z0-9]{80})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "huggingface-token",\r
      "title": "Hugging Face token",\r
      "severity": "high",\r
      "regex": "\\\\b(hf_[A-Za-z0-9]{30,50})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true,\r
      "require": [\r
        "[A-Z]",\r
        "[a-z]"\r
      ]\r
    },\r
    {\r
      "id": "twilio-api-key",\r
      "title": "Twilio API key",\r
      "severity": "high",\r
      "regex": "\\\\b(SK[0-9a-f]{32})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "twilio-account-sid",\r
      "title": "Twilio account SID",\r
      "severity": "medium",\r
      "regex": "\\\\b(AC[0-9a-f]{32})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "twilio-auth-token",\r
      "title": "Twilio auth token",\r
      "severity": "high",\r
      "regex": "(twilio[A-Za-z0-9_-]{0,24}|auth[_-]?token)[\\"']?[ \\\\t]*(:|=|:=|=>|,)[ \\\\t]*[\\"']?([a-f0-9]{32})(?![A-Za-z0-9])",\r
      "group": 3,\r
      "flags": "i",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "npm-token",\r
      "title": "npm access token",\r
      "severity": "high",\r
      "regex": "\\\\b(npm_[A-Za-z0-9]{36})\\\\b",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "pypi-token",\r
      "title": "PyPI upload token",\r
      "severity": "high",\r
      "regex": "\\\\b(pypi-AgEIcHlwaS5vcmc[A-Za-z0-9_-]{50,})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "sendgrid-key",\r
      "title": "SendGrid API key",\r
      "severity": "high",\r
      "regex": "\\\\b(SG\\\\.[A-Za-z0-9_-]{22}\\\\.[A-Za-z0-9_-]{43})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "telegram-bot-token",\r
      "title": "Telegram bot token",\r
      "severity": "medium",\r
      "regex": "\\\\b([0-9]{8,10}:AA[A-Za-z0-9_-]{33})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "azure-storage-key",\r
      "title": "Azure storage account key",\r
      "severity": "critical",\r
      "regex": "AccountKey=([A-Za-z0-9+/]{86}==)",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 4.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "jwt",\r
      "title": "JSON Web Token",\r
      "severity": "medium",\r
      "regex": "\\\\b(eyJ[A-Za-z0-9_-]{10,}\\\\.eyJ[A-Za-z0-9_-]{10,}\\\\.[A-Za-z0-9_-]{10,})(?![A-Za-z0-9_-])",\r
      "group": 1,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true\r
    },\r
    {\r
      "id": "url-credentials",\r
      "title": "Password inside a URL",\r
      "severity": "high",\r
      "regex": "\\\\b[a-z][a-z0-9+.-]{1,20}://([^ \\\\t:/@\\"']{1,64}):([^ \\\\t@/\\"']{6,})@[^ \\\\t/\\"']+",\r
      "group": 2,\r
      "flags": "i",\r
      "entropy_min": 2.5,\r
      "placeholder_check": true,\r
      "not_equal_group": 1\r
    },\r
    {\r
      "id": "bearer-token",\r
      "title": "Bearer token in an Authorization header",\r
      "severity": "high",\r
      "regex": "\\\\b(bearer)[ \\\\t]+([A-Za-z0-9._~+/-]{20,}=*)(?![A-Za-z0-9._~+/=-])",\r
      "group": 2,\r
      "flags": "i",\r
      "entropy_min": 3.5,\r
      "placeholder_check": true,\r
      "require": [\r
        "[0-9]",\r
        "[A-Za-z]"\r
      ],\r
      "exclude_regex": "^(https?://|\\\\.{0,2}/|/)|\\\\.(js|mjs|cjs|ts|tsx|json|py|md|html|css|txt|ya?ml|png|svg|jpe?g|gif|wasm|map|lock|toml|cfg|ini|sh)$"\r
    },\r
    {\r
      "id": "base64-encoded-secret",\r
      "title": "Secret encoded in base64",\r
      "severity": "high",\r
      "regex": "(^|[^A-Za-z0-9+/_.-])([A-Za-z0-9+/_-]{16,}={0,2})(?![A-Za-z0-9+/=_.-])",\r
      "group": 2,\r
      "flags": "",\r
      "entropy_min": 3.0,\r
      "placeholder_check": true,\r
      "decode": "base64",\r
      "max_length": 2048,\r
      "decoded_min_length": 8,\r
      "decoded_entropy_min": 3.0,\r
      "require": [\r
        "[0-9]",\r
        "[A-Za-z]"\r
      ],\r
      "context_regex": "(b64|base64)[A-Za-z0-9_.-]{0,20}[\\"']?[ \\\\t]*(:|=|:=|=>)",\r
      "file_context_regex": "^[ \\\\t]*kind:[ \\\\t]*[\\"']?Secret[\\"']?[ \\\\t]*$",\r
      "file_context_line_regex": "^[ \\\\t]+[A-Za-z0-9_.-]+:[ \\\\t]*[\\"']?[A-Za-z0-9+/_=-]+[\\"']?[ \\\\t]*$"\r
    },\r
    {\r
      "id": "generic-secret-assignment",\r
      "title": "Secret-looking value assigned to a secret-looking name",\r
      "severity": "medium",\r
      "regex": "(api[_-]?key|apikey|secret|token|passwd|password|pwd|access[_-]?key|private[_-]?key|client[_-]?secret|auth[_-]?key)[A-Za-z0-9_-]{0,20}[\\"']?[ \\\\t]*(:|=|:=|=>)[ \\\\t]*[\\"']([!#-&(-~]{12,})[\\"']",\r
      "group": 3,\r
      "flags": "i",\r
      "entropy_min": 3.5,\r
      "placeholder_check": true,\r
      "require": [\r
        "[0-9]",\r
        "[A-Za-z]"\r
      ],\r
      "exclude_regex": "^(https?://|\\\\.{0,2}/|/)|\\\\.(js|mjs|cjs|ts|tsx|json|py|md|html|css|txt|ya?ml|png|svg|jpe?g|gif|wasm|map|lock|toml|cfg|ini|sh)$"\r
    },\r
    {\r
      "id": "generic-secret-unquoted",\r
      "title": "Unquoted secret-looking value assigned to a secret-looking name (.env, YAML, INI)",\r
      "severity": "medium",\r
      "regex": "^[ \\\\t]*(export[ \\\\t]+)?[\\"']?[A-Za-z0-9_.-]*(api[_-]?key|apikey|secret|token|passwd|password|pwd|access[_-]?key|private[_-]?key|client[_-]?secret|auth[_-]?key)[A-Za-z0-9_.-]{0,20}[\\"']?[ \\\\t]*(:|=)[ \\\\t]*([A-Za-z0-9_+/=~-]{16,})[ \\\\t]*(#.*)?$",\r
      "group": 4,\r
      "flags": "i",\r
      "entropy_min": 3.5,\r
      "placeholder_check": true,\r
      "require": [\r
        "[0-9]",\r
        "[A-Za-z]"\r
      ],\r
      "exclude_regex": "^[a-z]+(_[a-z0-9]+)+$|^[A-Z]+(_[A-Z0-9]+)+$|^[a-z]+([A-Z][a-z0-9]+)+$"\r
    }\r
  ],\r
  "file_rules": [\r
    {\r
      "id": "env-file",\r
      "title": "Environment file with possible secrets",\r
      "severity": "high",\r
      "path_regex": "(^|/)\\\\.env(\\\\.[A-Za-z0-9_-]+)?$",\r
      "except_regex": "\\\\.(example|sample|template|dist|defaults)$",\r
      "advice": "Keep .env files out of the repository; commit a .env.example with placeholders instead."\r
    },\r
    {\r
      "id": "ssh-private-key-file",\r
      "title": "SSH private key file",\r
      "severity": "critical",\r
      "path_regex": "(^|/)id_(rsa|dsa|ecdsa|ed25519)$",\r
      "except_regex": "",\r
      "advice": "Remove the key from the repository and its history, and replace it: treat it as compromised."\r
    },\r
    {\r
      "id": "keystore-file",\r
      "title": "Key store or certificate bundle",\r
      "severity": "high",\r
      "path_regex": "\\\\.(p12|pfx|jks|keystore|kdbx)$",\r
      "except_regex": "",\r
      "advice": "Key stores and password databases do not belong in a repository."\r
    },\r
    {\r
      "id": "pem-or-key-file",\r
      "title": "PEM or key file",\r
      "severity": "medium",\r
      "path_regex": "\\\\.(pem|key)$",\r
      "except_regex": "",\r
      "advice": "If it holds a private key, remove it; a public certificate alone is not a secret."\r
    },\r
    {\r
      "id": "credential-config-file",\r
      "title": "Credential configuration file",\r
      "severity": "high",\r
      "path_regex": "(^|/)(\\\\.npmrc|\\\\.pypirc|\\\\.netrc|\\\\.git-credentials|\\\\.dockercfg|credentials|credentials\\\\.json|service[-_]account[^/]*\\\\.json)$",\r
      "except_regex": "",\r
      "advice": "These files usually hold tokens or passwords: keep them in the user's home directory or a secret manager."\r
    },\r
    {\r
      "id": "terraform-state",\r
      "title": "Terraform state file",\r
      "severity": "high",\r
      "path_regex": "\\\\.tfstate(\\\\.backup)?$",\r
      "except_regex": "",\r
      "advice": "State files can contain plaintext secrets; keep them in a protected backend."\r
    },\r
    {\r
      "id": "database-file",\r
      "title": "Database file in the repository",\r
      "severity": "low",\r
      "path_regex": "\\\\.(sqlite|sqlite3|db)$",\r
      "except_regex": "",\r
      "advice": "Check that it holds no personal or production data."\r
    }\r
  ],\r
  "config_rules": [\r
    {\r
      "id": "gha-pr-target-checkout",\r
      "title": "Workflow runs pull-request code with repository secrets",\r
      "severity": "high",\r
      "kind": "file-all",\r
      "path_regex": "(^|/)\\\\.github/workflows/[^/]+\\\\.ya?ml$",\r
      "all": [\r
        "^[^#]*pull_request_target",\r
        "^[^#]*actions/checkout",\r
        "^[^#]*github\\\\.event\\\\.pull_request\\\\.head\\\\.(sha|ref)"\r
      ],\r
      "advice": "With pull_request_target the workflow has write access and secrets; do not check out and run the contributor's code in it."\r
    },\r
    {\r
      "id": "gha-script-injection",\r
      "title": "Untrusted event text inside a shell step",\r
      "severity": "high",\r
      "kind": "line",\r
      "path_regex": "(^|/)\\\\.github/workflows/[^/]+\\\\.ya?ml$",\r
      "regex": "\\\\$\\\\{\\\\{[ \\\\t]*github\\\\.event\\\\.(issue\\\\.title|issue\\\\.body|pull_request\\\\.title|pull_request\\\\.body|comment\\\\.body|review\\\\.body|head_commit\\\\.message|pull_request\\\\.head\\\\.ref)[ \\\\t]*\\\\}\\\\}",\r
      "advice": "Pass event text through an environment variable instead of interpolating it into the script.",\r
      "except_line_regex": "^[ \\\\t]*(?!run:)[A-Za-z_][A-Za-z0-9_-]*:[ \\\\t]*[\\"']?\\\\$\\\\{\\\\{"\r
    },\r
    {\r
      "id": "gha-write-all",\r
      "title": "Workflow token with write access to everything",\r
      "severity": "medium",\r
      "kind": "line",\r
      "path_regex": "(^|/)\\\\.github/workflows/[^/]+\\\\.ya?ml$",\r
      "regex": "^[ \\\\t]*permissions:[ \\\\t]*write-all",\r
      "advice": "Grant only the permissions each job needs."\r
    },\r
    {\r
      "id": "gha-unpinned-action",\r
      "title": "Third-party action not pinned to a commit",\r
      "severity": "low",\r
      "kind": "line",\r
      "path_regex": "(^|/)\\\\.github/workflows/[^/]+\\\\.ya?ml$",\r
      "regex": "uses:[ \\\\t]*[\\"']?([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+)@(?![0-9a-f]{40}\\\\b)[^ \\\\t\\"'#]+",\r
      "advice": "Pin actions to a full commit SHA so that a moved tag cannot change what runs."\r
    },\r
    {\r
      "id": "pipe-to-shell",\r
      "title": "Script downloaded and run in one step",\r
      "severity": "medium",\r
      "kind": "line",\r
      "path_regex": "(^|/)(Dockerfile[^/]*|[^/]+\\\\.(sh|bash|ya?ml|ps1)|Makefile)$",\r
      "regex": "(curl|wget)[^|\\\\n]*\\\\|[ \\\\t]*(sudo[ \\\\t]+)?(sh|bash|zsh|python3?)\\\\b",\r
      "advice": "Download, check the hash or signature, then run."\r
    },\r
    {\r
      "id": "docker-root-user",\r
      "title": "Container image runs as root",\r
      "severity": "low",\r
      "kind": "file-none",\r
      "path_regex": "(^|/)Dockerfile[^/]*$",\r
      "none": [\r
        "^[ \\\\t]*USER[ \\\\t]+"\r
      ],\r
      "advice": "Add a USER line so that the container does not run as root."\r
    },\r
    {\r
      "id": "npm-install-script",\r
      "title": "Package runs a script when installed",\r
      "severity": "low",\r
      "kind": "line",\r
      "path_regex": "(^|/)package\\\\.json$",\r
      "regex": "\\"(preinstall|install|postinstall)\\"[ \\\\t]*:",\r
      "advice": "Install scripts run on every machine that installs the package; check what they do."\r
    },\r
    {\r
      "id": "python-unpinned-requirement",\r
      "title": "Python requirement without a fixed version",\r
      "severity": "info",\r
      "kind": "line",\r
      "path_regex": "(^|/)requirements[^/]*\\\\.txt$",\r
      "regex": "^[ \\\\t]*([A-Za-z0-9][A-Za-z0-9._-]*)[ \\\\t]*(\\\\[[^\\\\]]*\\\\])?[ \\\\t]*($|#|;|>=|>|<|~=|!=)",\r
      "advice": "Pin exact versions (==) or use a lock file for reproducible installs."\r
    }\r
  ],\r
  "not_checked": [\r
    "known vulnerabilities in dependencies (no vulnerability database is used offline)",\r
    "the Git history: secrets removed from the files but still in earlier commits",\r
    "binary files, archives inside the folder, and files larger than the size limit",\r
    "secrets in formats without a rule, however random: a value is reported only if a rule recognises its format or it is assigned to a secret-looking name",\r
    "whether a secret that was found is still valid (it is never sent anywhere to be tested)",\r
    "secret-looking assignments whose value has no digit or is only letters (the generic rule requires letters and digits, to avoid reporting words and identifiers)"\r
  ],\r
  "join_regex": "\\"[ \\\\t]*\\\\+[ \\\\t]*\\"|'[ \\\\t]*\\\\+[ \\\\t]*'"\r
}\r
`),i=new l(r),a=Object.fromEntries([...r.secret_rules,...r.file_rules,...r.config_rules].map(e=>[e.id,e])),o=JSON.parse(t.dataset.rules||`{}`);for(let[e,t]of Object.entries(o.rules||{}))a[e]&&(a[e]={...a[e],...t});let s=n.advice_secret;t.innerHTML=`<div class="sec-pick">
      <label class="btn primary sec-btn"><input type="file" class="sec-dir" webkitdirectory multiple hidden>${u(n.pick)}</label>
      <label class="btn sec-btn"><input type="file" class="sec-files" multiple hidden>${u(n.pick_files)}</label>
      <button type="button" class="btn sec-ex">${u(n.example)}</button></div>
    <p class="small muted sec-privacy">${u(n.privacy)}</p>
    <div class="sec-progress" hidden><div class="sec-bar"><i></i></div><p class="small mono sec-pn"></p></div>
    <div class="sec-out" aria-live="polite"></div>`;let c=t.querySelector(`.sec-out`),p=t.querySelector(`.sec-progress`),m=(r,i)=>{let l=e=>`<span class="sev sev-${e}">${u(n[`sev_${e}`]||e)}</span>`,d=e=>e.line?`${e.path}:${e.line}`:e.path,f=[...r.findings].sort((t,n)=>e.indexOf(t.severity)-e.indexOf(n.severity)).map(e=>`<tr><td>${l(e.severity)}</td><td><b>${u(a[e.rule]?.title||e.rule)}</b><div class="small muted">${u(e.category===`secret`?s:a[e.rule]?.advice||``)}</div></td>
        <td class="mono">${u(d(e))}</td><td class="mono small">${e.fingerprint?u(e.fingerprint):`—`}</td></tr>`).join(``),p=r.findings.length,m=e.find(e=>r.by_severity[e]>0);c.innerHTML=`<div class="sec-summary ${m?`worst-${m}`:`none`}"><p class="sec-head">${u(i)}</p>
        <p class="sec-big">${u(p?n.found.replace(`{n}`,String(p)):n.found_none)}</p>
        <p class="sec-counts">${e.map(e=>`${l(e)} ${r.by_severity[e]}`).join(` `)}</p>
        <p class="small muted">${u(n.read.replace(`{n}`,String(r.scanned_files)).replace(`{b}`,String(r.skipped.binary)).replace(`{l}`,String(r.skipped.too_large)))}
        ${u(n.suppressed.replace(`{p}`,String(r.suppressed.placeholder)).replace(`{e}`,String(r.suppressed.low_entropy)).replace(`{s}`,String(r.suppressed.shape)).replace(`{a}`,String(r.suppressed.allow_comment)))}</p>
        ${p?``:`<p class="small">${u(n.none_means)}</p>`}</div>
      ${p?`<div class="table-wrap"><table class="data sec-table"><thead><tr><th>${u(n.th_sev)}</th><th>${u(n.th_what)}</th><th>${u(n.th_where)}</th><th>${u(n.th_fp)}</th></tr></thead><tbody>${f}</tbody></table></div>`:``}
      <details class="sec-not"><summary>${u(n.not_checked)}</summary><ul>${(o.not_checked||r.not_checked).map(e=>`<li>${u(e)}</li>`).join(``)}</ul></details>
      <p><button type="button" class="btn small sec-dl">${u(n.download)}</button> <span class="small muted">${u(n.download_note)}</span></p>`,c.querySelector(`.sec-dl`).addEventListener(`click`,()=>{let e=new Blob([JSON.stringify(r,null,2)],{type:`application/json`}),t=document.createElement(`a`);t.href=URL.createObjectURL(e),t.download=`star-preflight-report.json`,document.body.appendChild(t),t.click(),t.remove(),setTimeout(()=>URL.revokeObjectURL(t.href),2e3)}),t.dataset.findings=String(p),t.dataset.worst=m||`none`},h=async(e,t)=>{let a=e=>e.includes(`/`)?e.slice(e.indexOf(`/`)+1):e,o=e.map(e=>({f:e,path:a(e.webkitRelativePath||e.name)})).filter(e=>!i.isIgnored(e.path)),s=e.length-o.length;if(o.length>d){c.innerHTML=`<p class="note">${u(n.too_many.replace(`{n}`,String(o.length)).replace(`{max}`,String(d)))}</p>`;return}p.hidden=!1,c.innerHTML=``;let l=p.querySelector(`.sec-bar i`),f=p.querySelector(`.sec-pn`);async function*h(){for(let e=0;e<o.length;e++){let{f:t,path:n}=o[e],i=t.size>r.limits.max_file_bytes;yield{path:n,size:t.size,data:i?new Uint8Array:new Uint8Array(await t.arrayBuffer())},e%40==0&&await new Promise(e=>setTimeout(e))}}let g=performance.now(),_=await i.scanFiles(h(),e=>{l.style.width=`${100*e/Math.max(1,o.length)}%`,f.textContent=n.progress.replace(`{n}`,String(e)).replace(`{t}`,String(o.length))});p.hidden=!0,m(_,t.replace(`{n}`,String(o.length)).replace(`{i}`,String(s)).replace(`{s}`,((performance.now()-g)/1e3).toFixed(1)))};t.querySelector(`.sec-dir`).addEventListener(`change`,e=>{let t=Array.from(e.target.files||[]);t.length&&h(t,n.label_folder)}),t.querySelector(`.sec-files`).addEventListener(`change`,e=>{let t=Array.from(e.target.files||[]);t.length&&h(t,n.label_folder)}),t.querySelector(`.sec-ex`).addEventListener(`click`,async()=>{m(await i.scanFiles(f()),n.label_example)}),t.dataset.ready=`1`}export{p as init};
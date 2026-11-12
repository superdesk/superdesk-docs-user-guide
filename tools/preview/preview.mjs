// Renders GitBook-flavoured markdown pages from the docs repo to a single
// self-contained HTML file for local review. GitBook block tags (stepper,
// step, hint, tabs) are turned into plain divs before marked runs; image
// paths are rewritten to absolute file:// URLs so the preview can live
// outside the repo.
import {marked} from 'marked';
import fs from 'node:fs';
import path from 'node:path';

const [repoRoot, outFile, ...pages] = process.argv.slice(2);
if (!repoRoot || !outFile || pages.length === 0) {
    console.error('usage: node preview.mjs <repo-root> <out.html> <page.md>...');
    process.exit(2);
}

function gitbookToHtml(md, pageDir) {
    return md
        .replace(/<!--[\s\S]*?-->/g, (c) => `<div class="note">${escapeHtml(c.slice(4, -3).trim())}</div>`)
        .replace(/\{%\s*hint\s+style="(\w+)"\s*%\}/g, '<div class="hint hint-$1">')
        .replace(/\{%\s*endhint\s*%\}/g, '</div>')
        .replace(/\{%\s*stepper\s*%\}/g, '<div class="stepper">')
        .replace(/\{%\s*endstepper\s*%\}/g, '</div>')
        .replace(/\{%\s*step\s*%\}/g, '<div class="step">')
        .replace(/\{%\s*endstep\s*%\}/g, '</div>')
        .replace(/\{%\s*tabs\s*%\}/g, '<div class="tabs">')
        .replace(/\{%\s*endtabs\s*%\}/g, '</div>')
        .replace(/\{%\s*tab\s+title="([^"]*)"\s*%\}/g, '<div class="tab"><div class="tab-title">$1</div>')
        .replace(/\{%\s*endtab\s*%\}/g, '</div>')
        .replace(/!\[([^\]]*)\]\(<?([^)>]+)>?\)/g, (m, alt, src) => `<img src="${src}" alt="${alt}">`)
        .replace(/src="([^"]+)"/g, (m, src) => {
            if (/^(https?:|data:|file:)/.test(src)) return m;
            const abs = path.resolve(pageDir, src);
            const exists = fs.existsSync(abs);
            return `src="file://${abs}" data-missing="${exists ? '' : '1'}"`;
        });
}

function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// marked treats a line starting with an HTML block as raw HTML until a blank
// line, so markdown inside our divs must be separated by blank lines. The
// GitBook pages already do that; the step headings ("### Title") follow a
// blank line after the opening tag.
marked.use({gfm: true, breaks: false});

const css = `
body{font-family:-apple-system,Inter,Segoe UI,Roboto,sans-serif;color:#1f2933;background:#fff;margin:0}
nav{position:sticky;top:0;background:#f6f8fa;border-bottom:1px solid #e1e4e8;padding:10px 24px;font-size:14px}
nav a{margin-right:18px;color:#0366d6;text-decoration:none}
main{max-width:860px;margin:0 auto;padding:24px 24px 80px}
article{border-top:4px solid #e1e4e8;margin-top:48px;padding-top:24px}
article:first-child{border-top:0;margin-top:0}
h1{font-size:32px;margin:.2em 0 .6em}h2{font-size:24px;margin:1.6em 0 .6em;padding-top:.4em;border-top:1px solid #eee}h3{font-size:18px;margin:1.3em 0 .5em}
p,li{line-height:1.6;font-size:16px}
code{background:#f3f4f6;padding:1px 5px;border-radius:4px;font-size:90%}
table{border-collapse:collapse;margin:1em 0;font-size:15px}th,td{border:1px solid #e1e4e8;padding:6px 10px;vertical-align:top;text-align:left}th{background:#f6f8fa}
figure{margin:1.4em 0;text-align:center}figure img{max-width:100%;height:auto;border-radius:8px;display:inline-block;cursor:zoom-in}
#lightbox{display:none;position:fixed;inset:0;background:rgba(15,23,42,.92);z-index:99;align-items:center;justify-content:center;cursor:zoom-out}#lightbox img{max-width:96vw;max-height:96vh;border-radius:8px}#lightbox.open{display:flex}figcaption{font-size:13px;color:#6b7280;margin-top:6px;text-align:center}
img[data-missing="1"]{min-height:60px;background:#fee;border:1px dashed #c00}
.hint{border-left:4px solid #3b82f6;background:#eff6ff;padding:10px 14px;border-radius:6px;margin:1em 0}
.hint-warning{border-color:#f59e0b;background:#fffbeb}.hint-danger{border-color:#ef4444;background:#fef2f2}.hint-success{border-color:#10b981;background:#ecfdf5}
.hint p{margin:.3em 0}
.stepper{border-left:2px solid #d1d5db;margin:1em 0 1.4em .6em;padding-left:22px;counter-reset:step}
.step{position:relative;margin:0 0 1.2em}.step h3{margin:.2em 0 .3em;font-size:17px}
.step::before{counter-increment:step;content:counter(step);position:absolute;left:-37px;top:0;width:26px;height:26px;border-radius:50%;background:#1f2933;color:#fff;font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:center}
.note{font-family:ui-monospace,Menlo,monospace;font-size:12px;background:#fff7ed;border:1px dashed #fb923c;padding:6px 10px;margin:1em 0;white-space:pre-wrap;color:#9a3412}
.tabs{border:1px solid #e1e4e8;border-radius:6px;padding:0 14px;margin:1em 0}.tab-title{font-weight:600;margin:12px 0 4px}
em.since{color:#6b7280}
`;

const sections = pages.map((rel) => {
    const abs = path.resolve(repoRoot, rel);
    const md = fs.readFileSync(abs, 'utf8');
    const html = marked.parse(gitbookToHtml(md, path.dirname(abs)));
    const id = rel.replace(/[^a-z0-9]+/gi, '-');
    const title = (md.match(/^# (.+)$/m) || [, rel])[1];
    return {id, title, rel, html};
});

const out = `<!doctype html><html><head><meta charset="utf-8"><title>User guide preview</title><style>${css}</style></head><body>
<nav>${sections.map((s) => `<a href="#${s.id}">${s.title}</a>`).join('')}<span style="float:right;color:#6b7280">local preview, not GitBook</span></nav>
<main>${sections.map((s) => `<article id="${s.id}"><div style="font-size:12px;color:#6b7280">${s.rel}</div>${s.html}</article>`).join('')}</main>
<div id="lightbox"><img alt=""></div>
<script>const lb=document.getElementById('lightbox');document.querySelectorAll('figure img').forEach(i=>i.addEventListener('click',()=>{lb.querySelector('img').src=i.src;lb.classList.add('open')}));lb.addEventListener('click',()=>lb.classList.remove('open'));document.addEventListener('keydown',e=>{if(e.key==='Escape')lb.classList.remove('open')});</script>
</body></html>`;
fs.writeFileSync(outFile, out);
console.log(`wrote ${outFile} (${sections.length} pages)`);

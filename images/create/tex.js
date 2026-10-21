// Converte expressões LaTeX em SVG com o MathJax (mesmos glifos dos slides).
// Uso: node tex.js '["\\varphi_D", "\\mathbf{x}_i"]'
// Saída: JSON { "expressão": "<svg ...>...</svg>", ... }

const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
const {AllPackages} = require('mathjax-full/js/input/tex/AllPackages.js');

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);

const doc = mathjax.document('', {
  InputJax: new TeX({packages: AllPackages}),
  OutputJax: new SVG({fontCache: 'none'})   // glifos embutidos: o SVG final não depende de fontes
});

const out = {};
for (const expr of JSON.parse(process.argv[2])) {
  out[expr] = adaptor.innerHTML(doc.convert(expr, {display: false}));
}
console.log(JSON.stringify(out));

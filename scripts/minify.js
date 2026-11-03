// uso: node minify.js entrada.html saida.html
const { minify } = require("html-minifier-terser");
const fs = require("fs");
(async () => {
  const src = fs.readFileSync(process.argv[2], "utf8");
  const out = await minify(src, {
    collapseWhitespace: true, conservativeCollapse: false, removeComments: true,
    minifyCSS: true, minifyJS: { compress: { passes: 1 }, mangle: { toplevel: false }, format: { ascii_only: false } },
    removeAttributeQuotes: false, keepClosingSlash: true, caseSensitive: true,
  });
  fs.writeFileSync(process.argv[3], out);
  console.log(process.argv[3], src.length, "->", out.length);
})().catch(e => { console.error(e); process.exit(1); });

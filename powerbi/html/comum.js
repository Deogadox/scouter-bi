/* Scouter BI — utilitários comuns a todas as páginas.
   Os dados chegam em window.D, montado pela medida DAX [JSON Dados]. */
(function () {
  var W = 1280, H = 720;

  function ajustar() {
    var app = document.getElementById("app");
    if (!app) return;
    var s = Math.min(window.innerWidth / W, window.innerHeight / H) || 1;
    app.style.transform = "scale(" + s + ")";
    app.style.left = Math.max(0, (window.innerWidth - W * s) / 2) + "px";
    app.style.top = Math.max(0, (window.innerHeight - H * s) / 2) + "px";
  }
  window.addEventListener("resize", ajustar);

  var D = window.D || { sagas: [], per: [], pod: [], tra: [], lut: [], meta: {} };

  // nomes da dublagem brasileira (a API usa nomes em espanhol/inglês)
  var APELIDO = {
    "Freezer": "Freeza", "Celula": "Cell", "Majin Buu": "Majin Boo", "Krillin": "Kuririn",
    "Android 16": "Androide 16", "Android 17": "Androide 17", "Android 18": "Androide 18",
    "Android 19": "Androide 19", "Android 20 (Dr. Gero)": "Dr. Gero", "Ginyu": "Capitão Ginyu"
  };

  var SAGA_CURTA = { 1: "Saiyajin", 2: "Namekusei", 3: "Ginyu", 4: "Freeza", 5: "Garlic Jr.", 6: "Trunks", 7: "Androides",
    8: "Cell Imperf.", 9: "Cell Perfeito", 10: "Jogos de Cell", 11: "G. Saiyaman", 12: "Torneio", 13: "Babidi", 14: "Majin Boo", 15: "Fusão", 16: "Kid Boo" };

  // golpes de assinatura (texto de ambientação para a arena e o dossiê)
  var GOLPES = {
    "Goku": [["Kamehameha", "Soco do Dragão", "Teletransporte Kamehameha"], "Genki Dama"],
    "Vegeta": [["Galick Ho", "Big Bang Attack", "Rajada Contínua"], "Final Flash"],
    "Gohan": [["Masenko", "Kamehameha", "Fúria de Gohan"], "Kamehameha Pai e Filho"],
    "Piccolo": [["Makankosappo", "Granada Infernal", "Raio dos Olhos"], "Makankosappo Máximo"],
    "Freezer": [["Raio da Morte", "Disco Mortal", "Onda de Choque"], "Bola da Morte"],
    "Celula": [["Kamehameha", "Raio Mortal", "Kienzan"], "Kamehameha Solar"],
    "Trunks": [["Burning Attack", "Golpe de Espada", "Masenko"], "Buster Cannon"],
    "Krillin": [["Kienzan", "Kamehameha", "Taiyoken"], "Kienzan Duplo"],
    "Tenshinhan": [["Kikoho", "Taiyoken", "Dodonpa"], "Shin Kikoho"],
    "Yamcha": [["Rouga Fuufuuken", "Soukidan", "Kamehameha"], "Soukidan Turbo"],
    "Chaos": [["Dodonpa", "Telecinese"], "Ataque Kamikaze"],
    "Raditz": [["Double Sunday", "Saturday Crush"], "Raio do Saiyajin"],
    "Nappa": [["Break Cannon", "Bomber DX"], "Explosão Gigante"],
    "Ginyu": [["Milky Cannon", "Pose Especial"], "Troca de Corpos"],
    "Recoome": [["Recoome Eraser Gun", "Recoome Kick"], "Ultra Fighting Bomber"],
    "Burter": [["Space Mach Attack", "Blue Hurricane"], "Tufão Azul"],
    "Jeice": [["Crusher Ball", "Rajada Vermelha"], "Crusher Ball Máxima"],
    "Guldo": [["Paralisia Temporal", "Ataque Mental"], "Congelar o Tempo"],
    "Zarbon": [["Elegant Blaster", "Monster Crush"], "Monster Crush Final"],
    "Dodoria": [["Dodoria Beam", "Investida"], "Raio da Boca"],
    "Nail": [["Rajada Namek", "Golpe Namek"], "Fúria Namekuseijin"],
    "Android 16": [["Rocket Punch", "Rajada de Ki"], "Hell's Flash"],
    "Android 17": [["Power Blitz", "Barreira de Energia"], "Super Explosão"],
    "Android 18": [["Destructo Disc", "Rajada Destrutiva"], "Power Blitz"],
    "Android 19": [["Raio Ocular", "Absorção de Energia"], "Absorção Total"],
    "Android 20 (Dr. Gero)": [["Raio Ocular", "Absorção de Energia"], "Absorção Total"],
    "Majin Buu": [["Raio de Chocolate", "Vapor Majin", "Kamehameha de Boo"], "Bomba Planetária"],
    "Gotenks": [["Ataque Kamikaze Fantasma", "Donut Galáctico", "Tiro Contínuo"], "Super Ataque Fantasma"],
    "Vegetto": [["Espada Espiritual", "Big Bang Kamehameha", "Rajada Final"], "Final Kamehameha"],
    "Mr. Satan": [["Soco Dinamite", "Chute Megaton"], "Golpe Secreto do Campeão"]
  };

  var U = {};
  U.D = D;
  U.ajustar = ajustar;
  U.clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };
  U.esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]; }); };
  U.nome = function (p) { return p ? (APELIDO[p.n] || p.n) : ""; };
  U.sagaCurta = function (o) { return SAGA_CURTA[o] || ("Saga " + o); };
  U.srcNome = function (s) { return s === "c" ? "canônico" : s === "g" ? "guia oficial" : "estimado"; };

  U.fmt = function (v) {
    if (v == null || isNaN(v)) return "–";
    var t = [[1e12, " tri"], [1e9, " bi"], [1e6, " mi"], [1e3, " mil"]];
    for (var i = 0; i < t.length; i++) {
      if (v >= t[i][0]) {
        var x = v / t[i][0];
        return x.toLocaleString("pt-BR", { maximumFractionDigits: x < 10 ? 1 : 0 }) + t[i][1];
      }
    }
    return Math.round(v).toLocaleString("pt-BR");
  };
  U.fmtFull = function (v) { return Math.round(v).toLocaleString("pt-BR"); };
  U.vezes = function (x) {
    if (x >= 1e6) return U.fmt(x).replace(" ", " ") + " de vezes";
    return "×" + (x >= 100 ? Math.round(x).toLocaleString("pt-BR") : x.toLocaleString("pt-BR", { maximumFractionDigits: 1 }));
  };

  // índices
  D.perById = {}; D.per.forEach(function (p) { D.perById[p.id] = p; });
  D.sagaByO = {}; D.sagas.forEach(function (s) { D.sagaByO[s.o] = s; });
  D.podByPer = {};
  D.pod.forEach(function (r) { (D.podByPer[r.p] = D.podByPer[r.p] || []).push(r); });
  D.per.forEach(function (p) {
    var rs = (D.podByPer[p.id] || []).sort(function (a, b) { return a.s - b.s || a.v - b.v; });
    p.pico = rs.reduce(function (m, r) { return r.v > m ? r.v : m; }, 0);
    p.sagas = rs.map(function (r) { return r.s; }).filter(function (s, i, a) { return a.indexOf(s) === i; });
  });
  D.traByPer = {};
  D.tra.forEach(function (t) { (D.traByPer[t.p] = D.traByPer[t.p] || []).push(t); });

  // ordem "de fama" para as grades
  var FAMA = ["Goku", "Vegeta", "Gohan", "Piccolo", "Trunks", "Krillin", "Freezer", "Celula", "Majin Buu", "Vegetto", "Gotenks",
    "Android 18", "Android 17", "Android 16", "Tenshinhan", "Yamcha", "Raditz", "Nappa", "Ginyu", "Zarbon", "Dodoria", "Recoome",
    "Burter", "Jeice", "Guldo", "Nail", "Android 19", "Android 20 (Dr. Gero)", "Chaos", "Mr. Satan"];
  D.perOrdem = D.per.slice().sort(function (a, b) {
    var ia = FAMA.indexOf(a.n), ib = FAMA.indexOf(b.n);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib) || a.n.localeCompare(b.n);
  });
  U.porNome = function (n) { for (var i = 0; i < D.per.length; i++) if (D.per[i].n === n) return D.per[i]; return null; };
  U.vilao = function (p) { return /Army of Frieza|Villain|Freelancer/.test(p.af || ""); };
  // a API mistura inglês (raça, afiliação) e espanhol (planeta): tradução só na tela
  var PT = {
    Saiyan: "Saiyajin", Human: "Humano", "Frieza Race": "Raça do Freeza", Namekian: "Namekuseijin", Android: "Androide",
    "Z Fighter": "Guerreiro Z", "Army of Frieza": "Exército do Freeza", Villain: "Vilão", Freelancer: "Mercenário", Other: "Outros",
    Tierra: "Terra", Namek: "Namekusei", "Freezer No. 79": "Planeta Freeza nº 79", Desconocido: "Desconhecido"
  };
  U.pt = function (v) { v = (v || "").trim(); return PT[v] || v; };

  U.golpes = function (p) { return GOLPES[p.n] || [["Rajada de Ki", "Golpe Físico", "Investida"], "Ataque Final"]; };

  // cor da aura pela forma
  U.aura = function (f) {
    f = (f || "").toLowerCase();
    if (f.indexOf("kaioken") >= 0) return "#ff3b3b";
    if (f.indexOf("ssj3") >= 0) return "#ffe45c";
    if (f.indexOf("ssj2") >= 0) return "#ffd23f";
    if (f.indexOf("ssj") >= 0) return "#ffc21a";
    if (f.indexOf("místico") >= 0) return "#f1edff";
    if (f.indexOf("boo") >= 0) return "#ff5cc8";
    if (f.indexOf("forma") >= 0) return "#b794f6";
    return "#7fb2ff";
  };

  // silhueta para quem não tem imagem na API (Nappa, Forças Ginyu, Chaos)
  var silN = 0;
  U.silhueta = function (cor, ini) {
    var id = "sg" + (++silN);
    return '<svg class="sil" viewBox="0 0 120 260" preserveAspectRatio="xMidYMax meet"><defs><linearGradient id="' + id + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="' + cor + '" stop-opacity=".85"/><stop offset="1" stop-color="#1b2440" stop-opacity=".95"/></linearGradient></defs>' +
      '<path fill="url(#' + id + ')" d="M60 14c13 0 22 10 22 23s-9 25-22 25-22-12-22-25 9-23 22-23zM40 66h40c16 0 28 10 30 26l6 52c1 8-12 11-15 3l-9-36-4 46 10 96c1 9-14 11-16 2l-15-78-15 78c-2 9-17 7-16-2l10-96-4-46-9 36c-3 8-16 5-15-3l6-52c2-16 14-26 30-26z"/>' +
      '<text x="60" y="44" text-anchor="middle" font-family="Bangers,Impact" font-size="20" fill="#0b1020" opacity=".75">' + U.esc(ini) + "</text></svg>";
  };
  U.iniciais = function (n) { return (n || "?").split(/[\s(]+/).filter(Boolean).slice(0, 2).map(function (x) { return x[0]; }).join("").toUpperCase(); };

  // retrato: imagem da API (ou da forma) com silhueta de reserva
  U.retrato = function (p, img, cor) {
    var src = img || (p && p.img) || "";
    var sil = U.silhueta(cor || U.aura(""), U.iniciais(U.nome(p)));
    if (!src) return sil;
    return '<img src="' + U.esc(src) + '" alt="" loading="lazy" referrerpolicy="no-referrer" ' +
      'onerror="this.outerHTML=this.getAttribute(&quot;data-sil&quot;)" data-sil="' + U.esc(sil) + '">';
  };

  // esfera do dragão com N estrelas
  var esfN = 0;
  var POS = {
    1: [[50, 52]], 2: [[39, 52], [61, 52]], 3: [[50, 38], [38, 60], [62, 60]], 4: [[39, 40], [61, 40], [39, 63], [61, 63]],
    5: [[50, 34], [35, 49], [65, 49], [41, 67], [59, 67]], 6: [[38, 36], [62, 36], [33, 54], [67, 54], [43, 70], [57, 70]],
    7: [[50, 30], [34, 42], [66, 42], [50, 51], [35, 63], [65, 63], [50, 73]]
  };
  function estrela(cx, cy, r) {
    var p = [];
    for (var i = 0; i < 10; i++) {
      var a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r;
      p.push((cx + rr * Math.cos(a)).toFixed(1) + "," + (cy + rr * Math.sin(a)).toFixed(1));
    }
    return '<polygon points="' + p.join(" ") + '" fill="#e8251d"/>';
  }
  U.esfera = function (n, tam) {
    var id = "eg" + (++esfN), r = n >= 6 ? 8 : n >= 4 ? 9.5 : 11;
    return '<svg viewBox="0 0 100 100" width="' + tam + '" height="' + tam + '"><defs><radialGradient id="' + id + '" cx="35%" cy="30%" r="75%">' +
      '<stop offset="0" stop-color="#fff6d0"/><stop offset=".22" stop-color="#ffd23f"/><stop offset=".7" stop-color="#ff8a00"/><stop offset="1" stop-color="#b84300"/></radialGradient></defs>' +
      '<circle cx="50" cy="50" r="46" fill="url(#' + id + ')"/>' + (POS[n] || []).map(function (q) { return estrela(q[0], q[1], r); }).join("") +
      '<ellipse cx="35" cy="27" rx="15" ry="8" fill="#fff" opacity=".5" transform="rotate(-28 35 27)"/></svg>';
  };

  U.marca = function (pagina) {
    return '<div class="brand"><span class="pg">' + U.esc(pagina) + "</span>" + U.esfera(4, 34) +
      '<div><div class="t">SCOUTER BI</div><div class="s">Dragon Ball Z em dados</div></div></div>';
  };

  // tooltip simples
  U.tip = function (app) {
    var t = document.createElement("div"); t.className = "tip"; app.appendChild(t);
    return {
      mostrar: function (html, x, y) { t.innerHTML = html; t.style.opacity = 1; var w = t.offsetWidth; t.style.left = Math.min(1280 - w - 8, x + 14) + "px"; t.style.top = (y + 14) + "px"; },
      esconder: function () { t.style.opacity = 0; }
    };
  };
  // posição do mouse em coordenadas do app (o app é escalado)
  U.pos = function (ev) {
    var app = document.getElementById("app"), r = app.getBoundingClientRect(), s = r.width / W;
    return { x: (ev.clientX - r.left) / s, y: (ev.clientY - r.top) / s };
  };

  U.contar = function (el, alvo, ms, fmt) {
    var t0 = performance.now(), de = 0;
    function passo(t) {
      var k = Math.min(1, (t - t0) / ms), e = 1 - Math.pow(1 - k, 3), v = de + (alvo - de) * e;
      el.textContent = fmt ? fmt(v) : Math.round(v);
      if (k < 1) requestAnimationFrame(passo);
    }
    requestAnimationFrame(passo);
  };

  window.U = U;
  setTimeout(ajustar, 0);
  ajustar();
})();

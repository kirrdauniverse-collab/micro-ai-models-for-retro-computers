#!/usr/bin/env node
/* docgen_v071.js — GLM Pico AI v0.7.1 dokumentációcsomag generátora
 * (docx-js, R1 borítórecept + DM-1 paletta a docx-skill szerint)
 * Futtatás:  node tools/docgen_v071.js   (a repó gyökeréből)
 */
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, PageNumber, NumberFormat, AlignmentType, HeadingLevel,
  WidthType, BorderStyle, ShadingType, TableOfContents, PageBreak,
  SectionType, TableLayoutType,
} = require("docx");
const fs = require("fs");
const path = require("path");

/* ---------- DM-1 (Deep Cyan — tech/AI) paletta a design-systemből ---------- */
const P = {
  bg: "162235", accent: "37DCF2",
  titleColor: "FFFFFF", subtitleColor: "B0B8C0",
  metaColor: "90989F", footerColor: "687078",
  primary: "0A1628",
  tbl: { headerBg: "1B6B7A", headerText: "FFFFFF", accentLine: "1B6B7A",
         innerLine: "C8DDE2", surface: "EDF3F5" },
};
const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB,
                       insideHorizontal: NB, insideVertical: NB };

/* ---------- általános építők ---------- */
function H1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160, line: 312 },
    children: [new TextRun({ text, bold: true, size: 32, color: P.primary,
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}
function H2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120, line: 312 },
    children: [new TextRun({ text, bold: true, size: 28, color: P.primary,
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}
function body(text, opts) {
  opts = opts || {};
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: 480 },
    spacing: { line: 312, after: opts.after || 80 },
    children: [new TextRun({ text, size: 24, color: "000000",
      font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
  });
}
/* kódsor (Z80 assembly / memóriakép) */
function code(text) {
  return new Paragraph({
    shading: { type: ShadingType.CLEAR, fill: P.tbl.surface },
    spacing: { line: 240, before: 0, after: 0 },
    indent: { left: 240, right: 240 },
    children: [new TextRun({ text: text.length ? text : " ",
      size: 16, color: "102A30",
      font: { ascii: "Courier New", eastAsia: "SimSun" } })],
  });
}
function codeBlock(lines) { return lines.map(code); }
/* kiemelt (fedő) sor oktatószöveggel */
function note(text) {
  return new Paragraph({
    spacing: { before: 120, after: 160, line: 312 },
    indent: { left: 240 },
    border: { left: { style: BorderStyle.SINGLE, size: 8,
                      color: P.accent, space: 10 } },
    children: [new TextRun({ text, size: 21, italics: true,
      color: "34505C", font: { ascii: "Times New Roman" } })],
  });
}
/* táblázat-cím + vízszintes táblázat (DM-1 tokenekkel) */
let tblNum = 0;
function tbl(title, header, rows, widths) {
  tblNum += 1;
  const out = [];
  out.push(new Paragraph({
    keepNext: true, spacing: { before: 200, after: 80 },
    children: [new TextRun({ text: tblNum + ". táblázat — " + title,
      bold: true, size: 21, color: "34505C",
      font: { ascii: "Times New Roman" } })],
  }));
  const mkCell = (text, isHead, w, alignLeft) => new TableCell({
    width: { size: w, type: WidthType.PERCENTAGE },
    shading: isHead ? { type: ShadingType.CLEAR, fill: P.tbl.headerBg }
                    : { type: ShadingType.CLEAR, fill: "FFFFFF" },
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    children: [new Paragraph({
      spacing: { line: 276 },
      children: [new TextRun({ text: String(text), bold: !!isHead,
        size: 20, color: isHead ? P.tbl.headerText : "000000",
        font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
    })],
  });
  out.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: P.tbl.accentLine },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: P.tbl.accentLine },
      left: NB, right: NB,
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1,
                          color: P.tbl.innerLine },
      insideVertical: NB,
    },
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true,
        children: header.map((h, i) => mkCell(h, true, widths[i])) }),
      ...rows.map(r => new TableRow({ cantSplit: true,
        children: r.map((v, i) => mkCell(v, false, widths[i])) })),
    ],
  }));
  return out;
}

/* ---------- borító: R1 recept (design-system.md) ---------- */
function splitTitleLines(title, charsPerLine) {
  if (title.length <= charsPerLine) return [title];
  const breakAfter = new Set([..."，。、；：！？", ..."的与和及之在于为",
                              ..."-_—–·/", ..." \t"]);
  const lines = []; let remaining = title;
  while (remaining.length > charsPerLine) {
    let breakAt = -1;
    for (let i = charsPerLine; i >= Math.floor(charsPerLine * 0.6); i--) {
      if (i < remaining.length && breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
    }
    if (breakAt === -1) breakAt = charsPerLine;
    lines.push(remaining.slice(0, breakAt).trim());
    remaining = remaining.slice(breakAt).trim();
  }
  if (remaining) lines.push(remaining);
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop(); lines[lines.length - 1] += last;
  }
  return lines;
}
function calcTitleLayout(title, maxWidthTwips, preferredPt, minPt) {
  preferredPt = preferredPt || 40; minPt = minPt || 24;
  const charsPerLine = (pt) => Math.floor(maxWidthTwips / (pt * 20));
  let titlePt = preferredPt, lines;
  while (titlePt >= minPt) {
    const cpl = charsPerLine(titlePt);
    if (cpl < 2) { titlePt -= 2; continue; }
    lines = splitTitleLines(title, cpl);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) {
    lines = splitTitleLines(title, charsPerLine(minPt)); titlePt = minPt;
  }
  return { titlePt, titleLines: lines };
}
function calcCoverSpacing(p) {
  const SAFETY = 1200;
  const usable = 16838 - SAFETY;
  const titleH = p.titleLineCount * (p.titlePt * 23 + 200);
  const subH = p.hasSubtitle ? (12 * 23 + 600) : 0;
  const engH = p.hasEnglishLabel ? (9 * 23 + 600) : 0;
  const metaH = p.metaLineCount * (10 * 23 + 100);
  const content = titleH + subH + engH + metaH + (p.fixedHeight || 800) + 900;
  const rem = Math.max(usable - content, 400);
  const FOOTER_MIN = 800;
  const rawTop = Math.floor(rem * 0.45), rawBottom = Math.floor(rem * 0.45);
  const bottomSpacing = Math.max(rawBottom, FOOTER_MIN);
  const topSpacing = Math.max(rawTop - Math.max(0, FOOTER_MIN - rawBottom), 400);
  return { topSpacing, bottomSpacing };
}
function buildCoverR1(config) {
  const padL = 1200, padR = 800;
  const availableWidth = 11906 - padL - padR - 300;
  const { titlePt, titleLines } = calcTitleLayout(config.title, availableWidth, 40, 24);
  const titleSize = titlePt * 2;
  const spacing = calcCoverSpacing({
    titleLineCount: titleLines.length, titlePt,
    hasSubtitle: !!config.subtitle, hasEnglishLabel: !!config.englishLabel,
    metaLineCount: (config.metaLines || []).length, fixedHeight: 400,
  });
  const accentLeft = { style: BorderStyle.SINGLE, size: 8,
                       color: P.accent, space: 12 };
  const children = [];
  children.push(new Paragraph({ spacing: { before: spacing.topSpacing } }));
  if (config.englishLabel) {
    children.push(new Paragraph({
      indent: { left: padL, right: padR }, spacing: { after: 500 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6,
                          color: P.accent, space: 8 } },
      children: [new TextRun({ text: config.englishLabel.split("").join("  "),
        size: 18, color: P.accent,
        font: { ascii: "Calibri", eastAsia: "SimHei" }, characterSpacing: 40 })],
    }));
  }
  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      indent: { left: padL },
      spacing: { after: i < titleLines.length - 1 ? 100 : 300,
                 line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [new TextRun({ text: titleLines[i], size: titleSize,
        bold: true, color: P.titleColor,
        font: { eastAsia: "SimHei", ascii: "Arial" } })],
    }));
  }
  if (config.subtitle) {
    children.push(new Paragraph({
      indent: { left: padL }, spacing: { after: 800 },
      children: [new TextRun({ text: config.subtitle, size: 24,
        color: P.subtitleColor,
        font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }
  for (const line of (config.metaLines || [])) {
    children.push(new Paragraph({
      indent: { left: padL + 200 }, spacing: { after: 80 },
      border: { left: accentLeft },
      children: [new TextRun({ text: line, size: 24, color: P.metaColor,
        font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }
  children.push(new Paragraph({ spacing: { before: spacing.bottomSpacing } }));
  children.push(new Paragraph({
    indent: { left: padL, right: padR },
    border: { top: { style: BorderStyle.SINGLE, size: 2,
                     color: P.accent, space: 8 } },
    spacing: { before: 200 },
    children: [
      new TextRun({ text: config.footerLeft || "", size: 16,
        color: P.footerColor, font: { ascii: "Arial" } }),
      new TextRun({ text: "                                        " }),
      new TextRun({ text: config.footerRight || "", size: 16,
        color: P.footerColor, font: { ascii: "Arial" } }),
    ],
  }));
  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: P.bg },
        borders: noBorders, children,
      })],
    })],
  })];
}

/* ---------- lábléc oldalszámmal ---------- */
function pageFooter() {
  return new Footer({ children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ children: [PageNumber.CURRENT], size: 18,
      color: "687078" })],
  })] });
}
function docHeader() {
  return new Header({ children: [new Paragraph({
    alignment: AlignmentType.RIGHT,
    border: { bottom: { style: BorderStyle.SINGLE, size: 2,
                        color: P.tbl.innerLine, space: 4 } },
    children: [new TextRun({ text: "GLM Pico AI v0.7.1 — dokumentációcsomag",
      size: 16, color: "687078", font: { ascii: "Arial" } })],
  })] });
}

/* ---------- tartalom ---------- */
const bodyChildren = [];
const add = (...els) => els.forEach(e => Array.isArray(e)
  ? bodyChildren.push(...e) : bodyChildren.push(e));

/* 1. Áttekintés */
add(H1("1. Áttekintés"));
add(body("A GLM Pico AI egy 1982-es Sinclair ZX81 (16 KiB RAM) mikro-számítógépre készült, teljesen önállóan, gépi kódban futó társalgóprogram: a felhasználó mondatait beolvasva, saját szótára és kazettán hordozott tudáscsomagjai alapján állít elő válaszokat. A rendszer a klasszikus gép minden erőforrását kihasználja: a program Z80 assembly-ben írt motorja körülbelül 7,3 KiB-ot foglal el, a fennmaradó memóriában szótár, tudáscsomagok, tartós állapot és a beszélgetés gyűrűje él. A GLM jelölés a projektet azonosítja; a jelen dokumentációcsomag a v0.7.1-es kiadáshoz tartozik."));
add(body("A csomag célja, hogy a program használata, belső felépítése, forráskódja és változás-története egy helyen, ellenőrizhető módon legyen dokumentálva. A kiadás a korábbi hibakeresési menetek tapasztalatait is rögzíti: a v0.7.0 a kazettafájl formátumát, a v0.7.1 a betöltés utáni indítási láncot javította — mindkettő részletes leírása a 6. fejezetben található."));
add(...tbl("A kézbesített fájlok (v0.7.1)",
  ["Fájlnév", "Tartalom"],
  [["GLM_PicoAI_v0.7.1_kazetta.T81", "A ZX81-es kazetta (4 blokk: PICOBOOT, PICOBASE, PICOASTR, PICOSCIN) — ezt töltse be az emulátorba"],
   ["GLM_PicoAI_v0.7.1_dokumentacio.docx", "Jelen dokumentáció (működés, felépítés, források, tudáscsomagok, változatok)"],
   ["GLM_PicoAI_v0.7.1_forraskod_csomag.zip", "Teljes forráskód: Z80 assembly motor, Python-eszközök, tudás-források, tervezési dokumentumok és a kazetta másolata"]],
  [42, 58]));
add(body("Az elnevezés rendszere a továbbiakban is egységes: minden átadott fájl neve a GLM megjelöléssel kezdődik, ezt a termék neve (Pico AI), a verziószám (pl. v0.7.1) és a fájl szerepe követi. A kazetta belsejében lévő blokknevek (PICOBOOT, PICOBASE, PICOASTR, PICOSCIN) a betöltési eljárás miatt változatlanok maradnak — a ZX81 BASIC LOAD parancsa ezekre a nevekre hivatkozik."));

/* 2. Betöltés és üzemeltetés */
add(H1("2. Betöltés és üzemeltetés"));
add(H2("2.1 Előfeltételek"));
add(body("A kazetta a Sinclair ZX81 16 KiB memóriakonfigurációját igényli. Emulátorban a beállítás: Hardware — ZX81, RAM — 16K. A tesztekhez az EightyOne emulátort használtuk (a kazetta az emulátor T81-formátumát követi), de a szalag bármely ZX81-emulátorban vagy — megfelelő átvitel után — valódi gépen is betölthető."));
add(H2("2.2 A betöltés lépései"));
add(body("Első lépésként a kazettafájlt szalagként kell beszúrni az emulátorba (EightyOne: Media, majd Tape, Insert). Ezután a gépnek a következő parancsokat adjuk ki, pontosan ebben a sorrendben:"));
add(...codeBlock([
  "LOAD \"PICOBOOT\"      <ENTER>   (a boot-blokk betöltése; a g\u00E9p maga",
  "                                futtatja le a programot)",
  "  ...a bemutat\u00F3 sz\u00F6veg megjelenik, v\u00E1rja az ENTER-t...",
  "<ENTER>                          (a boot folytat\u00E1sa)",
  "  ...a k\u00E9perny\u0151 t\u00F6rli mag\u00E1t, a g\u00E9p k\u00E9sz a bet\u00F6lt\u00E9sre...",
  "LOAD \"\"              <ENTER>   (a k\u00F6vetkez\u0151 blokk, a PICOBASE",
  "                                bet\u00F6lt\u00E9se a szalagr\u00F3l)",
]));
add(body("A második betöltés végén a gép automatikusan elindítja a társalgó-motort: első futásnál a gép bemutatkozik (FIRST RUN. LETS SET YOU UP.), majd néhány kérdést tesz fel a felhasználóról — például az évszámot (YEAR?) kérdezi —, és ezekből állítja össze a profilját. Ezután megjelenik a beszélgető-felület, és a gép készen áll a társalgásra: a mondatokat a szokásos módon, ENTER-rel zárva írhatjuk be."));
add(body("Két kiegészítő parancs érdemel említést. A /save begépelésére a motor a beszélgetés állapotát és a megtanult adatokat visszamenti a kazettára: a PICOBASE blokk felülíródik, így a következő indításnál a gép emlékszik ránk. A téma-váltás a motor menüjéből indítható: ilyenkor a következő tudáscsomag-blokk (PICOASTR vagy PICOSCIN) töltődik be a szalagról, ugyanazzal az automatikus újraindítással."));
add(H2("2.3 A képernyő felépítése"));
add(...tbl("A beszélgető-felület képernyő-sávjai",
  ["Sáv", "Tartalom"],
  [["0–2. sor", "a tartós állapot összecsomagolt megjelenítése (státusz)"],
   ["3. sor", "státuszsor (inverz): óra, fordulatszám,profil"],
   ["4–17. sor", "a társalgás konzolja: a beszélgetés görgetett szövege"],
   ["18. sor", "gondolkodás-sáv (inverz): a válasz-előállítás ideje alatt aktív"],
   ["19–21. sor", "beviteli sor, prompt és a gép tippje"]],
  [22, 78]));

/* 3. Rendszerfelépítés */
add(H1("3. Rendszerfelépítés és működés"));
add(H2("3.1 A kazetta blokkjai"));
add(body("A kazetta négy, névvel ellátott blokkot tartalmaz. A PICOBOOT a telepítőt hordozza: egy rövid BASIC-program, amely bemutatkozás után gépi kóddal előkészíti a felső memóriát, majd NEW-t hajt végre. A három további blokk (PICOBASE, PICOASTR, PICOSCIN) a motort és egy-egy tudáscsomagot tartalmazza rövidített képként: a betöltésük után a program önmagától elindul, és a csomagváltás is kazettáról, láncolt LOAD-dal történik."));
add(...tbl("A kazetta blokkjai (GLM_PicoAI_v0.7.1_kazetta.T81, 39 009 bájt)",
  ["Blokk", "Méret", "Szerep"],
  [["PICOBOOT", "1208 bájt", "bemutató + ML-telepítő (D_FILE, tartós zóna, RAMTOP) + NEW"],
   ["PICOBASE", "12 535 bájt", "motor + szótár + alaptudás (betöltés után automatikus indítás)"],
   ["PICOASTR", "12 535 bájt", "motor + szótár + csillagászati csomag"],
   ["PICOSCIN", "12 535 bájt", "motor + szótár + tudományos csomag"]],
  [22, 18, 60]));
add(H2("3.2 A memóriatérkép"));
add(...tbl("A 16 KiB memóriatérkép a motor működése közben",
  ["Címtartomány", "Tartalom"],
  [["0x4009–0x407C", "rendszer-változók (a ROM által használt terület)"],
   ["0x407D–0x4081", "a BASIC-program fejléce (1 REM sor eleje)"],
   ["0x4082–0x5D9F", "a társalgó-motor gépi kódja (kb. 7,3 KiB)"],
   ["0x5DA0–0x5DE7", "REM-farok: a /save által visszamentett 72 bájtos állapot"],
   ["0x5F00–0x68FF", "szótár: hash-index, zászlók, offsetek, szólista (2560 bájt)"],
   ["0x6900–0x70FF", "a betöltött tudáscsomag (PK01 formátum, max. 2 KiB)"],
   ["0x7100–0x715E", "ROM-munkaterület (E_LINE); a képek vége"],
   ["0x715F", "RAMTOP-határbájt (0xFF): a NEW-védelem megállítója"],
   ["0x7160–0x715F+72", "tartós állapot-zóna (XOR-védett, 72 bájt)"],
   ["0x71B0–0x742F", "tanult-zóna (640 bájt): a gép által megjegyzett szavak"],
   ["0x7430–0x7A5F", "a beszélgetés gyűrűje (kb. 1,6 KiB, görgetett)"],
   ["0x7B00–0x7E18", "képernyő (D_FILE): 24 sor × 32 oszlop + sorvégek"],
   ["0x7E19", "VARS zárójelző (0x80)"]],
  [26, 74]));
add(H2("3.3 A rendszerindítás láncolata"));
add(body("A PICOBOOT betöltése után a ZX81 ROM automatikusan lefuttatja a programot. A BASIC-sorok sorban: bemutató szövegek kiírása (2–5. sor), ENTER-várakozás INPUT-tal (6. sor), figyelmeztetés a következő lépésre (7–8. sor), majd a 9. sor a RAND USR 16514 utasítással meghívja a 0x4082 címen elhelyezett telepítőt. A telepítő — 54 bájt tiszta Z80 kód — elvégzi a felső memória előkészítését: üres képernyőfájlt ír a 0x7B00-ra, nullázza a tartós zónát, elhelyezi a VARS-zárójelzőt, és a RAMTOP rendszer-változót 0x715F-re állítja. A 10. sor ezután NEW-t hajt végre."));
add(body("A NEW parancs a ROM memóriájában újrarendez, és a magyarán kritikus pont a védelem: a NEW a RAMTOP alatti területet 0x02-vel tölti fel, a határvizsgálata pedig felfelé haladva az első nem 0x02 bájtnál áll meg. Mivel a telepítő a 0x715F címre 0xFF-et írt, a vizsgálat ott megáll — a NEW így csak a program területét törli, a képernyőfájlt, a tartós zónát és a beszélgetés-gyűrűt pedig érintetlenül hagyja. E trükk nélkül a NEW az egész 16 KiB-t felülírná, és a rendszer minden előkészítése elpusztulna (ez történt a v0.7.0 hibánál — lásd 6. fejezet)."));
add(body("A NEW után a felhasználó LOAD \"\" parancsára a szalag következő blokkja, a PICOBASE töltődik be. A betöltés végén a ROM ismét automatikusan futtatja a programot: az 1. sor REM-jében rejtezett motor kódja betöltésre kerül, a 2–3. sorok a téma-váltó és mentő láncolatot (IF USR 16514=1 THEN LOAD, IF USR 16514=2 THEN SAVE), a 4. sor pedig a RAND USR 16514 hívással átadja a vezérlést a motornak. A motor első dolga a SLOW mód biztosítása és a felület felrajzolása, majd — ha korábbi állapot nincs — a profil-bekérés, végül a társalgó-főciklus."));
add(note("A BASIC-sorok szerkezete bájtpontról megegyezik a régi, bizonyított v0.5.4-es kiadás blokkjaival (IF USR 16514=1 THEN LOAD sor, a szám-literálok 0x7E + 5 bájtos ZX lebegőpontos utótaggal) — az összevetést a 7. fejezetben ismertetett eszközök végezték el."));

/* 4. Z80 forrás */
add(H1("4. A Z80 gépi kód forrása"));
add(H2("4.1 A motor forrásfájljai"));
add(...tbl("A motor assembly-forrásai (engine/ mappa)",
  ["Fájl", "Méret", "Szerep"],
  [["main.z80", "29 189 bájt", "belépés, társalgó-főciklus, beviteli szerkesztő, LOAD/SAVE-lánc"],
   ["gen.z80", "25 544 bájt", "a válasz-előállító (mintázatok, mondat-összerakás)"],
   ["state.z80", "13 575 bájt", "tartós állapot: mentés/töltés XOR-védelemmel, esemény-öregedés"],
   ["token.z80", "11 314 bájt", "szöveg-tokenizálás, szótári keresés"],
   ["screen.z80", "6682 bájt", "képernyő-kezelés: konzol, státuszsor, görgetés"],
   ["keys.z80", "4412 bájt", "billentyűzet-olvasás, beviteli sor kezelése"],
   ["date.z80", "3634 bájt", "óra, dátum, évjárás-számítás a profilhoz"],
   ["tables.z80", "2942 bájt", "karakter- és kulcstáblák"],
   ["config.z80", "2468 bájt", "címkonstansok: memóriatérkép, ROM-rutinok"],
   ["bootinst.z80", "1683 bájt", "a PICOBOOT ML-telepítője (54 bájt binárisan)"]],
  [22, 16, 62]));
add(H2("4.2 Belépési pont és ROM-rutinok"));
add(body("A motor a 0x4082 címen (tízes számrendszerben 16514 — a BASIC USR hívásban ez a szám szerepel) egy ugróutasítással kezdődik, amely a tényleges belépési kódra ugrik. A belépéskor a motor saját vermet állít be a RAM tetején (0x7FFD), SLOW módot kér a ROM-tól, majd felrajzolja a felületet. A ROM-mal való együttműködés négy, a ROM-disassemblierből ellenőrzött címre épül:"));
add(...codeBlock([
  "ROM_CLS   EQU 0x0A2A    ; k\u00E9perny\u0151 t\u00F6rl\u00E9se",
  "ROM_SLOW  EQU 0x0F2B    ; SLOW m\u00F3d (k\u00E9perny\u0151 gener\u00E1l\u00E1s be)",
  "ROM_FAST  EQU 0x02E7    ; FAST m\u00F3d (k\u00E9perny\u0151 gener\u00E1l\u00E1s ki)",
  "ROM_KEYB  EQU 0x02BB    ; billenty\u0171zet-szken",
]));
add(body("A fordítást a projekthez írt kétmenetes assembler (tools/asm.py) végzi: címkéket, INCLUDE-olható modulokat és a ZX81-ROM által használt IX/IY-utasításokat is kezel. A motor binárisa 7454 bájt (0x4082-t\u0151l 0x5DA0-ig), a fordítás során keletkez\u0151 list\u00E1s- és map-f\u00E1jl az engine/build/ mapp\u00E1ban \u0151rz\u0151dik meg."));
add(H2("4.3 A patch-slotok"));
add(body("A build két, a motor binárisában jelölt bűnjellel (markerrel) dolgozik, amelyeket a kazetta-építő a fordítás után ír felül. A NAMESLOT jelöli annak a BASIC-sornak a névmezejét, amelyet a téma-váltás LOAD parancsa beír — így vált a gép csomagot anélkül, hogy a kódot újra kellene fordítani. A TAILSLOT a REM-farok címét jelöli: ide másolja a motor a /save el\u0151k\u00E9sz\u00EDt\u00E9sekor a 72 b\u00E1jtos \u00E1llapot\u00E1t, hogy az a mentett k\u00E9ppel egy\u00FCtt utazzon a kazett\u00E1n."));
add(H2("4.4 A boot-telepítő teljes listája"));
add(body("A rendszerindítás kulcseleme a PICOBOOT blokkba épített telepítő. Teljességében, annak bemutatására, milyen s\u0171r\u0171n \u00E9l a rendszer a g\u00E9p minden b\u00E1jtj\u00E1val, itt a teljes, 54 b\u00E1jtos bootinst.z80 forr\u00E1s:"));
add(...codeBlock([
  "        ORG 0x4082",
  "install:",
  "        ; 1) hat\u00E1rb\u00E1jt a NEW RAM-CHECK s\u00E9t\u00E1j\u00E1nak meg\u00E1ll\u00EDt\u00E1s\u00E1hoz",
  "        LD HL,0x715F",
  "        LD (HL),0xFF",
  "        ; 2) \u00FCres D_FILE a 0x7B00-ra: 0x76 + 24*(32 sz\u00F3k\u00F6z + 0x76)",
  "        LD HL,0x7B00",
  "        LD (HL),0x76",
  "        INC HL",
  "        LD B,24",
  "bi_row: PUSH BC",
  "        LD B,32",
  "        XOR A",
  "bi_cl:  LD (HL),A",
  "        INC HL",
  "        DJNZ bi_cl",
  "        LD (HL),0x76",
  "        INC HL",
  "        POP BC",
  "        DJNZ bi_row",
  "        ; 3) VARS 0x80 z\u00E1r\u00F3jelz\u0151 a 0x7E19-re",
  "        LD HL,0x7E19",
  "        LD (HL),0x80",
  "        ; 4) tart\u00F3s z\u00F3na null\u00E1z\u00E1sa: 0x900 = 2304 b\u00E1jt",
  "        LD HL,0x7160",
  "        LD BC,0x0900",
  "        XOR A",
  "bi_z:   LD (HL),A",
  "        INC HL",
  "        DEC C",
  "        JR NZ,bi_z",
  "        DEC B",
  "        JR NZ,bi_z",
  "        ; 5) RAMTOP := 0x715F (a 0x4004-es rendszer-v\u00E1ltoz\u00F3)",
  "        LD HL,0x715F",
  "        LD (0x4004),HL",
  "        RET",
]));

/* 5. Tudáscsomagok */
add(H1("5. A tudáscsomagok tartalma"));
add(H2("5.1 A csomagok és forrásaik"));
add(body("A gép tudása szöveges mondatgyűjteményekből áll, amelyeket a tools/kbtrain.py eszköz alakít a motor által közvetlenül olvasott PK01 formátumú csomagokká. A csomagok a kazetta blokkjaiban a 0x6900 címtől élnek, legfeljebb 2 KiB helyen; a betöltött csomag cseréjével változik a gép érdeklődési köre."));
add(...tbl("A három tudáscsomag (v0.7.1)",
  ["Csomag", "Forrás", "Méret", "Témakörök"],
  [["base.pk", "data/topics/base.txt (71 mondat)", "2016 bájt", "a gép önmagáról, a beszélgetés öröme, a ZX81-es lét"],
   ["astronomy.pk", "data/topics/astronomy.txt (44 mondat)", "1712 bájt", "csillagok, bolygók, éjszakai égbolt, kíváncsiság"],
   ["science.pk", "data/topics/science.txt (38 mondat)", "1600 bájt", "kísérletek, anyagok, találmányok, megfigyelések"]],
  [20, 34, 14, 32]));
add(body("A mondatok egyszerű, a gép szókincséhez illeszkedő angol nyelvűek — a motor az angolt használja a társalgás nyelveként, mivel a ZX81 karakterkészlete és a szótári tömörítés erre optimalizált. Néhány példa az alaptudásból: \u201Emy memory is small but i try\u201D, \u201Ewe can talk all day\u201D, \u201Ea good question is a gift\u201D, \u201Ethe tape keeps my dreams\u201D."));
add(H2("5.2 A PK01 formátum és a szótár"));
add(body("Minden csomag a PK01 bűnjellel kezdődik, amelyet verzió-, karakterkészlet- és darabszám-mezők, a mintázatok számára (nplans), egy ellenőrző összeg-kulcs (xor) és maga a tömörített mondat-anyag követ. A motor a beolvasott mondatokat a szótárral együtt használja: a bejövő mondatot szavakra töri, a szavakat a 0x5F00-tól élő szótárban keresi (hash-index, zászlók, offsetek, majd a szólista), és a találatok alapján választ mintázatot a válasz-előállítóban."));
add(body("A szótár (dict.bin, 2560 bájt) négy szakaszból áll: egy 256 bájtos hash-index, egy szavankénti zászlótábla (kérdez\u0151-, igesz\u00F3-, f\u0151neves-jelz\u0151 bitjeivel), egy 512 b\u00E1jtos offset-t\u00E1bla \u00E9s a k\u00F3dolt sz\u00F3lista. A tanult-z\u00F3na seg\u00EDts\u00E9g\u00E9vel a g\u00E9p az \u00FAj szavakat is megjegyzi, \u00E9s a k\u00F6vetkez\u0151 /save-n\u00E9l a kazett\u00E1ra viszi \u0151ket."));

/* 6. Változatások */
add(H1("6. Változatások"));
add(...tbl("A kiadások áttekintése",
  ["Verzió", "Dátum", "Tartalom"],
  [["v0.5.4", "régi projekt", "az eredeti, EightyOne-ban bizonyított kazetták (boot + 14 téma-blokk)"],
   ["v0.6.5", "régi projekt", "a motort tartalmazó verzió, amellyel a felhasználó már társalgott"],
   ["v0.7.0", "2026. 11. 23.", "új, rövid blokkos kazettaszerkezet + a T81-fájlformátum javítása"],
   ["v0.7.1", "2026. 11. 23.", "a RAMTOP-cím javítása (fehér képernyő a betöltés után) + dokumentációcsomag"]],
  [12, 18, 70]));
add(H2("6.1 A v0.7.0: a kazettaformátum javítása"));
add(body("A v0.7.0 első változata két, az emulátorban azonnal jelentkező hibával bírt. Egyrészt a kazettafájl nem kezdődött a kötelez\u0151 EO81 bűnjellel, emiatt az EightyOne már a fájl beszúrásakor elutasította a szalagot — a hivatalos EightyOne-forr\u00E1s (LoadT81File rutinja) szerint a b\u0171njel n\u00E9lk\u00FCli f\u00E1jl bet\u00F6lt\u00E9se elutas\u00EDt\u00E1ssal j\u00E1r. M\u00E1sr\u00E9szt a blokkok z\u00E1r\u00F3 b\u00E1jtja nem 0x80 volt, az emul\u00E1tor ez\u00E9rt a blokkok v\u00E9g\u00E9b\u0151l sz\u00E1z b\u00E1jtnyi r\u00E9szt v\u00E1gott volna le. Mindkett\u0151 jav\u00EDtva: a f\u00E1jl EO81 b\u0171njellel indul, a k\u00E9pek z\u00E1r\u00F3 b\u00E1jtja 0x80."));
add(H2("6.2 A v0.7.1: a fehér képernyő oka és javítása"));
add(body("A v0.7.0 javított kazettája már betölt\u00F6tt, a bemutat\u00F3 sz\u00F6veg is megjelent, az ut\u00E1nt\u00F6lt\u00E9s (LOAD \"\") v\u00E9g\u00E9n azonban a k\u00E9perny\u0151 kifeh\u00E9redett, \u00E9s a g\u00E9p nem reag\u00E1lt. A hiba gy\u00F6ker\u00E9t a ROM NEW parancs\u00E1nak m\u0171k\u00F6d\u00E9s\u00E9ben tal\u00E1ltuk meg: a NEW a RAMTOP rendszer-v\u00E1ltoz\u00F3b\u00F3l olvassa, meddig t\u00F6r\u00F6lje a mem\u00F3ri\u00E1t, \u00E9s a teljes alatta l\u00E9v\u0151 ter\u00E9letet 0x02-vel t\u00F6lti fel. A boot-telep\u00EDt\u0151 azonban a RAMTOP-ot t\u00E9ves c\u00EDmre \u00EDrta (a 0x4026-os rendszer-v\u00E1ltoz\u00F3ra, amely val\u00F3j\u00E1ban a billenty\u0171zet utols\u00F3 k\u00F3dj\u00E1t t\u00E1rolja), ez\u00E9rt a RAMTOP \u00E9rintetlen\u00FCl a g\u00E9p tetej\u00E9n maradt 0x8000-n — \u00E9s a NEW a teljes 16 KiB-ot fel\u00FCl\u00EDrta, bele\u00E9rtve a telep\u00EDt\u0151 \u00E1ltal k\u00E9sz\u00EDtett k\u00E9perny\u0151f\u00E1jlt is."));
add(body("A PICOBASE bet\u00F6lt\u00E9se ut\u00E1n a rendszer-v\u00E1ltoz\u00F3k a 0x7B00-as k\u00E9perny\u0151re mutattak, amelynek minden b\u00E1jtja 0x02 volt — sorv\u00E9g-jelz\u0151k n\u00E9lk\u00FCl. A ZX81 k\u00E9perny\u0151-gener\u00E1l\u00E1sa az ilyen k\u00E9pf\u00E1jlban \u00F6sszeomlik, a k\u00E9p pedig kifeh\u00E9redik: pontosan az \u00E9szlelt jelens\u00E9g. A jav\u00EDt\u00E1s egyetlen utas\u00EDt\u00E1s c\u00EDm\u00E9nek helyesb\u00EDt\u00E9se volt (LD (0x4004),HL), amelyet a ROM nyers b\u00E1jtjaib\u00F3l igazoltunk: a NEW rutin a 0x4004-es c\u00EDmr\u0151l olvassa a RAMTOP-ot. A jav\u00EDt\u00E1st val\u00F3di ROM-mal futtatott szimul\u00E1ci\u00F3n is bizony\u00EDtottuk: a NEW m\u00E1r a hat\u00E1rb\u00E1jtn\u00E1l meg\u00E1ll, a k\u00E9perny\u0151f\u00E1jl \u00E9s a tart\u00F3s z\u00F3na s\u00E9r\u00FCletlen marad, \u00E9s a motor fel\u00FClete kirajzol\u00F3dik."));

/* 7. Ellenőrzések */
add(H1("7. Ellenőrzések és tesztek"));
add(body("Minden kiadás három, egymást kiegészítő ellenőrzésen megy át. A kazetta-szerkezetet a tools/t81_validate.py vizsgálja: az EightyOne betölt\u0151rutinj\u00E1nak logik\u00E1j\u00E1t szimul\u00E1lva ellen\u0151rzi a b\u0171njelet, a blokkfejl\u00E9ceket, a blokkok z\u00E1r\u00F3 b\u00E1jtjait \u00E9s a n\u00E9v-illeszt\u00E9st. A v0.7.1 kazetta e vizsg\u00E1laton hib\u00E1tlanul \u00E1tment (mind a n\u00E9gy blokk rendben)."));
add(body("A m\u0171k\u00F6d\u00E9st a tools/zx81sim.py hajtja végre: a motor val\u00F3di g\u00E9pi k\u00F3dj\u00E1t futtatva egy teljes beszélget\u00E9st szimul\u00E1l a boot-t\u00F3l a v\u00E1laszokig (tests/chat_flow.txt). A v0.7.1-en a teljes forgat\u00F3k\u00F6nyv — boot, profil-bek\u00E9r\u00E9s, t\u00E1rsalg\u00E1s, ment\u00E9s — hib\u00E1tlanul lefut."));
add(body("A harmadik, legszigorúbb r\u00E9teg a tools/romsim.py: a ZX81 valódi, 8 KiB-os ROM-képét futtatja, \u00E9s benne a rendszerind\u00EDt\u00E1s kritikus l\u00E9p\u00E9seit vizsg\u00E1lja (tools/romflow_test.py). A v0.7.1-en a teszt h\u00E1rom l\u00E9p\u00E9se mind helyes kimenetet adott: a telep\u00EDt\u0151 helyesen \u00E1ll\u00EDtotta a RAMTOP-ot, a NEW nem \u00E9rintette a v\u00E9dett fels\u0151 mem\u00F3ri\u00E1t, \u00E9s a motor bel\u00E9p\u00E9se ut\u00E1n a profil-bek\u00E9r\u0151 fel\u00FClet (FIRST RUN. LETS SET YOU UP. / YEAR?) kirajzol\u00F3dott a k\u00E9perny\u0151re. A v\u00E9gs\u0151 sz\u00F3 azonban mindig az emul\u00E1toron meg tartozik: ez\u00E9rt a k\u00E9zbes\u00EDt\u00E9s el\u0151tt a kazetta a EightyOne-ban t\u00F6rt\u00E9nt bet\u00F6lt\u00E9si pr\u00F3b\u00E1n is \u00E1tesik."));

/* ---------- dokumentum összeállítása ---------- */
const doc = new Document({
  styles: { default: { document: {
    run: { font: { ascii: "Times New Roman", eastAsia: "SimSun" },
           size: 24, color: "000000" },
    paragraph: { spacing: { line: 312 } },
  }}},
  features: { updateFields: true },
  sections: [
    { /* borító */
      properties: { page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 0, bottom: 0, left: 0, right: 0 },
      }},
      children: buildCoverR1({
        title: "GLM Pico AI v0.7.1",
        subtitle: "Dokument\u00E1ci\u00F3csomag \u2014 ZX81 t\u00E1rsalg\u00F3g\u00E9p",
        englishLabel: "GLM PICO AI",
        metaLines: [
          "Kazetta: GLM_PicoAI_v0.7.1_kazetta.T81",
          "C\u00E9lrendszer: Sinclair ZX81 16K (EightyOne emul\u00E1tor)",
          "K\u00E9sz\u00FClt: 2026. november 23.",
        ],
        footerLeft: "GLM \u2014 Pico AI projekt",
        footerRight: "v0.7.1",
      }),
    },
    { /* tartalomjegyzék — római számozás */
      properties: {
        type: SectionType.NEXT_PAGE,
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
          pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN },
        },
      },
      footers: { default: pageFooter() },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 480, after: 360 },
          children: [new TextRun({ text: "Tartalomjegyz\u00E9k", bold: true,
            size: 32, font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
        }),
        new TableOfContents("Tartalomjegyz\u00E9k", {
          hyperlink: true, headingStyleRange: "1-2",
        }),
        new Paragraph({
          spacing: { before: 200 },
          children: [new TextRun({
            text: "Megjegyz\u00E9s: a tartalomjegyz\u00E9k mez\u0151k\u00F3dokkal k\u00E9sz\u00FClt. A pontos oldalsz\u00E1mok\u00E9rt a tartalomjegyz\u00E9kre kattintva v\u00E1lassza a \u201EMez\u0151 friss\u00EDt\u00E9se\u201D lehet\u0151s\u00E9get.",
            italics: true, size: 18, color: "888888" })],
        }),
      ],
    },
    { /* törzs — arab számozás 1-től */
      properties: {
        type: SectionType.NEXT_PAGE,
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL },
        },
      },
      headers: { default: docHeader() },
      footers: { default: pageFooter() },
      children: bodyChildren,
    },
  ],
});

const OUT = process.argv[2] ||
  "/home/z/my-project/download/GLM_PicoAI_v0.7.1_dokumentacio.docx";
Packer.toBuffer(doc).then(buf => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, buf);
  console.log("OK:", OUT, buf.length, "b\u00E1jt");
});

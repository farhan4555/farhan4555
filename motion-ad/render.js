// Renders ad.html frame-by-frame with headless Chromium and writes PNG frames.
// usage: node render.js <outDir> [fps] [start] [end] [step] [offset]
const path = require('path'), fs = require('fs');
const { chromium } = require(process.env.PW || 'playwright');
(async () => {
  const [out = 'frames', fps = 30, start = 0, end = null, step = 1, offset = 0] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(1); });
  await page.goto('file://' + path.resolve(__dirname, 'ad.html') + '?render');
  await page.evaluate(() => document.fonts.ready);
  const dur = await page.evaluate(() => window.DURATION);
  const last = end === null ? Math.round(dur * fps) : +end;
  const canvas = await page.$('#gl');
  for (let f = +start + +offset; f < last; f += +step) {
    const t0 = Date.now();
    await page.evaluate(t => window.renderFrame(t), f / fps);
    await canvas.screenshot({ path: path.join(out, `f${String(f).padStart(5, '0')}.png`) });
    if (f % 30 === +offset % 30 || +step > 1 && f % 30 < +step) console.log(`frame ${f}/${last} ${Date.now() - t0}ms`);
  }
  await browser.close();
})();

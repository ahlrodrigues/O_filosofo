const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = 3456;
const HOST = '127.0.0.1';
const DIST = __dirname;

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.css': 'text/css'
};

// Only these files may be written via /save, and only by exact basename
// (no path separators), so a crafted filename can't escape DIST.
const SAVE_ALLOWED_FILES = new Set(['quotes_bilingue.json', 'quotes_humor_bilingue.json']);

function resolveWithinDist(urlPathname) {
  const resolved = path.resolve(DIST, `.${urlPathname}`);
  if (resolved !== DIST && !resolved.startsWith(DIST + path.sep)) {
    return null;
  }
  return resolved;
}

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/save') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { filename, content } = JSON.parse(body);
        if (typeof filename !== 'string' || path.basename(filename) !== filename || !SAVE_ALLOWED_FILES.has(filename)) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'Nome de arquivo não permitido' }));
          return;
        }
        fs.writeFileSync(path.join(DIST, filename), content);
        res.writeHead(200);
        res.end(JSON.stringify({ ok: true }));
      } catch (e) {
        res.writeHead(500);
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  let requestUrl;
  try {
    requestUrl = new URL(req.url, `http://${HOST}`);
  } catch (e) {
    res.writeHead(400);
    res.end('Bad request');
    return;
  }

  const pathname = requestUrl.pathname === '/' ? '/review_quotes.html' : requestUrl.pathname;
  const filePath = resolveWithinDist(pathname);

  if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }

  const ext = path.extname(filePath);
  res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'text/plain' });
  res.end(fs.readFileSync(filePath));
});

server.listen(PORT, HOST, () => {
  console.log(`http://${HOST}:${PORT}`);
});

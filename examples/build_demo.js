// Builds examples/demo.html: the real board template with sample-board.json baked in.
// Run from the repository root: node examples/build_demo.js
const fs = require("fs");
const snap = JSON.parse(fs.readFileSync("examples/sample-board.json", "utf8"));
let page = fs.readFileSync("skills/agent-board/board.html", "utf8").replace("<title>Agent Board</title>", "<title>Agent Board demo</title>");
const anchor = "<script>\nconst ICON";
if (!page.includes(anchor)) throw new Error("board.html changed: script anchor not found");
// Times in the sample are "minutes ago", so the demo looks fresh whenever it is opened.
const loader = `<script>
window.BOARD_SNAPSHOT = ${JSON.stringify(snap)};
for (const col of ["agents", "tasks"]) for (const row of Object.values(window.BOARD_SNAPSHOT[col])) {
  row.updated_at = new Date(Date.now() - row.minutes_ago * 60000).toISOString();
}
window.BOARD_SNAPSHOT.taken_at = new Date().toISOString();
</script>
`;
page = page.replace(anchor, loader + anchor);
page = '<!doctype html>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<style>body{margin:0}</style>\n' + page;
fs.writeFileSync("examples/demo.html", page);
console.log("wrote examples/demo.html");

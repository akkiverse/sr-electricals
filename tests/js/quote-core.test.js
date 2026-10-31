// Browser quote list logic (US-3). Run with: npm test
const test = require("node:test");
const assert = require("node:assert/strict");
const Q = require("../../public/static/quote-core.js");

function memoryStorage() {
  const data = new Map();
  return { getItem: (k) => (data.has(k) ? data.get(k) : null), setItem: (k, v) => data.set(k, String(v)) };
}
const wire = { slug: "polycab-wire-2-5", name: "Polycab FR PVC house wire 2.5 sq mm", brand: "Polycab" };
const mcb = { slug: "havells-mcb-16", name: "Havells MCB single pole 16 A", brand: "Havells" };

test("AC-3.1: adding an item with quantity N shows it with N; adding again increases its quantity", () => {
  let items = [];
  items = Q.add(items, wire, 5);
  assert.equal(Q.count(items), 1);
  assert.deepEqual(items[0], { ...wire, qty: 5 });
  items = Q.add(items, mcb, 2);
  assert.equal(Q.count(items), 2);
  items = Q.add(items, wire, 3);
  assert.equal(Q.count(items), 2);
  assert.equal(items.find((i) => i.slug === wire.slug).qty, 8);
});

test("AC-3.2: changing a quantity or removing updates the list; only whole numbers 1 to 9999", () => {
  let items = Q.add(Q.add([], wire, 1), mcb, 1);
  items = Q.setQty(items, wire.slug, "40");
  assert.equal(items[0].qty, 40);
  items = Q.remove(items, mcb.slug);
  assert.deepEqual(items.map((i) => i.slug), [wire.slug]);
  for (const bad of ["0", "10000", "2.5", "-1", "", "abc", " 12a"]) {
    assert.throws(() => Q.setQty(items, wire.slug, bad), { message: Q.QTY_ERROR });
    assert.throws(() => Q.add(items, mcb, bad), { message: Q.QTY_ERROR });
  }
  assert.equal(Q.setQty(items, wire.slug, "9999")[0].qty, 9999);
  assert.equal(Q.add(Q.setQty(items, wire.slug, 9999), wire, 5)[0].qty, 9999);
});

test("AC-3.3: the WhatsApp link lists each item as <name> (<brand>) x <qty> plus name and buyer type", () => {
  const items = Q.add(Q.add([], wire, 20), mcb, 12);
  const url = Q.whatsappUrl("919304359146", items, { shop: "SR Electrical", name: "Ravi", buyerType: "Contractor" });
  assert.ok(url.startsWith("https://wa.me/919304359146?text="));
  const text = decodeURIComponent(url.split("?text=")[1]);
  assert.match(text, /Polycab FR PVC house wire 2\.5 sq mm \(Polycab\) x 20/);
  assert.match(text, /Havells MCB single pole 16 A \(Havells\) x 12/);
  assert.match(text, /Name: Ravi/);
  assert.match(text, /I am a: Contractor/);
  const noName = decodeURIComponent(Q.whatsappUrl("919304359146", items, {}).split("?text=")[1]);
  assert.doesNotMatch(noName, /Name:/);
});

test("AC-3.4: the list is kept in browser storage and survives a reload", () => {
  const storage = memoryStorage();
  Q.save(storage, Q.add([], wire, 7));
  const reloaded = Q.load(storage);
  assert.deepEqual(reloaded, [{ ...wire, qty: 7 }]);
  storage.setItem(Q.KEY, "not json");
  assert.deepEqual(Q.load(storage), []);
  storage.setItem(Q.KEY, JSON.stringify([{ slug: "x", name: "X", qty: 0 }, { slug: "y", name: "Y", qty: 2 }]));
  assert.deepEqual(Q.load(storage).map((i) => i.slug), ["y"]);
});

test("AC-3.5: an empty list can't be sent", () => {
  assert.equal(Q.canSend([]), false);
  assert.equal(Q.canSend(Q.add([], wire, 1)), true);
  assert.equal(Q.canSend(Q.load(memoryStorage())), false);
});

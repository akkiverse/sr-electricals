/* Quote list logic, kept in the browser only (AC-3.1 to AC-3.5). No DOM here, so it is unit-tested with node --test. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.QuoteCore = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var KEY = "sr_quote_v1";
  var MAX = 9999;
  var QTY_ERROR = "Enter a whole number from 1 to 9999.";

  function parseQty(value) {
    var s = String(value == null ? "" : value).trim();
    if (!/^\d+$/.test(s)) return null;
    var n = parseInt(s, 10);
    return n >= 1 && n <= MAX ? n : null;
  }

  function load(storage) {
    try {
      var raw = storage && storage.getItem(KEY);
      var data = raw ? JSON.parse(raw) : [];
      if (!Array.isArray(data)) return [];
      return data.filter(function (it) {
        return it && typeof it.slug === "string" && typeof it.name === "string" && parseQty(it.qty) !== null;
      }).map(function (it) {
        return { slug: it.slug, name: it.name, brand: String(it.brand || ""), qty: parseQty(it.qty) };
      });
    } catch (e) {
      return [];
    }
  }

  function save(storage, items) {
    try { storage && storage.setItem(KEY, JSON.stringify(items)); } catch (e) { /* private mode: list lasts this visit */ }
    return items;
  }

  function add(items, item, qty) {
    var n = parseQty(qty);
    if (n === null) throw new Error(QTY_ERROR);
    var out = items.map(function (it) { return Object.assign({}, it); });
    var found = out.find(function (it) { return it.slug === item.slug; });
    if (found) found.qty = Math.min(MAX, found.qty + n);
    else out.push({ slug: item.slug, name: item.name, brand: item.brand || "", qty: n });
    return out;
  }

  function setQty(items, slug, qty) {
    var n = parseQty(qty);
    if (n === null) throw new Error(QTY_ERROR);
    return items.map(function (it) { return it.slug === slug ? Object.assign({}, it, { qty: n }) : Object.assign({}, it); });
  }

  function remove(items, slug) {
    return items.filter(function (it) { return it.slug !== slug; });
  }

  function count(items) {
    return items.reduce(function (sum, it) { return sum + 1; }, 0);
  }

  function canSend(items) { return items.length > 0; }

  function message(items, opts) {
    opts = opts || {};
    var lines = ["Hello " + (opts.shop || "SR Electrical") + ", please send your best rate for:"];
    items.forEach(function (it, i) {
      lines.push((i + 1) + ". " + it.name + (it.brand ? " (" + it.brand + ")" : "") + " x " + it.qty);
    });
    if (opts.name && opts.name.trim()) lines.push("Name: " + opts.name.trim());
    if (opts.buyerType) lines.push("I am a: " + opts.buyerType);
    lines.push("Sent from the SR Electrical website");
    return lines.join("\n");
  }

  function whatsappUrl(number, items, opts) {
    return "https://wa.me/" + number + "?text=" + encodeURIComponent(message(items, opts));
  }

  return { KEY: KEY, QTY_ERROR: QTY_ERROR, parseQty: parseQty, load: load, save: save, add: add, setQty: setQty,
           remove: remove, count: count, canSend: canSend, message: message, whatsappUrl: whatsappUrl };
});

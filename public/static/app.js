/* Page behaviour: theme toggle (AC-6.2), quote list UI (US-3). Logic lives in quote-core.js. */
(function () {
  "use strict";
  var Q = window.QuoteCore;
  var store = null;
  try { store = window.localStorage; } catch (e) { store = null; }
  var body = document.body;
  var waNumber = body.getAttribute("data-wa");
  var shop = body.getAttribute("data-shop");

  /* ---------- theme ---------- */
  var root = document.documentElement;
  function currentTheme() {
    if (root.dataset.theme) return root.dataset.theme;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  function labelToggle() {
    var btn = document.querySelector("[data-theme-toggle]");
    if (btn) btn.setAttribute("aria-label", currentTheme() === "dark" ? "Switch to light theme" : "Switch to dark theme");
  }
  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-theme-toggle]");
    if (!t) return;
    var next = currentTheme() === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try { store && store.setItem("sr_theme", next); } catch (err) { /* ignore */ }
    labelToggle();
  });
  labelToggle();

  /* ---------- toast ---------- */
  var toastTimer;
  function toast(text) {
    var el = document.querySelector("[data-toast]");
    if (!el) return;
    el.textContent = text;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove("show"); }, 2600);
  }

  /* ---------- quote list ---------- */
  var items = Q.load(store);
  function persist(next) { items = Q.save(store, next); refreshCount(); }
  function refreshCount() {
    var n = Q.count(items);
    document.querySelectorAll("[data-quote-count]").forEach(function (el) {
      el.textContent = String(n);
      el.hidden = n === 0;
      el.setAttribute("aria-label", n + " item" + (n === 1 ? "" : "s") + " in your quote list");
    });
  }
  refreshCount();

  function addItem(item, qty) {
    persist(Q.add(items, item, qty));
    toast("Added " + item.name + " to your quote list");
  }

  // "Add" on product cards
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-add-quote]");
    if (!btn) return;
    addItem({ slug: btn.dataset.slug, name: btn.dataset.name, brand: btn.dataset.brand }, 1);
    btn.classList.add("added");
    setTimeout(function () { btn.classList.remove("added"); }, 900);
  });

  // steppers (+/-) next to any quantity input
  document.addEventListener("click", function (e) {
    var step = e.target.closest("[data-step]");
    if (!step) return;
    var input = step.parentElement.querySelector("input");
    var n = Q.parseQty(input.value) || 1;
    n = Math.max(1, Math.min(9999, n + parseInt(step.dataset.step, 10)));
    input.value = n;
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });

  // product page form
  var addForm = document.querySelector("[data-add-form]");
  if (addForm) {
    addForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var input = addForm.querySelector("input[name=qty]");
      var err = addForm.querySelector("[data-error]");
      try {
        addItem({ slug: addForm.dataset.slug, name: addForm.dataset.name, brand: addForm.dataset.brand }, input.value);
        err.hidden = true; input.removeAttribute("aria-invalid");
      } catch (ex) {
        err.textContent = ex.message; err.hidden = false; input.setAttribute("aria-invalid", "true"); input.focus();
      }
    });
  }

  // quote page
  var page = document.querySelector("[data-quote-page]");
  if (page) {
    var list = page.querySelector("[data-quote-list]");
    var tpl = page.querySelector("[data-quote-row]");
    var empty = page.querySelector("[data-quote-empty]");
    var form = page.querySelector("[data-quote-form]");
    var send = page.querySelector("[data-quote-send]");
    var formErr = page.querySelector("[data-quote-error]");

    var render = function () {
      list.innerHTML = "";
      items.forEach(function (it, i) {
        var row = tpl.content.firstElementChild.cloneNode(true);
        var link = row.querySelector("[data-f=link]");
        link.textContent = it.name; link.href = "/products/" + encodeURIComponent(it.slug);
        row.querySelector("[data-f=brand]").textContent = it.brand;
        var qty = row.querySelector("[data-f=qty]");
        qty.value = it.qty; qty.id = "qty-" + i;
        var lab = row.querySelector("[data-f=qlabel]");
        lab.htmlFor = qty.id; lab.textContent = "Quantity of " + it.name;
        row.querySelector("[data-remove]").setAttribute("aria-label", "Remove " + it.name);
        row.dataset.slug = it.slug;
        list.appendChild(row);
      });
      var has = Q.canSend(items);
      empty.hidden = has;
      form.hidden = !has;
      send.disabled = !has;
    };
    list.addEventListener("change", function (e) {
      var input = e.target.closest("[data-f=qty]");
      if (!input) return;
      var row = input.closest(".qrow");
      var err = row.querySelector("[data-f=error]");
      try {
        persist(Q.setQty(items, row.dataset.slug, input.value));
        err.hidden = true; input.removeAttribute("aria-invalid");
      } catch (ex) {
        err.textContent = ex.message; err.hidden = false; input.setAttribute("aria-invalid", "true");
      }
    });
    list.addEventListener("click", function (e) {
      var rm = e.target.closest("[data-remove]");
      if (!rm) return;
      persist(Q.remove(items, rm.closest(".qrow").dataset.slug));
      render();
      toast("Removed from your quote list");
    });
    page.querySelector("[data-quote-clear]").addEventListener("click", function () {
      persist([]); render();
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (list.querySelector("[aria-invalid=true]")) {
        formErr.textContent = "Fix the quantities marked above, then send again."; formErr.hidden = false; return;
      }
      formErr.hidden = true;
      var url = Q.whatsappUrl(waNumber, items, {
        shop: shop,
        name: form.querySelector("[name=name]").value,
        buyerType: form.querySelector("[name=buyer_type]").value
      });
      send.classList.add("zap");
      setTimeout(function () { send.classList.remove("zap"); window.location.href = url; }, 420);
    });
    render();
  }

  document.body.addEventListener("htmx:afterSwap", refreshCount);
})();

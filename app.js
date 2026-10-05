let appState = {
    settings: {},
    catalog: [
        { id: 1, name: "1.5 sq mm Wire", category: "Electrical", rate: 1850, unit: "Roll", gst: 18, description: "Flame retardant copper wire", image_url: "" },
        { id: 2, name: "2.5 sq mm Wire", category: "Electrical", rate: 2850, unit: "Roll", gst: 18, description: "Heavy duty copper wire", image_url: "" },
        { id: 3, name: "1 Inch PVC Pipe", category: "Plumbing", rate: 320, unit: "Length", gst: 18, description: "Rigid plumbing pipe", image_url: "" }
    ],
    cart: [],
    currentDocNumber: "EST-1001",
    currentDocId: null
};

function $(id) {
    return document.getElementById(id);
}

function escapeHTML(str) {
    if (!str) return "";
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

function formatCurrency(amount) {
    return "₹" + parseFloat(amount || 0).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function isGstEnabled() {
    return $("billTypeToggle").value === "gst";
}

function isPriceVisible() {
    return $("priceDisplayToggle").value === "show";
}

function previewImage(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            $("imagePreview").src = e.target.result;
            $("imagePreviewContainer").style.display = "block";
        };
        reader.readAsDataURL(file);
    }
}

function login() {
    const email = $("loginEmail").value.trim();
    const password = $("loginPassword").value;
    if ((email === "hari@example.com" || email === "kavin@example.com") && password === "password") {
        $("loginStatus").className = "status success";
        $("loginStatus").textContent = "Login successful.";
        $("userStatus").textContent = "HARI ALTRIGAL";
        setTimeout(() => goTo(2), 400);
    } else {
        $("loginStatus").className = "status error";
        $("loginStatus").textContent = "Invalid email or password.";
    }
}

function buildCategories() {
    const select = $("category");
    if (!select) return;
    const categories = [...new Set(appState.catalog.map(p => p.category))];
    select.innerHTML = '<option value="all">All Categories</option>';
    categories.forEach(cat => {
        const opt = document.createElement("option");
        opt.value = cat; opt.textContent = cat;
        select.appendChild(opt);
    });
}

function renderProducts() {
    const searchEl = $("search");
    const categoryEl = $("category");
    if (!searchEl || !categoryEl) return;

    const search = searchEl.value.toLowerCase().trim();
    const category = categoryEl.value;
    const filtered = appState.catalog.filter(p => {
        const matchesSearch = p.name.toLowerCase().includes(search) || (p.description || "").toLowerCase().includes(search);
        const matchesCategory = category === "all" || p.category === category;
        return matchesSearch && matchesCategory;
    });

    const container = $("products");
    if (!container) return;
    container.innerHTML = filtered.length === 0 ? "<p>No items found.</p>" : "";

    filtered.forEach(p => {
        const div = document.createElement("div");
        div.className = "product";
        const imgTag = p.image_url 
            ? '<img src="' + p.image_url + '" class="item-img" alt="' + escapeHTML(p.name) + '">' 
            : '<div class="item-img" style="display:flex;align-items:center;justify-content:center;color:#94a3b8;">No Image</div>';

        div.innerHTML = '<div>' +
            imgTag +
            '<span class="product-category">' + escapeHTML(p.category) + '</span>' +
            '<h3>' + escapeHTML(p.name) + '</h3>' +
            '<p>' + escapeHTML(p.description || "") + '</p>' +
            '</div>' +
            '<div class="product-bottom">' +
            '<div>' +
            '<div class="price">' + formatCurrency(p.rate) + '</div>' +
            '<small>per ' + escapeHTML(p.unit) + ' • GST ' + p.gst + '%</small>' +
            '</div>' +
            '<button class="btn-primary" onclick="addToCartById(' + p.id + ')">Add Item</button>' +
            '</div>';
        container.appendChild(div);
    });
}

function createNewProduct(event) {
    event.preventDefault();
    const name = $("newItemName").value.trim();
    const category = $("newItemCategory").value.trim();
    const rate = parseFloat($("newItemRate").value);
    const unit = $("newItemUnit").value.trim();
    const gst = parseFloat($("newItemGST").value) || 0;
    const description = $("newItemDescription").value.trim();
    const imagePreview = $("imagePreview").src;

    const newProduct = {
        id: Date.now(),
        name,
        category,
        rate,
        unit,
        gst,
        description,
        image_url: $("imagePreviewContainer").style.display !== "none" ? imagePreview : ""
    };

    appState.catalog.push(newProduct);
    buildCategories();
    renderProducts();
    $("addProductForm").reset();
    $("imagePreviewContainer").style.display = "none";
}

function addToCartById(id) {
    const item = appState.catalog.find(p => p.id === id);
    if (!item) return;
    const existing = appState.cart.find(c => c.id === id);
    if (existing) {
        existing.qty += 1;
    } else {
        appState.cart.push({ ...item, qty: 1 });
    }
    renderCartUI();
}

function updateQty(id, qty) {
    const item = appState.cart.find(c => c.id === id);
    if (item) {
        item.qty = Math.max(1, parseInt(qty) || 1);
        renderCartUI();
    }
}

function removeFromCart(id) {
    appState.cart = appState.cart.filter(c => c.id !== id);
    renderCartUI();
}

function calculateCartTotals() {
    let subtotal = 0;
    let tax = 0;
    const useGst = isGstEnabled();

    appState.cart.forEach(item => {
        const itemSubtotal = item.rate * item.qty;
        subtotal += itemSubtotal;
        if (useGst) {
            tax += (itemSubtotal * (item.gst || 0)) / 100;
        }
    });

    return {
        subtotal,
        tax,
        grandTotal: subtotal + tax
    };
}

function renderCartUI() {
    const tbody = $("cartBody");
    if (!tbody) return;
    tbody.innerHTML = "";
    const useGst = isGstEnabled();
    const showPrice = isPriceVisible();

    document.querySelectorAll(".gst-col").forEach(el => {
        el.style.display = useGst ? "" : "none";
    });
    document.querySelectorAll(".price-col").forEach(el => {
        el.style.display = showPrice ? "" : "none";
    });

    appState.cart.forEach(item => {
        const tr = document.createElement("tr");
        const itemTax = useGst ? (item.rate * item.qty * item.gst) / 100 : 0;
        const itemTotal = (item.rate * item.qty) + itemTax;

        const imgHtml = item.image_url ? '<img src="' + item.image_url + '" class="cart-thumb" alt="">' : '-';

        tr.innerHTML = '<td>' + imgHtml + '</td>' +
            '<td><strong>' + escapeHTML(item.name) + '</strong><br><small>' + escapeHTML(item.description || "") + '</small></td>' +
            '<td>' + escapeHTML(item.unit) + '</td>' +
            '<td class="price-col" style="' + (showPrice ? '' : 'display:none;') + '">' + formatCurrency(item.rate) + '</td>' +
            '<td><input type="number" class="qty" value="' + item.qty + '" min="1" onchange="updateQty(' + item.id + ', this.value)"></td>' +
            '<td class="gst-col price-col" style="' + (useGst && showPrice ? '' : 'display:none;') + '">' + formatCurrency(itemTax) + ' (' + item.gst + '%)</td>' +
            '<td class="price-col" style="' + (showPrice ? '' : 'display:none;') + '">' + formatCurrency(itemTotal) + '</td>' +
            '<td><button class="btn-danger" onclick="removeFromCart(' + item.id + ')">Remove</button></td>';

        tbody.appendChild(tr);
    });

    const totals = calculateCartTotals();
    $("cartSubtotal").textContent = formatCurrency(totals.subtotal);
    $("cartTax").textContent = formatCurrency(totals.tax);
    $("cartTotal").textContent = formatCurrency(totals.grandTotal);
}

function goTo(step) {
    for (let i = 1; i <= 4; i++) {
        const page = $("page" + i);
        const stepEl = $("step" + i);
        if (page) page.classList.remove("active");
        if (stepEl) stepEl.classList.remove("active");
    }
    const targetPage = $("page" + step);
    const targetStep = $("step" + step);
    if (targetPage) targetPage.classList.add("active");
    if (targetStep) targetStep.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function buildQuotationView() {
    const totals = calculateCartTotals();
    const useGst = isGstEnabled();

    $("quoteNumber").textContent = appState.currentDocNumber;
    $("quoteDate").textContent = $("docDate").value;
    $("quoteBillType").textContent = useGst ? "GST Bill" : "Non-GST Estimate";

    $("quoteClient").textContent = $("clientName").value || "-";
    $("quoteCompany").textContent = $("clientCompany").value || "-";
    $("quoteAddress").textContent = $("clientAddress").value || "-";
    $("quotePhone").textContent = $("clientPhone").value || "-";
    $("quoteEmail").textContent = $("clientEmail").value || "-";
    $("quoteGST").textContent = $("clientGST").value || "-";
    $("quoteTerms").textContent = $("terms").value;

    const tbody = $("quoteItems");
    if (!tbody) return;
    tbody.innerHTML = "";

    document.querySelectorAll("#quotation .gst-col").forEach(el => {
        el.style.display = useGst ? "" : "none";
    });

    appState.cart.forEach((item, index) => {
        const tr = document.createElement("tr");
        const itemTax = useGst ? (item.rate * item.qty * item.gst) / 100 : 0;
        const itemTotal = (item.rate * item.qty) + itemTax;
        const imgHtml = item.image_url ? '<img src="' + item.image_url + '" class="cart-thumb" alt="">' : '-';

        tr.innerHTML = '<td>' + (index + 1) + '</td>' +
            '<td>' + imgHtml + '</td>' +
            '<td><strong>' + escapeHTML(item.name) + '</strong><br><small>' + escapeHTML(item.description || "") + '</small></td>' +
            '<td>' + escapeHTML(item.unit) + '</td>' +
            '<td>' + item.qty + '</td>' +
            '<td class="text-right">' + formatCurrency(item.rate) + '</td>' +
            '<td class="gst-col text-right" style="' + (useGst ? '' : 'display:none;') + '">' + formatCurrency(itemTax) + '</td>' +
            '<td class="text-right">' + formatCurrency(itemTotal) + '</td>';

        tbody.appendChild(tr);
    });

    $("quoteSubtotal").textContent = formatCurrency(totals.subtotal);
    $("quoteTax").textContent = formatCurrency(totals.tax);
    $("quoteTotal").textContent = formatCurrency(totals.grandTotal);
}

function saveQuotation() {
    if (appState.cart.length === 0) { alert("Please add at least one item."); goTo(2); return; }
    if (!$("clientName").value.trim()) { alert("Please enter customer name."); return; }

    buildQuotationView();
    goTo(4);

    $("saveStatus").className = "status success";
    $("saveStatus").textContent = "Client Estimated Quotation generated successfully.";
}

function convertToOfficialInvoice() {
    $("documentHeaderTitle").textContent = "OFFICIAL TAX INVOICE";
    $("saveStatus").className = "status success";
    $("saveStatus").textContent = "Converted to Official Tax Invoice successfully.";
}

document.addEventListener("DOMContentLoaded", () => {
    const searchEl = $("search");
    const categoryEl = $("category");
    if (searchEl) searchEl.addEventListener("input", renderProducts);
    if (categoryEl) categoryEl.addEventListener("change", renderProducts);

    const docDateEl = $("docDate");
    if (docDateEl) {
        const today = new Date().toISOString().split("T")[0];
        docDateEl.value = today;
    }

    buildCategories();
    renderProducts();
    renderCartUI();
});
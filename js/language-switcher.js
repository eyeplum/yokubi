// Adds a language picker to the menu bar.
//
// The English book is built to the site root and the Chinese book to `zh/`.
// Both share the same file layout, so switching language keeps the reader
// on the same page.
(function () {
    var LANGUAGES = [
        { code: "en", label: "English", dir: "" },
        { code: "zh", label: "简体中文", dir: "zh/" },
    ];

    var current = document.documentElement.lang.toLowerCase().indexOf("zh") === 0 ? "zh" : "en";
    var currentDir = LANGUAGES.filter(function (l) { return l.code === current; })[0].dir;

    // `path_to_root` is defined by mdBook's page template.
    var bookRoot = new URL(typeof path_to_root !== "undefined" ? path_to_root : "", window.location.href);
    var siteRoot = new URL(currentDir ? "../" : "./", bookRoot);
    // Drop the query and fragment: search terms and heading anchors don't
    // carry over between languages.
    var here = window.location.href.split(/[?#]/)[0];
    var pagePath = here.indexOf(bookRoot.href) === 0 ? here.slice(bookRoot.href.length) : "";

    function urlFor(lang) {
        return new URL(lang.dir + pagePath, siteRoot).href;
    }

    var buttons = document.querySelector(".menu-bar .right-buttons");
    if (!buttons) {
        return;
    }

    var wrapper = document.createElement("div");
    wrapper.className = "language-switcher";

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "icon-button";
    toggle.id = "language-toggle";
    toggle.title = "Language / 语言";
    toggle.setAttribute("aria-label", "Language / 语言");
    toggle.setAttribute("aria-haspopup", "true");
    toggle.setAttribute("aria-expanded", "false");
    toggle.innerHTML =
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="none" ' +
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M4 5h9M8.5 3v2M11 5c-.8 4-3.6 7.3-7 9M6 8.5c1.2 2.2 3.2 4.1 5.5 5.2"/>' +
        '<path d="M13 21l4-9 4 9M14.5 18h5"/></svg>';

    var popup = document.createElement("ul");
    popup.className = "language-popup";
    popup.setAttribute("role", "menu");
    popup.hidden = true;

    LANGUAGES.forEach(function (lang) {
        var item = document.createElement("li");
        item.setAttribute("role", "none");
        var link = document.createElement("a");
        link.setAttribute("role", "menuitem");
        link.href = urlFor(lang);
        link.lang = lang.code;
        link.textContent = lang.label;
        if (lang.code === current) {
            link.className = "active";
            link.setAttribute("aria-current", "true");
        }
        item.appendChild(link);
        popup.appendChild(item);
    });

    function setOpen(open) {
        popup.hidden = !open;
        toggle.setAttribute("aria-expanded", String(open));
    }

    toggle.addEventListener("click", function (e) {
        e.stopPropagation();
        setOpen(popup.hidden);
    });
    document.addEventListener("click", function (e) {
        if (!wrapper.contains(e.target)) {
            setOpen(false);
        }
    });
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
            setOpen(false);
        }
    });

    wrapper.appendChild(toggle);
    wrapper.appendChild(popup);
    buttons.insertBefore(wrapper, buttons.firstChild);
})();

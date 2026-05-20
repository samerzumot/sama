(function () {
    var mount = document.getElementById('sidebar-mount');
    if (!mount) return;

    fetch('_partials/sidebar.html')
        .then(function (r) { return r.text(); })
        .then(function (html) {
            mount.innerHTML = html;

            var page = location.pathname.split('/').pop().replace('.html', '') || 'index';
            mount.querySelectorAll('.sidebar-link').forEach(function (link) {
                if (link.getAttribute('href').replace('.html', '') === page) {
                    link.classList.add('active');
                }
            });

            var toggle  = document.getElementById('sidebar-toggle');
            var sidebar = document.getElementById('sidebar');
            var overlay = document.getElementById('sidebar-overlay');
            var close   = document.getElementById('sidebar-close');

            function openSidebar()  { sidebar.classList.add('active'); overlay.classList.add('active'); }
            function closeSidebar() { sidebar.classList.remove('active'); overlay.classList.remove('active'); }

            toggle.addEventListener('click', openSidebar);
            close.addEventListener('click', closeSidebar);
            overlay.addEventListener('click', closeSidebar);
        });
})();

(function() {
            const currentTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', currentTheme);
            const toggleButton = document.getElementById('theme-toggle');

            function updateButtonText(theme) {
                toggleButton.textContent = theme === 'dark' ? '☀️' : '🌙';
            }
            updateButtonText(currentTheme);

            toggleButton.addEventListener('click', function() {
                let theme = document.documentElement.getAttribute('data-bs-theme');
                let newTheme = theme === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-bs-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                updateButtonText(newTheme);
            });
        })();
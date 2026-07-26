(function() {
    function togglePeriodFields() {
        const periodSelect = document.getElementById('id_period');
        if (!periodSelect) return;

        const period = periodSelect.value;

        const weekdaysMultipleField = document.getElementById('weekdaysMultipleField');
        const weekdaySingleField = document.getElementById('weekdaySingleField');
        const dayOfMonthField = document.getElementById('dayOfMonthField');

        // Скрываем специфичные поля
        if (weekdaysMultipleField) weekdaysMultipleField.style.display = 'none';
        if (weekdaySingleField) weekdaySingleField.style.display = 'none';
        if (dayOfMonthField) dayOfMonthField.style.display = 'none';

        // Показываем нужные поля в зависимости от типа
        if (period === 'daily') {
            // Ежедневно: дни недели (множественный выбор)
            if (weekdaysMultipleField) weekdaysMultipleField.style.display = 'block';
        } else if (period === 'weekly') {
            // Еженедельно: один день недели
            if (weekdaySingleField) weekdaySingleField.style.display = 'block';
        } else if (period === 'monthly') {
            // Ежемесячно: день месяца
            if (dayOfMonthField) dayOfMonthField.style.display = 'block';
        }
        // Разовая: только время (уже видно)
    }

    function init() {
        const periodSelect = document.getElementById('id_period');
        if (periodSelect) {
            periodSelect.addEventListener('change', togglePeriodFields);
            togglePeriodFields();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
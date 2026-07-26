document.addEventListener('DOMContentLoaded', function () {
  const confirmModal = document.getElementById('confirmModal');

  if (!confirmModal) return;

  // Элементы окна, которые будем менять
  const modalTitle = confirmModal.querySelector('#modalTitle');
  const modalBody = confirmModal.querySelector('#modalBody');
  const confirmBtn = confirmModal.querySelector('#confirmActionBtn');

  // При показе окна
  confirmModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget; // кнопка, открывшая окно

    // Читаем data-атрибуты с дефолтными значениями
    const actionUrl = button.getAttribute('data-action-url');
    const itemName = button.getAttribute('data-item-name') || 'элемент';
    const title = button.getAttribute('data-title') || 'Подтверждение действия';
    let bodyTemplate = button.getAttribute('data-body-template') || 'Вы уверены, что хотите выполнить это действие?';
    const confirmText = button.getAttribute('data-confirm-text') || 'Подтвердить';
    const confirmClass = button.getAttribute('data-confirm-class') || 'btn-primary';

    // Подставляем имя в тело (если есть шаблон с {name})
    bodyTemplate = bodyTemplate.replace(/\{name\}/g, itemName);

    // Заполняем элементы
    modalTitle.textContent = title;
    modalBody.innerHTML = bodyTemplate;
    confirmBtn.textContent = confirmText;
    confirmBtn.className = `btn ${confirmClass}`; // меняем класс
    confirmBtn.setAttribute('data-url', actionUrl);
  });

  // Обработчик клика на кнопку подтверждения (один для всех)
  confirmBtn.addEventListener('click', function () {
    const url = this.getAttribute('data-url');
    if (url) {
      window.location.href = url;
      // Если хотите AJAX, раскомментируйте и передавайте CSRF
    }
  });
});

function openDeleteModal(deleteUrl, itemName, itemType) {
    const modal = document.getElementById('confirmModal');
    if (!modal) {
        console.error('Modal not found!');
        return;
    }

    const modalBody = modal.querySelector('.modal-body');
    const confirmBtn = modal.querySelector('#confirmDeleteBtn');

    modalBody.innerHTML = `
        <p>Вы уверены, что хотите удалить ${itemType}:</p>
        <p class="text-purple-light fs-5"><strong>${itemName}</strong></p>
        <p class="text-muted small">Это действие нельзя отменить.</p>
    `;

    confirmBtn.onclick = function() {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = deleteUrl;

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;

        form.appendChild(csrfInput);
        document.body.appendChild(form);
        form.submit();
    };

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}


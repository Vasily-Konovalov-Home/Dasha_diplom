/**
 * Фоновый сервис-воркер браузерного расширения.
 * Отслеживает навигацию пользователя и инициирует проверку URL
 * через локальный API-сервер.
 */

// Хранилище результатов последней проверки для каждой вкладки браузера.
const tabResults = {};

/**
 * Выполняет проверку URL-адреса через локальный API-сервер.
 * При обнаружении совпадения отправляет команду показа предупреждения
 * в content-скрипт активной вкладки. В противном случае отправляет
 * команду скрытия предупреждения.
 *
 * @param {string} url - URL-адрес для проверки.
 * @param {number} tabId - идентификатор вкладки браузера.
 */
async function checkUrl(url, tabId) {
    try {
        const response = await fetch(
            `http://localhost:8000/check-url?url=${encodeURIComponent(url)}`
        );
        const data = await response.json();

        // Сохранение результата для данной вкладки
        tabResults[tabId] = {
            url: url,
            found: data.found,
            data: data
        };

        if (data.found) {
            // Сайт найден в предупредительном списке ЦБ РФ — показываем предупреждение
            chrome.tabs.sendMessage(tabId, {
                action: 'showWarning',
                data: data
            }).catch(() => {
                // Вкладка может быть ещё не готова принять сообщение
            });
        } else {
            // Сайт не найден — скрываем предупреждение, если оно отображалось
            chrome.tabs.sendMessage(tabId, {
                action: 'hideWarning'
            }).catch(() => {});
        }
    } catch (err) {
        console.log('Ошибка при проверке URL:', err.message);
    }
}

/**
 * Обработчик события полной загрузки страницы.
 * Срабатывает при переходе на новый URL с полной перезагрузкой документа.
 */
chrome.webNavigation.onCompleted.addListener(async (details) => {
    // Игнорируем вложенные фреймы (iframe)
    if (details.frameId !== 0) return;
    checkUrl(details.url, details.tabId);
});

/**
 * Обработчик события изменения состояния истории (History API).
 * Срабатывает при SPA-переходах (одностраничные приложения),
 * когда URL изменяется без полной перезагрузки страницы.
 */
chrome.webNavigation.onHistoryStateUpdated.addListener(async (details) => {
    if (details.frameId !== 0) return;
    console.log('SPA-переход обнаружен:', details.url);
    checkUrl(details.url, details.tabId);
});

/**
 * Обработчик закрытия вкладки браузера.
 * Удаляет сохранённые результаты проверки для освобождения памяти.
 */
chrome.tabs.onRemoved.addListener((tabId) => {
    delete tabResults[tabId];
});
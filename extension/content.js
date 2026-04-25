/**
 * Контент-скрипт браузерного расширения.
 * Отвечает за отображение предупреждающего баннера и модального окна
 * с подробной информацией о мошеннических организациях
 * из предупредительного списка ЦБ РФ.
 */

(function() {
    /**
     * Отображает предупреждающий баннер в верхней части страницы.
     *
     * @param {Object} data - данные, полученные от API-сервера.
     * @param {boolean} data.found - признак обнаружения организации в списке ЦБ РФ.
     * @param {number} data.count - количество найденных организаций.
     * @param {Array} data.companies - массив объектов организаций.
     */
    function showWarning(data) {
        // Удаляем ранее созданный баннер, если он существует на странице
        const oldBanner = document.getElementById('cbr-warning-banner');
        if (oldBanner) oldBanner.remove();
        // Удаляем ранее созданное модальное окно, если оно открыто
        const oldModal = document.getElementById('cbr-warning-modal');
        if (oldModal) oldModal.remove();

        const banner = document.createElement('div');
        banner.id = 'cbr-warning-banner';
        banner.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background: #d32f2f;
            color: white;
            padding: 12px 20px;
            font-family: Arial, sans-serif;
            font-size: 15px;
            z-index: 2147483646;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
        `;

        // Формирование текста предупреждения
        let text = 'ВНИМАНИЕ! ';
        if (data.count === 1) {
            const company = data.companies[0];
            text += `Данный интернет-ресурс связан с организацией из предупредительного списка Банка России: "${company.name}"`;
        } else {
            text += `Данный интернет-ресурс связан с ${data.count} организациями из предупредительного списка Банка России`;
        }

        // Кнопка для открытия подробной информации
        const detailsBtn = document.createElement('button');
        detailsBtn.textContent = 'Подробнее';
        detailsBtn.style.cssText = `
            background: white;
            color: #d32f2f;
            border: none;
            padding: 6px 14px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            font-size: 13px;
        `;

        detailsBtn.onclick = () => showDetailsModal(data);

        banner.appendChild(document.createTextNode(text));
        banner.appendChild(detailsBtn);
        document.body.prepend(banner);
    }

    /**
     * Отображает модальное окно с подробными сведениями об организациях,
     * найденных в предупредительном списке ЦБ РФ.
     * Каждый сайт организации представлен в виде кликабельной ссылки.
     * Предусмотрена прямая ссылка на карточку организации на официальном сайте ЦБ РФ.
     *
     * @param {Object} data - данные, полученные от API-сервера.
     */
    function showDetailsModal(data) {
        const oldModal = document.getElementById('cbr-warning-modal');
        if (oldModal) oldModal.remove();

        // Затемняющий фон (оверлей)
        const overlay = document.createElement('div');
        overlay.id = 'cbr-warning-modal';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            z-index: 2147483647;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Arial, sans-serif;
        `;

        // Контейнер модального окна
        const modal = document.createElement('div');
        modal.style.cssText = `
            background: white;
            color: #333;
            padding: 25px 30px;
            border-radius: 8px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 8px 30px rgba(0,0,0,0.5);
        `;

        // Заголовок окна
        const title = document.createElement('h3');
        title.textContent = 'Организации из предупредительного списка Банка России';
        title.style.cssText = `
            margin: 0 0 15px 0;
            color: #d32f2f;
            font-size: 18px;
        `;
        modal.appendChild(title);

        // Информация о каждой найденной организации
        data.companies.forEach((company, index) => {
            const companyBlock = document.createElement('div');
            companyBlock.style.cssText = `
                margin-bottom: 15px;
                padding: 15px;
                background: #fef4f4;
                border-left: 4px solid #d32f2f;
                border-radius: 4px;
            `;

            let infoHtml = `<strong style="font-size: 16px;">${index + 1}. ${company.name}</strong><br>`;
            infoHtml += `<span style="color: #666;">Дата внесения в список: ${company.date_added || 'не указана'}</span><br>`;

            // Отображение сайтов организации в виде кликабельных ссылок
            if (company.sites) {
                infoHtml += '<span style="color: #666;">Связанные интернет-ресурсы:</span><br>';
                const sites = company.sites.split(/[,;]/);
                sites.forEach(site => {
                    site = site.trim();
                    if (site) {
                        let url = site;
                        // Добавление протокола, если он отсутствует
                        if (!url.startsWith('http://') && !url.startsWith('https://')) {
                            url = 'https://' + url;
                        }
                        infoHtml += `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color: #d32f2f; text-decoration: underline; word-break: break-all;">${site}</a><br>`;
                    }
                });
            }

            if (company.comment) {
                infoHtml += `<span style="color: #666;">Комментарий Банка России: ${company.comment}</span><br>`;
            }

            // Прямая ссылка на карточку организации на официальном сайте ЦБ РФ
            if (company.id) {
                infoHtml += `<br><a href="https://cbr.ru/inside/warning-list/detail/?id=${company.id}" target="_blank" rel="noopener noreferrer" style="color: #1565C0; text-decoration: underline; font-weight: bold;">Открыть карточку организации на сайте Банка России</a>`;
            }

            companyBlock.innerHTML = infoHtml;
            modal.appendChild(companyBlock);
        });

        // Ссылка на общий список ЦБ РФ
        const source = document.createElement('p');
        source.style.cssText = `
            margin: 15px 0 0 0;
            font-size: 13px;
            color: #666;
        `;
        source.innerHTML = 'Источник: <a href="https://cbr.ru/inside/warning-list/" target="_blank" rel="noopener noreferrer" style="color: #d32f2f;">cbr.ru/inside/warning-list/</a>';
        modal.appendChild(source);

        // Кнопка закрытия модального окна
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'Закрыть';
        closeBtn.style.cssText = `
            background: #d32f2f;
            color: white;
            border: none;
            padding: 10px 25px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            margin-top: 15px;
        `;
        closeBtn.onclick = () => overlay.remove();
        modal.appendChild(closeBtn);

        // Закрытие модального окна при клике на затемнённый фон
        overlay.onclick = (event) => {
            if (event.target === overlay) overlay.remove();
        };

        overlay.appendChild(modal);
        document.body.appendChild(overlay);
    }

    /**
     * Скрывает предупреждающий баннер и модальное окно (если они отображаются).
     * Вызывается при переходе на страницу, не обнаруженную в списке ЦБ РФ.
     */
    function hideWarning() {
        const banner = document.getElementById('cbr-warning-banner');
        if (banner) banner.remove();
        const modal = document.getElementById('cbr-warning-modal');
        if (modal) modal.remove();
    }

    /**
     * Обработчик сообщений от фонового сервис-воркера.
     * Принимает команды показа или скрытия предупреждения.
     */
    chrome.runtime.onMessage.addListener((message) => {
        if (message.action === 'showWarning' && message.data && message.data.found) {
            showWarning(message.data);
        } else if (message.action === 'hideWarning') {
            hideWarning();
        }
    });
})();
/* -------------------------------- */
/* flash-messagesの処理 */
/* -------------------------------- */
document.addEventListener('DOMContentLoaded', function() {
    // エラーメッセージ
    clearerror();

    // 成功メッセージ
    clearSuccess();
});

/* メッセージの消去　*/
function clearElement(element) {
    element.classList.add('fade-out');
    setTimeout(() => {
        element.remove();
    }, 400);
}

/* -------------------------------- */
/* エラーメッセージの消去 */
/* -------------------------------- */
function clearerror() {
    const flashMessages = document.querySelector('.flash-error');
    if (!flashMessages) return;

    flashMessages.addEventListener('click', function() {
        clearElement(flashMessages);
    });

    // 5秒後に自動で消去
    setTimeout(() => {
        clearElement(flashMessages);
    }, 5000);
}

/* -------------------------------- */
/* 成功メッセージの消去 */
/* -------------------------------- */
function clearSuccess() {
    const flashMessages = document.querySelector('.flash-success');
    if (!flashMessages) return;

    flashMessages.addEventListener('click', function() {
        clearElement(flashMessages);
    });

    // 5秒後に自動で消去
    setTimeout(() => {
        clearElement(flashMessages);
    }, 5000);
}
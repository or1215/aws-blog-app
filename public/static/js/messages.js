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
    const flashMessages = document.querySelectorAll('.flash-error');
    if (!flashMessages) return;

    flashMessages.forEach(message => {
        message.addEventListener('click', function() {
            clearElement(message);
        });
    });

    // 5秒後に自動で消去
    setTimeout(() => {
        flashMessages.forEach(message => {
            clearElement(message);
        });
    }, 5000);
}

/* -------------------------------- */
/* 成功メッセージの消去 */
/* -------------------------------- */
function clearSuccess() {
    const flashMessages = document.querySelectorAll('.flash-success');
    if (!flashMessages) return;

    flashMessages.forEach(message => {
        message.addEventListener('click', function() {
            clearElement(message);
        });
    });

    // 5秒後に自動で消去
    setTimeout(() => {
        flashMessages.forEach(message => {
            clearElement(message);
        });
    }, 5000);
}
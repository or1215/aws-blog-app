// file.js
document.addEventListener('DOMContentLoaded', () => {
    const avatarTrigger = document.getElementById('avatarTrigger');
    const avatarInput = document.getElementById('avatarInput');

    // 要素が存在する場合のみ処理を実行（エラー防止）
    if (avatarTrigger && avatarInput) {
        // アバター部分をクリックした時にファイル選択を開く
        avatarTrigger.addEventListener('click', () => {
            avatarInput.click();
        });

        // ファイルが選択されたらプレビューを表示する（任意ですが推奨）
        avatarInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    // 現在のアバター表示（imgかspan）をプレビュー画像に差し替える
                    const previewUrl = event.target.result;
                    
                    // .avatar-wrapperの中身を書き換え
                    // ※マスク部分は残す必要があります
                    const imgElement = avatarTrigger.querySelector('.profile-image');
                    const emojiElement = avatarTrigger.querySelector('.default-emoji');

                    if (imgElement) {
                        imgElement.src = previewUrl;
                    } else if (emojiElement) {
                        // 絵文字だった場合はimgタグに作り替える
                        const newImg = document.createElement('img');
                        newImg.src = previewUrl;
                        newImg.className = 'profile-image';
                        emojiElement.replaceWith(newImg);
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
});
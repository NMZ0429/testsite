const upload = (simplemde, uploadFile, textarea) => {
    const formData = new FormData();
    formData.append('file', uploadFile);
    fetch(textarea.dataset.url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrftoken,
        },
    }).then(response => {
        return response.json();
    }).then(response => {
        const extension = response.url.split('.').pop().toLowerCase();
        let md = '';

        // 画像なら![]()に、そうでなければ[]()に
        if (['png', 'jpg', 'gif', 'jpeg'].includes(extension)) {
            md = `![](${response.url})`;
        } else {
            md = `[${response.url}](${response.url})`;
        }
        const pos = simplemde.codemirror.getCursor();
        simplemde.codemirror.setSelection(pos, pos);
        simplemde.codemirror.replaceSelection(md);
    }).catch(error => {
        console.log(error);
    });
};
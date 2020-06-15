function confirmDelete(url, id) {
    if ($(`#confirm_${id}`).length > 0) {
        return;
    }

    let link = $(`#delete_${id}`);
    let confirm = link.append(
        `<span class="deleteconfirm" id="confirm_${id}">Are you sure?
           <a id="do_delete_${id}">yes</a>
           <a id="cancel_delete_${id}">no</a>
         </span>`);
    $(document).on('click', `a#do_delete_${id}`, function() {
        var req = new XMLHttpRequest();
        req.addEventListener("load", function() {
            $(`#link_${id}`).remove();
        });
        req.open("DELETE", url);
        req.send();
    });
    $(document).on('click', `a#cancel_delete_${id}`, function() {
        $(`#confirm_${id}`).remove();
    });
}

function removeConfirm(id) {
    $(`#confirm_${id}`).remove();
}

$(document).ready(() => {
    let input = document.querySelector('.tagtest');
    if (input) {
        let tags = new Tagify(input);

        let form = $("form[name=\"edit_link\"]")
        form.submit(event => {
            event.preventDefault();
            let url = form.attr("action");
            let body = {
                "url": $('input[name="url"]').val(),
                "name": $('input[name="name"]').val(),
                "description": $('input[name="description"]').val(),
                "private": $('input[name="private"]').is(":checked"),
                "tags": tags.value.map(o => o.value),
            };
            fetch(url, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body),
            }).then(response => response.json())
                .then(body => window.location.href = body['redirect'] || url)
                .catch(err => window.location.href = url);
        });
    }
});

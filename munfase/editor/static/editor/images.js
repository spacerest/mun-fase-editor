function hideUri(element_id, new_background_url) {
    var blurry_img = document.getElementById(element_id);
    blurry_img.style.backgroundImage = 'url(' + new_background_url + ')';
    blurry_img.classList.remove("blurme");
}

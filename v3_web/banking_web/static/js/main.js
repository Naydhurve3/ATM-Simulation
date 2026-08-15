document.addEventListener('DOMContentLoaded', function() {
    var flashes = document.querySelectorAll('.flash');
    if (flashes.length > 0) {
        setTimeout(function() {
            flashes.forEach(function(f) {
                f.style.transition = 'opacity 0.3s';
                f.style.opacity = '0';
                setTimeout(function() { f.remove(); }, 300);
            });
        }, 4000);
    }
});

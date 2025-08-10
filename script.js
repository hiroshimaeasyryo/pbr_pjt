// script.js
window.onload = function() {
    var navbar = document.querySelector('.navbar');
    var footer = document.querySelector('footer');
    var plotDiv = document.querySelector('.plotly-graph-div');

    if (!plotDiv) return;

    var navbarHeight = navbar ? navbar.offsetHeight : 0;
    var footerHeight = footer ? footer.offsetHeight : 0;
    var windowHeight = window.innerHeight;
    var graphHeight = Math.max(200, windowHeight - navbarHeight - footerHeight);
    plotDiv.style.height = graphHeight + 'px';
};

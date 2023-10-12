// script.js
window.onload = function() {
    var navbarHeight = document.querySelector('.navbar').offsetHeight;
    var footerHeight = document.querySelector('footer').offsetHeight;
    var windowHeight = window.innerHeight;
    var graphHeight = windowHeight - navbarHeight - footerHeight;
    document.querySelector('#graph').style.height = graphHeight + 'px';
};

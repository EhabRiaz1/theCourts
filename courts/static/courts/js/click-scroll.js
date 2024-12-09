//jquery-click-scroll
//by syamsul'isul' Arifin

jQuery(document).ready(function($) {
    $('.click-scroll').click(function(e) {
        e.preventDefault();
        var target = $(this).attr('href');
        var headerHeight = $('.navbar').outerHeight();
        
        $('html, body').animate({
            scrollTop: $(target).offset().top - headerHeight
        }, 500);
    });
}); 
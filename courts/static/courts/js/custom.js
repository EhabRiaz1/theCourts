jQuery(document).ready(function($) {
    "use strict";

    // PRELOADER
    $(window).on('load', function () {
        $('.preloader').fadeOut('slow');
    });

    // NAVBAR
    if($.fn.sticky) {
        $('.navbar').sticky({
            topSpacing: 0
        });
    }

    // CUSTOM LINK
    $('.custom-link').click(function(e){
        e.preventDefault();
        var el = $(this).attr('href');
        var elWrapped = $(el);
        var header_height = $('.navbar').height();

        scrollToDiv(elWrapped,header_height);
    });

    function scrollToDiv(element,navheight){
        if(element.length) {
            var offset = element.offset();
            var offsetTop = offset.top;
            var totalScroll = offsetTop-navheight;

            $('body,html').animate({
                scrollTop: totalScroll
            }, 300);
        }
    }

    // MENU
    $('.navbar-collapse a').on('click',function(){
        $(".navbar-collapse").collapse('hide');
    });

    // CUSTOM LINK
    $('.smoothscroll').click(function(){
        var el = $(this).attr('href');
        var elWrapped = $(el);
        var header_height = $('.navbar').height();

        scrollToDiv(elWrapped,header_height);
        return false;

        function scrollToDiv(element,navheight){
            var offset = element.offset();
            var offsetTop = offset.top;
            var totalScroll = offsetTop-navheight;

            $('body,html').animate({
                scrollTop: totalScroll
            }, 300);
        }
    });

    // MAGNIFIC POPUP
    $('.popup-image').magnificPopup({
        type: 'image',
        gallery: {
            enabled: true
        },
        zoom: {
            enabled: true,
            duration: 300,
            easing: 'ease-in-out'
        }
    });
}); 
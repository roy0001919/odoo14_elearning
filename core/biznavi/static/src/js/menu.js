$(document).ready(function () {

    $(".toggle_leftmenu").click(function () {
        $("#leftbar").toggleClass('toggled');
    });

    // $(".oe_application_menu_placeholder li ul li a").each(function (index) {
    //     $(this).on("click", function () {
    //         if ($(window).width() <= 768) {
    //             $("button.navbar-toggle").click();
    //         }
    //     });
    // });

    $("#leftbar").find("a").click(function (e) {
        if ($(window).width() <= 768) {
            if (!$(this).next().is( "ul")) {
                $("#leftbar").toggleClass('toggled');
            }
        }
    });

});

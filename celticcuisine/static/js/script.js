    $(document).ready(function(){
        // Dropdown function in top nav
        $(".dropdown-trigger").dropdown({ hover: true });
        // Sidenav initialization
        $(".sidenav").sidenav({ edge: "right" });
        // select initialization
        $("select").formSelect();
        //Tooltip function used in forms
        $(".tooltipped").tooltip();
        //Parallax function used on hero image
        $('.parallax').parallax();
        //Modal function used on delete buttons
        $('.modal').modal();
      });
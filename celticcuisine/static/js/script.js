    $(document).ready(function(){
        // Dropdown function in top nav
        $(".dropdown-trigger").dropdown({ hover: true });
        // Sidenav initialization
        $(".sidenav").sidenav({ edge: "right" });
        // select initialization
        $("select").formSelect();
      });
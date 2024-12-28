const passkey_client = new Passwordless.Client({ apiKey: "mediaviewer:public:8cd7916568ca470cb0738f8ce8d20f18" })

var tableElement;
var csrf_token;
var didScroll;
var lastScrollTop = 0;
var delta = 10;
var viewedCheckboxColumn = 3;

function bindAlertMessage($) {
    $(".alert").bind('closed.bs.alert', function() {
        $.ajax({
            url: '/mediaviewer/ajaxclosemessage/',
        type: 'POST',
        dataType: 'json',
        data: {
            messageid: this.id,
        csrfmiddlewaretoken: csrf_token
        },
        success: function(json){},
        error: function(xhr, errmsg, err){}
        });
    });
}

function preparePage($) {
    bindAlertMessage($);
    $('.carousel').slick({
        infinite: true,
        speed: 600,
        centerMode: true,
        variableWidth: true,
        adaptiveHeight: false,
        autoplay: true,
        autoplaySpeed: 2000,
        pauseOnFocus: true,
        pauseOnHover: false,
        swipeToSlide: true,
        arrows: true,
        waitForAnimate: false
    });
}

function setHomeFormSubmit($) {
    $('form').submit(function(){
        var username = document.getElementById('username');
        var usernameTextbox = document.getElementById('username-textbox');
        username.value = usernameTextbox.value;

        var password = document.getElementById('password');
        var passwordTextbox = document.getElementById('password-textbox');
        password.value = passwordTextbox.value;
    });
}

function sleep (time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

function prepareDataTable($, sortOrder, table_data_page, filter_id) {
    if(filter_id){
        var ajax_path = '/mediaviewer/ajax/' + table_data_page + '/' + String(filter_id) + '/';
    }else{
        var ajax_path = '/mediaviewer/ajax/' + table_data_page + '/';
    }

    dt_config = dataTableConfig($, sortOrder, table_data_page, ajax_path);

    new DataTable('#myTable', dt_config);
}

function dataTableConfig($, sortOrder, table_data_page, ajax_path){
    dt_config = {
        order: sortOrder,
        autoWidth: true,
        columnDefs: [{
            "targets": 'nosort',
            "orderable": false
        }],
        drawCallback: function (settings) {
            sleep(2000).then(() => {
            configureTooltips($);
            });
        },
        stateSave: true,
        createdRow: function (row, data, index) {
            $(row).addClass('base-row');
        }
    };

    dt_config.scroller = {
        loadingIndicator: true
    };
    dt_config.scrollY = 450;
    dt_config.scrollX = true;
    dt_config.scrollCollapse = false;
    dt_config.deferRender = false;
    dt_config.pageLength = 15;

    dt_config.serverSide = true;
    dt_config.ajax = {
        url: ajax_path,
        dataSrc: function(json){
            sleep(2000).then(() => {
            configureTooltips($);
            });
            return json.data;
        },
    }

    var responsive_priorities = [];
    if(table_data_page == 'ajaxtvshows'){
        dt_config.buttons = [
            {
                text: 'Clear All Viewed',
                action: function (e, dt, node, config) {
                    var update_payload = {
                        "media_files": {}
                    };
                    selected_rows = $(".viewed-checkbox:checked").get();
                    file_ids = [];

                    for(var i = 0; i < selected_rows.length; i++){
                        elem = selected_rows[i];
                        file_ids.push(elem.name);
                        elem.removeAttribute('checked');
                        elem.checked = false;
                        update_payload["media_files"][elem.name] = false;
                    }

                    _ajaxCheckBox(update_payload, 'media_file', false);
                }
            },
            {
                text: 'Mark All Viewed',
                action: function (e, dt, node, config) {
                    var update_payload = {
                        "media_files": {}
                    };
                    selected_rows = $(".viewed-checkbox:not(:checked)").get();
                    file_ids = [];

                    for(var i = 0; i < selected_rows.length; i++){
                        elem = selected_rows[i];
                        file_ids.push(elem.name);
                        elem.setAttribute('checked', 'true');
                        elem.checked = true;
                        update_payload["media_files"][elem.name] = true;
                    }
                    _ajaxCheckBox(update_payload, 'media_file', false);
                }
            },
        ];
        dt_config.dom = 'frtip<"row justify-content-center" <"col-auto" B>>';

        responsive_priorities = [
            {responsivePriority: 500, target: 1},
        ];
    } else if(table_data_page == 'ajaxtvshowssummary'){
        responsive_priorities = [
            {responsivePriority: 1, target: 0}
        ];
    } else if(table_data_page == 'ajaxmovierows'){
        responsive_priorities = [
            {responsivePriority: 500, target: 1},
        ];
    } else {
        console.log("This shouldn't be possible!");
        console.log(table_data_page);
    }

    for(var i=0; i < responsive_priorities.length; i++){
        dt_config.columnDefs.push(responsive_priorities[i]);
    }
    return dt_config;
}

function configureTooltips($){
    options = {
        animated: true,
        placement: placePopover,
        html: true,
        delay: 200
    };
    $(function () {
        $('.img-preview').popover(options);
        $('.skip-btn').popover();
    });
}

function placePopover(popover_node, trigger_node){
    if(!popover_node._element.matches(':hover')){
        $(trigger).hide();
        return 'manual';
    }

    $('.popover-body').on('click', function () {
        var popover = popover_node;
        var trigger = trigger_node;
        $(this).hide();
    });
    $('.popover-body').on('mouseleave', function () {
        var popover = popover_node;
        var trigger = trigger_node;
        $(this).hide();
    });
    return 'auto';
}

function prepareTableForRequests($){
    tableElement = $('#myTable');

    tableElement.dataTable({
        stateSave: true,
        autoWidth: true,
        paginate: false,
        ordering: false,
        info: false,
        searching: false,
        responsive: {
            details: true
        },
        columnDefs: [
            {
                className: 'control',
                orderable: false
            },
            {responsivePriority: 1, target: 0},
            {responsivePriority: 500, target: 1},
            {responsivePriority: 1, target: 2}
        ]
    });
}

function ajaxMovieCheckBox(file_ids, is_detail_page){
    update_payload = {
        csrfmiddlewaretoken: csrf_token,
        'movies': {}
    };

    file_ids.forEach((val, idx)=>{
        var box = document.getElementsByName(val)[0];
        var checked = box.checked;
        update_payload["movies"][val] = checked;
        box.setAttribute('disabled', 'disabled');
    });

    _ajaxCheckBox(update_payload, 'movie', is_detail_page);
}

function ajaxTVCheckBox(file_ids, is_detail_page){
    update_payload = {
        csrfmiddlewaretoken: csrf_token,
        "media_files": {}
    };

    file_ids.forEach((val, idx)=>{
        var box = document.getElementsByName(val)[0];
        var checked = box.checked;
        update_payload["media_files"][val] = checked;
        box.setAttribute('disabled', 'disabled');
    });

    _ajaxCheckBox(update_payload, 'media_file', is_detail_page);
}

function _ajaxCheckBox(update_payload, movie_or_media_file, is_detail_page){
    jQuery.ajax({
        url : "/mediaviewer/ajaxviewed/",
        type : "POST",
        contentType: "application/json",
        processData: false,
        data : JSON.stringify(update_payload),
        success : function(json) {
            if(json.errmsg !== ''){
                alert(json.errmsg);
            } else {
                selectors = []

                if(movie_or_media_file === 'movie'){
                    res_data = json.data['movies'];
                }else{
                    res_data = json.data['media_files'];
                }

                for(let file_id in res_data){
                    viewed = Boolean(res_data[file_id][0]);

                    selectors.push('#saved-' + file_id);

                    var box = document.getElementsByName(file_id)[0];
                    box.removeAttribute('disabled');
                }

                var selector_str = '';
                for(var i = 0; i < selectors.length; i++){
                    if(i == selectors.length - 1){
                        selector_str += selectors[i];
                    } else {
                        selector_str += selectors[i] + ',';
                    }
                }

                savedFields = $(selector_str);

                var fadeOutLength;
                if(is_detail_page){
                    fadeOutLength = 2000;
                    savedFields.html("&nbsp;Saved");
                } else {
                    fadeOutLength = 500;
                    savedFields.parent().parent().parent().addClass("row-highlight");
                }

                savedFields.attr('style', '');

                savedFields.fadeOut(fadeOutLength, function() {
                    savedFields.attr('style', 'display: none;');
                    if(is_detail_page){
                        savedFields.html("");
                    } else {
                        savedFields.parent().parent().parent().removeClass("row-highlight");
                    }
                });
            }
        },
        error : function(xhr,errmsg,err) {
            alert(xhr.status + ": " + xhr.responseText);
        }
    });
}

function openDownloadWindow(id, obj_type){
    payload = {csrfmiddlewaretoken: csrf_token}
    if(obj_type === 'movie'){
        payload['movie_id'] = id
    } else {
        payload['mf_id'] = id
    }


    $.ajax({
    url: '/mediaviewer/ajaxdownloadbutton/',
    type: 'POST',
    dataType: 'json',
    data: payload,
    success: function(json){
        if(json.errmsg === ""){
            var win = window.open(json.downloadLink, "_self");
            win.opener = null;
            win.location = json.downloadLink;
            win.focus();
        } else {
            alert(json.errmsg);
        }
    },
    error: function(xhr, errmsg, err){}
    });
}

function prepareAjaxWaiterStatus($, is_staffer){
    $.ajax({
        url: '/mediaviewer/ajaxwaiterstatus/',
    type: 'POST',
    dataType: 'json',
    data: {
        csrfmiddlewaretoken: csrf_token
    },
    success: function(json){
        var statusLabel = document.getElementById('waiter-status');
        if(json.status === true){
            statusLabel.className = 'badge text-bg-success';
            statusLabel.innerText = 'Connected';
        } else {
            statusLabel.className = 'badge text-bg-danger';
            if(is_staffer === 'false'){
                statusLabel.innerText = 'Disconnected';
            } else {
                statusLabel.innerText = json.failureReason;
            }
        }
    },
    error: function(xhr, errmsg, err){}
    });
}


function callAjaxVote(name){
    jQuery.ajax({
        url : "/mediaviewer/ajaxvote/",
        type : "POST",
        dataType: "json",
        data : {
            requestid : name,
        csrfmiddlewaretoken: csrf_token
        },
        success : function(json) {
            var cell = document.getElementById('vote-' + json.requestid);
            cell.outerHTML = 'Thanks for voting!';
            var numberOfVotes = json.numberOfVotes;
            $('#numberOfVotes-' + json.requestid)[0].innerHTML = numberOfVotes;
        },
        error : function(xhr,errmsg,err) {
            alert(xhr.status + ": " + xhr.responseText);
        }
    });
}

function callDoneButton(name){
    $.ajax({
        url : "/mediaviewer/ajaxdone/",
    type : "POST",
    dataType: "json",
    data : {
        requestid : name,
    csrfmiddlewaretoken: csrf_token
    },
    success : function(json) {
        if(json.errmsg === ""){
            var query = 'done-' + json.requestid;
            var cell = document.getElementById(query);
            cell.outerHTML = json.message;
        } else {
            alert(json.errmsg);
        }
    },
    error : function(xhr,errmsg,err) {
        alert(xhr.status + ": " + xhr.responseText);
    }
    });
}

function callGiveUpButton(name){
    $.ajax({
        url : "/mediaviewer/ajaxgiveup/",
    type : "POST",
    dataType: "json",
    data : {
        requestid : name,
    csrfmiddlewaretoken: csrf_token
    },
    success : function(json) {
        if(json.errmsg === ""){
            var query = 'giveup-' + json.requestid;
            var cell = document.getElementById(query);
            cell.outerHTML = json.message;
        } else {
            alert(json.errmsg);
        }
    },
    error : function(xhr,errmsg,err) {
        alert(xhr.status + ": " + xhr.responseText);
    }
    });
}

function reportButtonClick(id, type){
    payload = {csrfmiddlewaretoken: csrf_token}

    if(type === 'movie'){
        payload['movie_id'] = id
    } else if(type === 'media_file'){
        payload['mf_id'] = id
    }

    jQuery.ajax({
    url : "/mediaviewer/ajaxreport/",
    type : "POST",
    dataType: "json",
    data : payload,
    success : function(json) {
        if(json.errmsg !== ''){
            alert(json.errmsg);
        } else {
            var cell = document.getElementsByName('report-' + json.reportid)[0];
            cell.outerHTML = "Report Submitted";
        }
    },
    error : function(xhr,errmsg,err) {
        alert(xhr.status + ": " + xhr.responseText);
    }
    });
}

async function register_passkey(){
    let options = {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type':
                    'application/json;charset=utf-8',
                "csrfmiddlewaretoken": csrf_token,
            },
        }
    try{
        create_token_path = document.location.pathname.replace('user/reset', 'create-token');
        create_token_path = create_token_path.replace('user/create', 'create-token');
        const fetch_resp = await fetch(create_token_path, options);
        fetch_json = await fetch_resp.json();
        if(fetch_json){
            var register_token = fetch_json['token'];
            const { token, error } = await passkey_client.register(register_token);
            if(token){
            window.location.href = '/mediaviewer/create-token-complete/';
            }else{
            window.location.href = '/mediaviewer/create-token-failed/';
            }
            return;
        }
    } catch(err) {
        console.log(err);
        window.location.href = '/mediaviewer/create-token-failed/';
    }

}

async function bypass_passkey(){
    bypass_path = document.location.pathname.replace('user/reset', 'bypass-passkey');
    bypass_path = bypass_path.replace('user/create', 'bypass-passkey');
    window.location.href = bypass_path;
    return;
}

async function verify_passkey(){
    const { token, error } =  await passkey_client.signinWithDiscoverable();

    const search_params = new URLSearchParams(this.document.location.search);
    const next = search_params.get('next');

    if(token){
        new_location = '/mediaviewer/verify-token/?token=' + token;
        if(next){
            new_location = new_location + '&next=' + next;
        }
        window.location.href = new_location;
        return;
    }

    window.location.href = '/mediaviewer/user/reset/';
}

function display_help(){
    var help_text = document.getElementById('help-text');
    var help_link = document.getElementById('help-link');

    if(help_text){
        help_text.style = "display:block;";
        help_link.style = "display:none;";
        window.scrollTo(0, document.body.scrollHeight);
    }
}

function hasScrolled(){
    var topNavbarHeight = $('#top-navbar').outerHeight() + 20;

    var st = $(this).scrollTop();
    var diff = Math.abs(lastScrollTop - st);
    if (diff <= delta)
        return;

    if(st > lastScrollTop && diff > topNavbarHeight){
        $('#top-navbar').removeClass('nav-show').addClass('nav-hide');
        $('#bottom-navbar').removeClass('nav-show').addClass('nav-hide');
        lastScrollTop = st;
    } else if(st < lastScrollTop && diff > topNavbarHeight){
            $('#top-navbar').removeClass('nav-hide').addClass('nav-show');
            $('#bottom-navbar').removeClass('nav-hide').addClass('nav-show');
        lastScrollTop = st;
    }
}

function scrollSetup(){
    $(window).scroll(function (event) {
        didScroll = true;
    });

    setInterval(function(){
        if(didScroll){
            hasScrolled();
            didScroll = false;
            }
            }, 250);
}

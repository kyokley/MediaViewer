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
    tableElement = $('#myTable');

    if(filter_id){
        var ajax_path = '/mediaviewer/ajax/' + table_data_page + '/' + String(filter_id) + '/';
    }else{
        var ajax_path = '/mediaviewer/ajax/' + table_data_page + '/';
    }

    dt_config = dataTableConfig($, sortOrder, table_data_page, ajax_path);

    tableElement.dataTable(dt_config);
}

function dataTableConfig($, sortOrder, table_data_page, ajax_path){
    dt_config = {
        order: sortOrder,
        autoWidth: true,
        responsive: {
            details: {
                type: 'column',
                target: -1
            }
        },
        columnDefs: [{
            "targets": 'nosort',
            "orderable": false
        }],
        drawCallback: function (settings) {
            sleep(2000).then(() => {
            configureTooltips($);
            });
        },
        stateSave: true
    };

    dt_config.scroller = {
        loadingIndicator: true
    };
    dt_config.scrollY = 450;
    dt_config.scrollCollapse = true;
    dt_config.deferRender = true;
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

    if(table_data_page == 'ajaxtvshows'){
        dt_config.buttons = [
            {
                text: 'Clear All Viewed',
                action: function (e, dt, node, config) {
                    selected_rows = $(".viewed-checkbox:checked");
                    file_ids = [];
                    selected_rows.each(
                        (idx, elem)=>{
                            file_ids.push(elem.name);
                            elem.removeAttribute('checked');
                        }
                    )
                    ajaxCheckBox(file_ids);
                }
            },
            {
                text: 'Mark All Viewed',
                action: function (e, dt, node, config) {
                    selected_rows = $(".viewed-checkbox:not(:checked)");
                    file_ids = [];
                    selected_rows.each(
                        (idx, elem)=>{
                            file_ids.push(elem.name);
                            elem.setAttribute('checked', 'true');
                        }
                    )
                    ajaxCheckBox(file_ids);
                }
            },
        ];
        dt_config.dom = 'frtip<"row justify-content-center" <"col-auto" B>>';
    }
    return dt_config;
}

function configureTooltips($){
    options = {
        animated: true,
        placement: placePopover,
        html: true,
        offset: [10, 10],
        delay: 200
    };
    $(function () {
        $('.img-preview').popover(options);
        $('[data-bs-toggle="tooltip"]').tooltip();
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
        autoWidth: false,
        paginate: false,
        ordering: false,
        info: false,
        searching: false,
        responsive: {
            details: {
                type: 'column',
                target: -1
            }
        },
        columnDefs: [{
                    className: 'control',
                    orderable: false,
                    targets: -1
        }]
    });
}

function ajaxCheckBox(file_ids){
    update_payload = {csrfmiddlewaretoken: csrf_token};

    file_ids.forEach((val, idx)=>{
        var box = document.getElementsByName(val)[0];
        var checked = box.checked;
        update_payload[val] = checked;
        box.setAttribute('disabled', 'disabled');
    });

    jQuery.ajax({
        url : "/mediaviewer/ajaxviewed/",
        type : "POST",
        dataType: "json",
        data : update_payload,
        success : function(json) {
            if(json.errmsg !== ''){
                alert(json.errmsg);
            } else {
                for(let file_id in json.data){
                    viewed = Boolean(json.data[file_id][0]);

                    var res = jQuery('#saved-' + file_id);
                    var savedField = res[0];
                    savedField.setAttribute('style', '');
                    savedField.innerText = "Saved";
                    res.fadeOut(2000, function() {
                        savedField.innerText = "";
                        res.show(0);
                    });
                    var box = document.getElementsByName(file_id)[0];
                    box.removeAttribute('disabled');
                };
            }
        },
        error : function(xhr,errmsg,err) {
            alert(xhr.status + ": " + xhr.responseText);
        }
    });
}

function openDownloadWindow(id){
    $.ajax({
    url: '/mediaviewer/ajaxdownloadbutton/',
    type: 'POST',
    dataType: 'json',
    data: {
        fileid: id,
        csrfmiddlewaretoken: csrf_token
    },
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

function reportButtonClick(id){
    jQuery.ajax({
    url : "/mediaviewer/ajaxreport/",
    type : "POST",
    dataType: "json",
    data : {
        reportid : id,
        csrfmiddlewaretoken: csrf_token
    },
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

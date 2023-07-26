const passkey_client = new Passwordless.Client({ apiKey: "mediaviewer:public:8cd7916568ca470cb0738f8ce8d20f18" })

var tableElement;
var csrf_token;
var didScroll;
var lastScrollTop = 0;
var delta = 10;
var navbarHeight = $('.navbar-fixed-top').outerHeight() + 20;
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

function prepareTableSorter($, sortOrder, table_data_page, filter_id) {
    tableElement = $('#myTable');

    if(filter_id){
        var ajax_path = '/mediaviewer/ajax/' + table_data_page + '/' + String(filter_id) + '/';
    }else{
        var ajax_path = '/mediaviewer/ajax/' + table_data_page + '/';
    }
    tableElement.dataTable({
        order: sortOrder,
        autoWidth: false,
        serverSide: true,
        ajax: ajax_path,
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

    tableElement.on('page.dt', function(){
        dt = tableElement.DataTable();
        var info = dt.page.info();
        store_page_info(window.location.href, info.page);
    });

    page_number = get_page_info(window.location.href);
    if(page_number){
        dt = tableElement.DataTable();
        dt.page(page_number).draw(false);
    }
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

function jumpToLastViewedPage($){
    tableElement = $('#myTable');
    dt = tableElement.DataTable();
    if(dt.page.len() === -1){
        return;
    }

    pageLength = dt.page.len();

    maxIndex = dt.rows().data().length;
    data = dt.column(viewedCheckboxColumn).data();
    for(var i = 0; i < dt.rows().data().length; i++){
        value = data[i];
          if(value.indexOf('true') >= 0){
              maxIndex = Math.min(maxIndex, i);
              break;
          }
    }

    // Subtract a very small amount to make sure evenly divisible pages round down
    newPage = Math.max(0, Math.floor(maxIndex / pageLength - .00001));
    dt.page(newPage).draw(false);
}

function prepareViewedCheckBoxes($){
}

function ajaxCheckBox(file_id){
    var box = document.getElementsByName(file_id)[0];
    var checked = box.checked;

    box.previousSibling.innerHTML = checked;

    jQuery.ajax({
        url : "/mediaviewer/ajaxviewed/",
        type : "POST",
        dataType: "json",
        data : {
            fileid : file_id,
            viewed : checked,
            csrfmiddlewaretoken: csrf_token
        },
        success : function(json) {
            if(json.errmsg !== ''){
                alert(json.errmsg);
            } else {
                var res = jQuery('#saved-' + json.fileid);
                var savedField = res[0];
                savedField.innerText = "Saved";
                res.fadeOut(2000, function() {
                    savedField.innerText = "";
                    res.show(0);
                });
            }
        },
        error : function(xhr,errmsg,err) {
            alert(xhr.status + ": " + xhr.responseText);
        }
    });
}

function prepareScraperButton($){
    scrapeBtn = document.getElementById('scraper-btn');
    if(scrapeBtn === null){
        return;
    }
    scrapeBtn.onclick = function() {
        scrapeBtn.innerHTML = "Running";
        $.ajax({
            url : "/mediaviewer/ajaxrunscraper/",
            type : "POST",
            dataType: "json",
            data : {
                csrfmiddlewaretoken: csrf_token
            },
            success : function(json) {
                if(json.errmsg !== ''){
                    alert(json.errmsg);
                } else {
                    scrapeBtn.innerHTML = "Done";
                }
            },
            error : function(xhr,errmsg,err) {
                alert(xhr.status + ": " + xhr.responseText);
            }
        });
        scrapeBtn.className = scrapeBtn.className + " disabled";
    };
}

function prepareDownloadButtons($, waiterStatus){
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
            statusLabel.className = 'label label-success';
            statusLabel.innerText = 'Connected';
        } else {
            statusLabel.className = 'label label-danger';
            if(is_staffer === 'false'){
                statusLabel.innerText = 'Disconnected';
            } else {
                statusLabel.innerText = json.failureReason;
            }
        }

        prepareDownloadButtons($, json.status);
    },
    error: function(xhr, errmsg, err){}
    });
}

function setFileDetailCheckboxes(viewed, hidden){
    if(viewed === 'True'){
        jQuery('#toggle-viewed').prop('checked', 'checked');
    }
    if(hidden === 'True'){
        jQuery('#toggle-hide').prop('checked', 'checked');
    }
};

function prepareVoteButton($){
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

function prepareDoneButton($){
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

function setSettingsRadioButtons(ip_format, local_ip, bangup_ip){
    if(ip_format === local_ip){
        jQuery('#local_ip').prop("checked", "checked");
    } else if (ip_format === bangup_ip) {
        jQuery('#bangup').prop("checked", "checked");
    }
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

function populateUnwatchedBadges(url){
    jQuery.ajax({url: url,
                 type: "GET",
                 dataType: "json",
                 success: function(json){
                     var i;
                     for(i=0; i<json.results.length; i++){
                         var number_of_shows = json.results[i].number_of_unwatched_shows;
                         if(number_of_shows > 0){
                             badgeSpan = tableElement.$("#unwatched-show-badge-" + json.results[i].pk);
                             badgeSpan.html(number_of_shows);
                         }
                     }

                     if(json.next){
                         populateUnwatchedBadges(json.next);
                     }
                 },
                 error: function(json){
                     console.log("An error has occurred attempting to set badges");
                 }
    });
}

function validatePassword(password){
    var digit_regex = /\d/;
    var char_regex = /[^0-9]/;
    var test_string = String(password);
    return test_string.search(digit_regex) !== -1 && test_string.search(char_regex) !== -1 && test_string.length >= 6
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

    if(token){
        window.location.href = '/mediaviewer/verify-token/?token=' + token;
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
    var st = $(this).scrollTop();
    if (Math.abs(lastScrollTop - st) <= delta)
        return;

    if(st > lastScrollTop && st > navbarHeight){
        $('.navbar-fixed-top').removeClass('nav-show').addClass('nav-hide');
        $('.navbar-fixed-bottom').removeClass('nav-show').addClass('nav-hide');
    } else {
        if(st + $(window).height() < $(document).height()){
            $('.navbar-fixed-top').removeClass('nav-hide').addClass('nav-show');
            $('.navbar-fixed-bottom').removeClass('nav-hide').addClass('nav-show');
        }
    }

    lastScrollTop = st;
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

function store_page_info(url, page_number){
    page_info = localStorage.getItem('page_info');
    if(page_info){
        page_info = JSON.parse(page_info)
        page_info[url] = {'page_number': page_number,
                          'date': new Date()};
    } else {
        var page_info = {};
        page_info[url] = {'page_number': page_number,
                          'date': new Date()};
    }
    localStorage.setItem('page_info', JSON.stringify(page_info));
}

function get_page_info(url){
    page_info = localStorage.getItem('page_info');
    if(page_info){
        page_info = JSON.parse(page_info);
        if(page_info[url]){
            data = page_info[url];
            var day = 1000 * 60 * 60 * 24;
            var current_date = new Date();
            date = new Date(data.date);
            var diff = Math.ceil((current_date.getTime()-date.getTime())/(day));

            if(diff > 1){
                return null;
            } else {
                return data.page_number;
            }
        }
    }
    return null;
}

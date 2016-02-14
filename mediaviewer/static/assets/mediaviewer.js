var tableElement;

function bindAlertMessage($, token) {
    $(".alert").bind('closed.bs.alert', function() {
        $.ajax({
            url: '/mediaviewer/ajaxclosemessage/',
        type: 'POST',
        dataType: 'json',
        data: {
            messageid: this.id,
        csrfmiddlewaretoken: token
        },
        success: function(json){},
        error: function(xhr, errmsg, err){}
        });
    });
}

function preparePage($, token) {
    bindAlertMessage($, token);
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

function prepareTableSorter($, sortOrder) {
    tableElement = $('#myTable');

    tableElement.dataTable({
        order: sortOrder,
        stateSave: true,
        autoWidth: false,
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

function prepareViewedCheckBoxes($, token){
}

function ajaxCheckBox(token, file_id){
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
            csrfmiddlewaretoken: token
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

function prepareScraperButton($, token){
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
                csrfmiddlewaretoken: token
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

function prepareDownloadButtons($, token, waiterStatus){
}

function openDownloadWindow(id, token){
    $.ajax({
    url: '/mediaviewer/ajaxdownloadbutton/',
    type: 'POST',
    dataType: 'json',
    data: {
        fileid: id,
        csrfmiddlewaretoken: token
    },
    success: function(json){
        if(json.errmsg === ""){
            var win = window.open(json.downloadLink, "_blank", "height=400, width=812, resizeable=yes");
            win.focus();
        } else {
            alert(json.errmsg);
        }
    },
    error: function(xhr, errmsg, err){}
    });
}

function prepareAjaxWaiterStatus($, token, is_staffer){
    $.ajax({
        url: '/mediaviewer/ajaxwaiterstatus/',
    type: 'POST',
    dataType: 'json',
    data: {
        csrfmiddlewaretoken: token
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

        prepareDownloadButtons($, token, json.status);
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

function prepareVoteButton($, token){
}

function callAjaxVote(name, token){
    jQuery.ajax({
        url : "/mediaviewer/ajaxvote/",
        type : "POST",
        dataType: "json",
        data : {
            requestid : name,
        csrfmiddlewaretoken: token
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

function prepareDoneButton($, token){
}

function callDoneButton(name, token){
    $.ajax({
        url : "/mediaviewer/ajaxdone/",
    type : "POST",
    dataType: "json",
    data : {
        requestid : name,
    csrfmiddlewaretoken: token
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

function setSettingsRadioButtons(ip_format, local_ip, bangup_ip){
    if(ip_format === local_ip){
        jQuery('#local_ip').prop("checked", "checked");
    } else if (ip_format === bangup_ip) {
        jQuery('#bangup').prop("checked", "checked");
    }
}

function reportButtonClick(id, token){
    jQuery.ajax({
    url : "/mediaviewer/ajaxreport/",
    type : "POST",
    dataType: "json",
    data : {
        reportid : id,
        csrfmiddlewaretoken: token
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

/* DEBUGGING */
var debugging = false;

/* Get last session */
function setCookie(name,value,days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}
function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}
function eraseCookie(name) {   
    document.cookie = name +'=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}
var session = getCookie("session");

/* PRE-FILL DATES */
var today = new Date()
var tomorrow = new Date();
var last_week = new Date();
tomorrow.setDate(today.getDate() + 1);
last_week.setDate(today.getDate() - 30);
document.getElementById('min_date').valueAsDate = last_week;
document.getElementById('max_date').valueAsDate = tomorrow;

/* API URL*/
var api_url = "https://litai.eastus.cloudapp.azure.com:1024/";

/* Query API*/
function query_api() {

    // get search string
    var url = api_url + "search/";
    var has_params = false;
    var elements = ["keywords", "min_date", "max_date"];
    for (const element of elements) {
        var value = document.getElementById(element).value;
        if (value.length > 0) {
            url += !has_params? "?": "&";
            url += element + "=" + encodeURI(value)
            has_params = true;
        }
    }

    // add in scores table
    url += !has_params? "?": "&";
    url += "scores_table=" + document.getElementById("table_selection").value;

    // log url
    if (debugging) {console.log("Querying " + url);}

    // query api
    var request = new XMLHttpRequest();
    request.open("GET", url, true);
    request.onload = function(e) {
        if (request.readyState === 4) {
            if (request.status === 200) {
                show_results(request);
            }
        }
    };
    request.send(null);
}

/* Read user token from URL */
const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const user = urlParams.get("user");

/* Delete Comments */
function delete_comment(id) {
    var request = new XMLHttpRequest();
    request.onreadystatechange = async function() {
        if (request.readyState == XMLHttpRequest.DONE) {
            response = JSON.parse(request.responseText);
            if (response["success"]) {
                document.getElementById("comment_" + id).style.display = null;
            } else {
                document.getElementById("comment_" + id).innerHTML += "You can only delete your own comments!";
            }
        }
    }
    const url = api_url + "delete-comment/"
        + "?id=" + id
        + "&session=" + session;
    console.log(url);
    request.open("GET", url, true);
    request.send(null);
}

/* Show results*/
function show_results(request) {

    // parse json response
    var json = JSON.parse(request.responseText)

    // build html results output
    var html = "";
    has_field = false;
    for (field in json) {

        // write title, as a link
        html += "<br />";
        html += "<a class=\"p1\" ";
        html += "href=https://pubmed.ncbi.nlm.nih.gov/" + json[field]["PMID"] + "/ ";
        html += "target=\"_blank\" rel=\"noopener noreferrer\">";
        html += json[field]["Title"];
        html += "</a>"

        // write meta-data
        html += "<p class=\"p3\">";
        html += "PMID: " + json[field]["PMID"] + " &middot; ";
        html += "Score: " + json[field]["Score"].toPrecision(3) + " &middot; ";
        html += "Date: " + json[field]["Date"] + " &middot; ";
        html += "DOI: " + json[field]["DOI"];
        html += "</p>"

        // write abstract
        html +="<p class=\"p2\">";
        html += json[field]["Abstract"];
        html += "</p>";

        // show comments
        for (let g = 0; g < json[field]["Comments"].length; g++) {
            comments = json[field]["Comments"][g];
            html += "<div class='pcomment' id='comment_" + comments["ID"] + "'>"
            html += "<p class=p2>" + comments["Comment"] + "</p>";
            html += "<p class='p3 right'>" + comments["User"];
            if (session) {
                html += "&nbsp;&nbsp;-&nbsp;&nbsp<a onclick=\"delete_comment(" + comments["ID"] + ")\"><u>Delete</u></a></p3>";
            }
            html += "</div>";
        }

        // offer feedback options
        if (session) {
            accept_target = "feedback('accept', " + json[field]["PMID"] + ")";
            reject_target = "feedback('reject', " + json[field]["PMID"] + ")";
            comment_target = "comment(" + json[field]["PMID"] + ")";
            html += "<div>"
            html += "<a class=\"p2\" onclick=\"" + accept_target + "\">";
            html += "<u>Accept Article</u>";
            html += "</a>";
            html += " &middot; ";
            html += "<a class=\"p2\" onclick=\"" + reject_target + "\">";
            html += "<u>Reject Article</u>";
            html += "</a>";
            html += "</br>";
            html += "<p class=\"p2\" id=\"feedback_" + json[field]["PMID"] + "\"></p>";
            html += "<textarea placeholder='Leave a Comment...' id=\"comment_" + json[field]["PMID"] + "\"></textarea>";
            html += "<button class='button button2' onclick=\"" + comment_target + "\">Submit Comment</button>";
            html += "</br>";
            html += "</div>"
        }

        // mark that article(s) have been found
        has_field = true;
    }

    // write error message
    if (!has_field) {
        html += "<p class=\"p2\">No articles match your search query.</p>";
    }

    // show results on webpage
    document.getElementById("results").innerHTML = html;
    document.getElementById("results-box").style = "display: block";
}

/* Offer feedback */
function feedback(action, pmid) {
    var request = new XMLHttpRequest();
    const url = api_url + "feedback/"
        + "?pmid=" + pmid
        + "&session=" + session
        + "&scores_table=" + document.getElementById("table_selection").value
        + "&feedback=" + (action == 'accept'? 1: 0);
    request.open("GET", url, true);
    request.send(null);
    document.getElementById("feedback_" + pmid).textContent += "\n\nThanks! Feedback saved.";
}

function comment(pmid) {
    var request = new XMLHttpRequest();
    const url = api_url + "comment/"
        + "?pmid=" + pmid
        + "&session=" + session
        + "&scores_table=" + document.getElementById("table_selection").value
        + "&comment=" + document.getElementById("comment_" + pmid).value;
    request.open("GET", url, true);
    request.send(null);
    document.getElementById("comment_" + pmid).value = "";
    document.getElementById("comment_" + pmid).placeholder = "Submitted!";
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function login() {
    var request = new XMLHttpRequest();
    request.onreadystatechange = async function() {
        if (request.readyState == XMLHttpRequest.DONE) {
            response = JSON.parse(request.responseText);
            if (response["success"]) {
                session = response["session"];
                document.getElementById("login_status").innerHTML = "Success! Redirecting...";
                await sleep(3000);
                open_menu();
                eraseCookie("session");
                setCookie("session");
            } else {
                document.getElementById("login_status").innerHTML = "Error: Invalid username / password. Try again?";
            }
        }
    }
    const url = api_url + "get-session/"
        + "?user=" + document.getElementById("username").value
        + "&password=" + document.getElementById("password").value;
    request.open("GET", url, true);
    request.send(null);
}

function change_password() {
    var request = new XMLHttpRequest();
    request.onreadystatechange = async function() {
        if (request.readyState == XMLHttpRequest.DONE) {
            response = JSON.parse(request.responseText);
            if (response["success"]) {
                session = response["session"];
                document.getElementById("login_status").innerHTML = "Success! Redirecting...";
                await sleep(3000);
                open_menu();
                eraseCookie("session");
                setCookie("session");
            } else {
                document.getElementById("login_status").innerHTML = "Error: Invalid username / password. Try again?";
            }
        }
    }
    const url = api_url + "change-password/"
        + "?user=" + document.getElementById("username").value
        + "&old_password=" + document.getElementById("password").value
        + "&new_password=" + document.getElementById("new_password").value;
    request.open("GET", url, true);
    request.send(null);
}

// open menu
function open_menu() {

    // toggle icon
    document.getElementById("hamburger").classList.toggle("change");

    // toggle transparency, open login panel
    if (document.getElementById("transparency").style.display) {
        document.getElementById("transparency").style.display = null;
        document.getElementById("login").style.display = null;
    } else {
        document.getElementById("transparency").style.display = "block";
        document.getElementById("login").style.display = "block";
    }
}

/* Query API on Startup */
query_api();

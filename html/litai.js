/* DEBUGGING */
var debugging = false;

/* PRE-FILL DATES */
var today = new Date()
var tomorrow = new Date();
var last_week = new Date();
tomorrow.setDate(today.getDate() + 1);
last_week.setDate(today.getDate() - 30);
document.getElementById('min_date').valueAsDate = last_week;
document.getElementById('max_date').valueAsDate = tomorrow;

/* API URL*/
var api_url = "https://litai.eastus.cloudapp.azure.com/search/";

/* Query API*/
function query_api() {

    // get search string
    var url = api_url;
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
const token = urlParams.get("token");

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

        // offer feedback options
        if (token != null) {
            accept_target = "feedback('accept', " + json[field]["PMID"] + ")";
            reject_target = "feedback('reject', " + json[field]["PMID"] + ")";
            html += "<a class=\"p2\" onclick=\"" + accept_target + "\">";
            html += "<u>Accept Article</u>";
            html += "</a>"
            html += " &middot; ";
            html += "<a class=\"p2\" onclick=\"" + reject_target + "\">";
            html += "<u>Reject Article</u>";
            html += "</a>"
            html += "<p class=\"p2\" id=\"feedback_" + json[field]["PMID"] + "\"></p>";
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
    const url = "https://litai.eastus.cloudapp.azure.com/feedback/" + action
        + "?pmid=" + pmid
        + "&table=" + document.getElementById("table_selection").value
        + "&token=" + token;
    request.open("GET", url, true);
    request.send(null);
    document.getElementById("feedback_" + pmid).textContent += "Thanks! Feedback saved.";
}

/* Query API on Startup */
query_api();

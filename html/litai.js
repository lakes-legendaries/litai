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

/* Show results*/
function show_results(request) {
    var html = ""
    var json = JSON.parse(request.responseText)
    for (field in json) {
        html += "<br />";
        html += "<a class=\"p1\" ";
        html += "href=https://pubmed.ncbi.nlm.nih.gov/" + json[field]["PMID"] + "/ ";
        html += "target=\"_blank\" rel=\"noopener noreferrer\">";
        html += json[field]["Title"];
        html += "</a><p class=\"p2\">";
        html += "PMID: " + json[field]["PMID"] + " &middot; ";
        html += "Score: " + json[field]["Score"].toPrecision(3) + " &middot; ";
        html += "Date: " + json[field]["Date"];
        html += "</p><p class=\"p2\">";
        html += json[field]["Abstract"];
        html += "</p>";
    }
    document.getElementById("results").innerHTML = html;
    document.getElementById("results-box").style = "display: block";
}

/* Query API on Startup */
query_api();

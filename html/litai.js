/* DEBUGGING */
var debugging = false;

/* API URL*/
var api_url = "https://litai.kindplant-8e343140.eastus.azurecontainerapps.io/search/";

/* Query API*/
function query_api() {

    // get table url
    var url = api_url;
    if (document.getElementById("senescence").checked) {
        url += "senescence";
    } else {
        url += "hbot";
    }

    // get search string
    var has_params = false;
    var elements = ["keywords", "min_date"];
    for (const element of elements) {
        var value = document.getElementById(element).value;
        if (value.length > 0) {
            url += !has_params? "?": "&";
            url += element + "=" + encodeURI(value)
            has_params = true;
        }
    }

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
        html += json[field]["Abstract"];
        html += "</p>";
    }
    document.getElementById("results").innerHTML = html;
    document.getElementById("results-box").style = "display: block";
}

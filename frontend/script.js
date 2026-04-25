async function generateSQL() {
    const question = document.getElementById("userInput").value.trim();
    if (!question) return;

    document.getElementById("loader").style.display = "block";
    document.getElementById("results").style.display = "none";
    document.getElementById("errorBox").style.display = "none";

    try {
        const response = await fetch("http://127.0.0.1:8000/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });

        const data = await response.json();
        document.getElementById("loader").style.display = "none";

        if (!response.ok) {
            showError(data.detail || "Server error");
            return;
        }

        document.getElementById("schemaText").innerText = data.pipeline_trace?.schema_text || "-";
        document.getElementById("schemaHeaders").innerText = (data.pipeline_trace?.headers || []).join(" | ") || "-";
        document.getElementById("generatorInput").innerText = data.pipeline_trace?.generated_input || "-";
        document.getElementById("validatorIntent").innerText = data.pipeline_trace?.validator_intent || "-";
        document.getElementById("generatedSQL").innerText = data.generated_sql || "-";
        document.getElementById("validatedSQL").innerText = data.validated_sql || "-";
        document.getElementById("optimizedSQL").innerText = data.optimized_sql || data.final_sql || "-";
        document.getElementById("finalSQL").innerText = data.final_sql || "-";
        document.getElementById("intentBadge").innerText = data.intent || "SELECT";

        const bench = data.optimization?.benchmark || {};
        document.getElementById("beforeMs").innerText = bench.before_ms ? bench.before_ms + " ms" : "-";
        document.getElementById("afterMs").innerText = bench.after_ms ? bench.after_ms + " ms" : "-";
        document.getElementById("speedup").innerText = bench.speedup ? bench.speedup + "x" : "-";

        const recs = data.optimization?.recommended_indexes || [];
        if (recs.length > 0) {
            document.getElementById("indexRecs").innerHTML =
                "<p><b>Recommended indexes:</b></p><ul>" +
                recs.map((item) => `<li><code>${item}</code></li>`).join("") +
                "</ul>";
        } else {
            document.getElementById("indexRecs").innerHTML = "<p>No index recommendations.</p>";
        }

        const rows = data.result || [];
        if (rows.length === 0) {
            document.getElementById("tableOutput").innerHTML = "<p>No results found.</p>";
        } else {
            const keys = Object.keys(rows[0]);
            let html = "<table><tr>" + keys.map((key) => `<th>${key}</th>`).join("") + "</tr>";
            rows.forEach((row) => {
                html += "<tr>" + keys.map((key) => `<td>${row[key] ?? ""}</td>`).join("") + "</tr>";
            });
            html += "</table>";
            document.getElementById("tableOutput").innerHTML = html;
        }

        document.getElementById("results").style.display = "block";
    } catch (error) {
        document.getElementById("loader").style.display = "none";
        showError("Could not connect to server. Make sure the backend is running.");
    }
}

function showError(message) {
    const box = document.getElementById("errorBox");
    box.innerText = "Error: " + message;
    box.style.display = "block";
}

function clearAll() {
    document.getElementById("userInput").value = "";
    document.getElementById("results").style.display = "none";
    document.getElementById("errorBox").style.display = "none";
    document.getElementById("loader").style.display = "none";
}
